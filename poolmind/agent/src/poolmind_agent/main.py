"""
PoolMind Agent - Main Entry Point

This script runs the PoolMind agent in continuous mode, checking for arbitrage opportunities
across exchanges and executing trades when profitable opportunities are found.
"""
import os
import asyncio
import logging
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import httpx

from poolmind_agent.core.agent import PoolMindAgent
from poolmind_agent.utils.config import AgentConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

class ExternalAPIClient:
    """Client for interacting with the external PoolMind API"""
    
    def __init__(self, api_url: str):
        """
        Initialize the API client
        
        Args:
            api_url: Base URL for the API
        """
        self.api_url = api_url
        logger.info(f"Initialized External API client with URL: {api_url}")
    
    async def notify_trade_execution(self, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Notify the external API about a successful trade execution
        
        Args:
            trade_data: Data about the executed trade
            
        Returns:
            API response
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/trades",
                    json=trade_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code in (200, 201):
                    logger.info(f"Successfully notified API about trade: {trade_data.get('id')}")
                    return response.json()
                else:
                    logger.error(f"Error notifying API: {response.status_code} {response.text}")
                    return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
        
        except Exception as e:
            logger.error(f"Error notifying API about trade: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_pool_status(self) -> Dict[str, Any]:
        """
        Get current pool status from the external API
        
        Returns:
            Pool status data
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/pool/status",
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Error getting pool status: {response.status_code} {response.text}")
                    return {}
        
        except Exception as e:
            logger.error(f"Error getting pool status: {str(e)}")
            return {}

class ArbitrageMonitor:
    """
    Monitors exchanges for arbitrage opportunities and executes trades
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the arbitrage monitor
        
        Args:
            config_path: Path to config file (optional)
        """
        # Load configuration
        self.config = AgentConfig(config_path)
        
        # Initialize agent
        self.agent = PoolMindAgent(self.config)
        
        # Initialize API client
        api_url = os.getenv("API_URL", "https://poolmind.futurdevs.com/api")
        self.api_client = ExternalAPIClient(api_url)
        
        # Track execution state
        self.running = False
        self.last_check_time = 0
        self.check_interval = 30  # seconds
        
        logger.info("Arbitrage Monitor initialized")
    
    async def initialize(self) -> None:
        """Initialize the agent and services"""
        await self.agent.initialize()
        logger.info("Arbitrage Monitor services initialized")
    
    async def check_arbitrage_opportunities(self) -> List[Dict[str, Any]]:
        """
        Check for arbitrage opportunities across exchanges
        
        Returns:
            List of arbitrage opportunities
        """
        try:
            # Get market data from all supported exchanges
            market_data = []
            
            for exchange in self.config.supported_exchanges:
                # Get all tickers for this exchange
                tickers = await self.agent.exchange_client.get_all_tickers(exchange)
                
                # Add to market data
                market_data.append({
                    "exchange": exchange,
                    "tickers": tickers
                })
            
            # Update agent with market data
            await self.agent.observe(market_data)
            
            # Get detected opportunities
            opportunities = await self.agent.get_detected_opportunities(limit=10)
            
            if opportunities:
                logger.info(f"Found {len(opportunities)} arbitrage opportunities")
            
            return opportunities
        
        except Exception as e:
            logger.error(f"Error checking arbitrage opportunities: {str(e)}")
            return []
    
    async def execute_arbitrage(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an arbitrage trade for a detected opportunity
        
        Args:
            opportunity: Arbitrage opportunity
            
        Returns:
            Execution result
        """
        try:
            # Generate strategy
            strategy = await self.agent.generate_strategy(opportunity)
            
            if not strategy:
                logger.warning("Failed to generate strategy for opportunity")
                return {"success": False, "error": "Failed to generate strategy"}
            
            # Assess risk
            risk_assessment = await self.agent.assess_risk(strategy)
            
            if not risk_assessment.get("proceed", False):
                logger.warning(f"Strategy rejected by risk assessment: {risk_assessment.get('recommendation')}")
                return {"success": False, "error": f"Risk assessment rejected: {risk_assessment.get('recommendation')}"}
            
            # Optimize execution
            execution_plan = await self.agent.optimize_execution(strategy)
            
            if not execution_plan:
                logger.warning("Failed to optimize execution")
                return {"success": False, "error": "Failed to optimize execution"}
            
            # Execute strategy
            execution_result = await self.agent.execute(strategy)
            
            if execution_result.get("success", False):
                logger.info(f"Successfully executed arbitrage: {execution_result}")
                
                # Notify external API
                trade_data = {
                    "id": execution_result.get("order_id", f"trade-{int(time.time())}"),
                    "timestamp": datetime.now().isoformat(),
                    "pair": strategy.get("pair"),
                    "buy_exchange": strategy.get("buy_exchange"),
                    "sell_exchange": strategy.get("sell_exchange"),
                    "buy_price": execution_result.get("buy_price"),
                    "sell_price": execution_result.get("sell_price"),
                    "amount": strategy.get("amount"),
                    "profit": execution_result.get("actual_profit"),
                    "profit_pct": execution_result.get("actual_profit_pct"),
                    "status": "completed"
                }
                
                # Notify API
                await self.api_client.notify_trade_execution(trade_data)
                
                # Store in RAG for future reference
                await self.agent.rag_service.store_trade_outcome({
                    "strategy": strategy,
                    "execution": execution_result,
                    "outcome": {
                        "profit": execution_result.get("actual_profit"),
                        "profit_pct": execution_result.get("actual_profit_pct"),
                        "success": True
                    }
                })
                
                # Reflect on execution
                await self.agent.reflect(execution_result)
            
            return execution_result
        
        except Exception as e:
            logger.error(f"Error executing arbitrage: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def run_continuous(self) -> None:
        """Run the arbitrage monitor in continuous mode"""
        self.running = True
        
        logger.info("Starting continuous arbitrage monitoring")
        
        try:
            while self.running:
                # Check if it's time to check for opportunities
                current_time = time.time()
                if current_time - self.last_check_time >= self.check_interval:
                    self.last_check_time = current_time
                    
                    # Check for opportunities
                    opportunities = await self.check_arbitrage_opportunities()
                    
                    # Execute profitable opportunities
                    for opportunity in opportunities:
                        # Check if opportunity meets minimum profit threshold
                        if opportunity.get("estimated_profit_pct", 0) >= self.config.min_profit_threshold:
                            logger.info(f"Executing arbitrage for {opportunity.get('pair')} with estimated profit {opportunity.get('estimated_profit_pct')}%")
                            await self.execute_arbitrage(opportunity)
                
                # Sleep to avoid excessive CPU usage
                await asyncio.sleep(1)
        
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, stopping")
            self.running = False
        
        except Exception as e:
            logger.error(f"Error in continuous monitoring: {str(e)}")
            self.running = False
        
        finally:
            # Cleanup
            await self.agent.stop()
            logger.info("Arbitrage monitoring stopped")
    
    def stop(self) -> None:
        """Stop the arbitrage monitor"""
        self.running = False
        logger.info("Stopping arbitrage monitor")

async def main():
    """Main entry point"""
    try:
        # Create and initialize arbitrage monitor
        monitor = ArbitrageMonitor()
        await monitor.initialize()
        
        # Run in continuous mode
        await monitor.run_continuous()
    
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise

if __name__ == "__main__":
    # Run the main async function
    asyncio.run(main())
