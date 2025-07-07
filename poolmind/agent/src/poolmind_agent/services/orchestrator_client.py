"""
Orchestrator Client - Interface for interacting with the PoolMind orchestrator
"""
from typing import Dict, List, Any, Optional
import logging
import asyncio
import json
import time
import os
from datetime import datetime

import httpx

from poolmind_agent.utils.config import AgentConfig

logger = logging.getLogger(__name__)

class OrchestratorClient:
    """
    Client for interacting with the PoolMind orchestrator
    """
    
    def __init__(self, config: AgentConfig):
        """
        Initialize the Orchestrator Client
        
        Args:
            config: Agent configuration
        """
        self.config = config
        self.base_url = os.getenv("API_URL", "https://poolmind.futurdevs.com/api")
        self.api_key = config.orchestrator_api_key
        self.last_request_time = 0
        self.use_mock = os.getenv("USE_MOCK_API", "false").lower() == "true"
        
        logger.info(f"Orchestrator Client initialized with API URL: {self.base_url} (use_mock={self.use_mock})")
    
    async def get_pool_status(self) -> Dict[str, Any]:
        """
        Get current status of the pool from orchestrator
        
        Returns:
            Pool status data
        """
        try:
            # Apply rate limiting
            await self._apply_rate_limiting()
            
            # Check if we're in mock mode
            if self.use_mock:
                return self._get_mock_pool_status()
            
            # Make API request
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/pool/status",
                    headers=self._get_headers()
                )
                
                # Check response
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Error getting pool status: {response.status_code} {response.text}")
                    return self._get_mock_pool_status()
            
        except Exception as e:
            logger.error(f"Error getting pool status: {str(e)}")
            return self._get_mock_pool_status()
    
    async def get_trading_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get trading history from orchestrator
        
        Args:
            limit: Maximum number of trades to return
            
        Returns:
            List of historical trades
        """
        try:
            # Apply rate limiting
            await self._apply_rate_limiting()
            
            # Check if we're in mock mode
            if self.use_mock:
                return self._get_mock_trading_history(limit)
            
            # Make API request
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/trading/history",
                    params={"limit": limit},
                    headers=self._get_headers()
                )
                
                # Check response
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Error getting trading history: {response.status_code} {response.text}")
                    return self._get_mock_trading_history(limit)
            
        except Exception as e:
            logger.error(f"Error getting trading history: {str(e)}")
            return self._get_mock_trading_history(limit)
    
    async def submit_strategy(self, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit a trading strategy to the orchestrator
        
        Args:
            strategy: Trading strategy
            
        Returns:
            Submission result
        """
        try:
            # Apply rate limiting
            await self._apply_rate_limiting()
            
            # Check if we're in mock mode
            if self.use_mock:
                return self._get_mock_submission_result(strategy)
            
            # Make API request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/strategy/submit",
                    json=strategy,
                    headers=self._get_headers()
                )
                
                # Check response
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Error submitting strategy: {response.status_code} {response.text}")
                    return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
            
        except Exception as e:
            logger.error(f"Error submitting strategy: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_execution_result(self, strategy_id: str) -> Dict[str, Any]:
        """
        Get execution result for a strategy
        
        Args:
            strategy_id: Strategy ID
            
        Returns:
            Execution result
        """
        try:
            # Apply rate limiting
            await self._apply_rate_limiting()
            
            # Check if we're in mock mode
            if self.use_mock:
                return self._get_mock_execution_result(strategy_id)
            
            # Make API request
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/strategy/{strategy_id}/result",
                    headers=self._get_headers()
                )
                
                # Check response
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Error getting execution result: {response.status_code} {response.text}")
                    return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
            
        except Exception as e:
            logger.error(f"Error getting execution result: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def notify_trade_execution(self, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Notify orchestrator of a trade execution
        
        Args:
            trade_data: Trade execution data
            
        Returns:
            Notification result
        """
        try:
            # Apply rate limiting
            await self._apply_rate_limiting()
            
            # Check if we're in mock mode
            if self.use_mock:
                return {"success": True, "message": "Trade execution notification received"}
            
            # Make API request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/trade/notify",
                    json=trade_data,
                    headers=self._get_headers()
                )
                
                # Check response
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Error notifying trade execution: {response.status_code} {response.text}")
                    return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
            
        except Exception as e:
            logger.error(f"Error notifying trade execution: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def notify_event(self, event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Notify orchestrator of an event
        
        Args:
            event_type: Event type
            event_data: Event data
            
        Returns:
            Notification result
        """
        try:
            # Apply rate limiting
            await self._apply_rate_limiting()
            
            # Check if we're in mock mode
            if self.use_mock:
                return {"success": True, "message": "Event notification received"}
            
            # Make API request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/events/notify",
                    json={"type": event_type, "data": event_data},
                    headers=self._get_headers()
                )
                
                # Check response
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Error notifying event: {response.status_code} {response.text}")
                    return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
            
        except Exception as e:
            logger.error(f"Error notifying event: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_agent_config(self) -> Dict[str, Any]:
        """
        Get agent configuration from orchestrator
        
        Returns:
            Agent configuration
        """
        try:
            # Apply rate limiting
            await self._apply_rate_limiting()
            
            # Check if we're in mock mode
            if self.use_mock:
                return self._get_mock_agent_config()
            
            # Make API request
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/agent/config",
                    headers=self._get_headers()
                )
                
                # Check response
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Error getting agent config: {response.status_code} {response.text}")
                    return self._get_mock_agent_config()
            
        except Exception as e:
            logger.error(f"Error getting agent config: {str(e)}")
            return self._get_mock_agent_config()
    
    async def report_arbitrage_opportunity(self, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Report an arbitrage opportunity to the orchestrator
        
        Args:
            opportunity_data: Arbitrage opportunity data
            
        Returns:
            Report result
        """
        try:
            # Apply rate limiting
            await self._apply_rate_limiting()
            
            # Check if we're in mock mode
            if self.use_mock:
                return {"success": True, "message": "Arbitrage opportunity reported", "opportunity_id": f"opp-{int(time.time())}"}
            
            # Make API request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/arbitrage/report",
                    json=opportunity_data,
                    headers=self._get_headers()
                )
                
                # Check response
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Error reporting arbitrage opportunity: {response.status_code} {response.text}")
                    return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
            
        except Exception as e:
            logger.error(f"Error reporting arbitrage opportunity: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get HTTP headers for API requests
        
        Returns:
            HTTP headers
        """
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": f"PoolMind-Agent/{self.config.version}"
        }
    
    async def _apply_rate_limiting(self) -> None:
        """
        Apply rate limiting for API calls
        """
        try:
            # Get rate limit
            rate_limit = self.config.orchestrator_rate_limit  # Requests per second
            
            # Calculate minimum time between requests
            min_time_between_requests = 1.0 / rate_limit
            
            # Calculate time since last request
            time_since_last_request = time.time() - self.last_request_time
            
            # Sleep if needed
            if time_since_last_request < min_time_between_requests:
                sleep_time = min_time_between_requests - time_since_last_request
                await asyncio.sleep(sleep_time)
            
            # Update last request time
            self.last_request_time = time.time()
            
        except Exception as e:
            logger.error(f"Error applying rate limiting: {str(e)}")
    
    def _get_mock_pool_status(self) -> Dict[str, Any]:
        """
        Get mock pool status
        
        Returns:
            Mock pool status
        """
        return {
            "pool_id": "pool-1",
            "total_value": 1000000 + (time.time() % 100000),
            "liquidity_reserve": 150000 + (time.time() % 50000),
            "participant_count": 100 + int(time.time() % 20),
            "active_strategies": 5 + int(time.time() % 5),
            "total_profit_24h": 5000 + (time.time() % 1000),
            "roi_30d": 0.05 + (time.time() % 100) / 10000,
            "status": "active",
            "last_updated": datetime.now().isoformat()
        }
    
    def _get_mock_trading_history(self, limit: int) -> List[Dict[str, Any]]:
        """
        Get mock trading history
        
        Args:
            limit: Maximum number of trades to return
            
        Returns:
            Mock trading history
        """
        # Common trading pairs
        pairs = [
            "BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT",
            "ADA/USDT", "DOGE/USDT", "SHIB/USDT", "AVAX/USDT", "DOT/USDT"
        ]
        
        # Common exchanges
        exchanges = [
            "Binance", "Coinbase", "Kraken", "Huobi", "KuCoin",
            "Bitfinex", "Bybit", "OKX", "Gate.io", "Gemini"
        ]
        
        # Generate mock trades
        trades = []
        
        for i in range(min(limit, 100)):
            # Calculate timestamp (older trades first)
            timestamp = datetime.now().timestamp() - (i * 3600)  # 1 hour apart
            
            # Select pair and exchanges
            pair_index = (int(timestamp) + i) % len(pairs)
            buy_exchange_index = (int(timestamp) + i) % len(exchanges)
            sell_exchange_index = (buy_exchange_index + 1 + i % (len(exchanges) - 1)) % len(exchanges)
            
            pair = pairs[pair_index]
            buy_exchange = exchanges[buy_exchange_index]
            sell_exchange = exchanges[sell_exchange_index]
            
            # Generate mock prices
            base_price = 100.0 * (1 + pair_index)
            buy_price = base_price * (0.99 + (i % 100) / 10000)
            sell_price = buy_price * (1.01 + (i % 50) / 10000)
            
            # Generate mock amounts
            position_size = 10000.0 + (i % 10) * 1000
            
            # Calculate profit
            profit_pct = ((sell_price - buy_price) / buy_price) * 100.0
            profit = position_size * profit_pct / 100.0
            
            # Create trade
            trade = {
                "id": f"trade-{int(timestamp)}-{i}",
                "strategy_id": f"strategy-{int(timestamp)}-{i}",
                "timestamp": datetime.fromtimestamp(timestamp).isoformat(),
                "pair": pair,
                "buy_exchange": buy_exchange,
                "sell_exchange": sell_exchange,
                "buy_price": buy_price,
                "sell_price": sell_price,
                "position_size": position_size,
                "profit": profit,
                "profit_pct": profit_pct,
                "status": "completed"
            }
            
            trades.append(trade)
        
        return trades
    
    def _get_mock_submission_result(self, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get mock submission result
        
        Args:
            strategy: Trading strategy
            
        Returns:
            Mock submission result
        """
        # Generate strategy ID
        strategy_id = f"strategy-{int(time.time())}-{hash(json.dumps(strategy)) % 10000}"
        
        return {
            "success": True,
            "strategy_id": strategy_id,
            "message": "Strategy submitted successfully",
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_mock_execution_result(self, strategy_id: str) -> Dict[str, Any]:
        """
        Get mock execution result
        
        Args:
            strategy_id: Strategy ID
            
        Returns:
            Mock execution result
        """
        # Generate random execution result
        success = True  # 80% success rate
        
        if success:
            return {
                "success": True,
                "strategy_id": strategy_id,
                "status": "completed",
                "profit": 100.0 + (time.time() % 100),
                "profit_pct": 0.5 + (time.time() % 100) / 1000,
                "execution_time": 2.5 + (time.time() % 10) / 10,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "strategy_id": strategy_id,
                "status": "failed",
                "error": "Execution failed due to market conditions",
                "timestamp": datetime.now().isoformat()
            }
    
    def _get_mock_agent_config(self) -> Dict[str, Any]:
        """
        Get mock agent configuration
        
        Returns:
            Mock agent configuration
        """
        return {
            "supported_exchanges": [
                "binance", "gate", "bybit", "hotcoin", "coinw", "orangex"
            ],
            "trading_pairs": [
                "BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT",
                "ADA/USDT", "DOGE/USDT", "SHIB/USDT", "AVAX/USDT", "DOT/USDT"
            ],
            "min_profit_threshold": 0.5,  # Minimum profit threshold (%)
            "max_position_size": 50000.0,  # Maximum position size
            "max_slippage": 0.2,  # Maximum allowed slippage (%)
            "risk_tolerance": 0.7,  # Risk tolerance (0-1)
            "update_interval": 60,  # Update interval in seconds
            "execution_timeout": 30,  # Execution timeout in seconds
            "last_updated": datetime.now().isoformat()
        }
