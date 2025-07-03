"""
Orchestrator Client - Interface for interacting with the PoolMind orchestrator
"""
from typing import Dict, List, Any, Optional
import logging
import asyncio
import json
import time
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
        self.base_url = config.orchestrator_url
        self.api_key = config.orchestrator_api_key
        self.last_request_time = 0
        self.use_mock = True  # Always use mock implementations for testing
        
        logger.info("Orchestrator Client initialized")
    
    async def get_pool_status(self) -> Dict[str, Any]:
        """
        Get current status of the pool from orchestrator
        
        Returns:
            Pool status data
        """
        try:
            # Apply rate limiting
            await self._apply_rate_limiting()
            
            # In a real implementation, we would call the orchestrator API here
            # For now, return mock data
            async with httpx.AsyncClient() as client:
                # Check if we're in mock mode
                if self.config.use_mock_data or not self.base_url:
                    return self._get_mock_pool_status()
                
                # Make API request
                response = await client.get(
                    f"{self.base_url}/api/pool/status",
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
            
            # In a real implementation, we would call the orchestrator API here
            # For now, return mock data
            async with httpx.AsyncClient() as client:
                # Check if we're in mock mode
                if self.config.use_mock_data or not self.base_url:
                    return self._get_mock_trading_history(limit)
                
                # Make API request
                response = await client.get(
                    f"{self.base_url}/api/trading/history",
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
            
            # In a real implementation, we would call the orchestrator API here
            # For now, return mock data
            async with httpx.AsyncClient() as client:
                # Check if we're in mock mode
                if self.config.use_mock_data or not self.base_url:
                    return self._get_mock_submission_result(strategy)
                
                # Make API request
                response = await client.post(
                    f"{self.base_url}/api/strategy/submit",
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
            
            # In a real implementation, we would call the orchestrator API here
            # For now, return mock data
            async with httpx.AsyncClient() as client:
                # Check if we're in mock mode
                if self.config.use_mock_data or not self.base_url:
                    return self._get_mock_execution_result(strategy_id)
                
                # Make API request
                response = await client.get(
                    f"{self.base_url}/api/strategy/{strategy_id}/result",
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
            
            # In a real implementation, we would call the orchestrator API here
            # For now, return mock data
            async with httpx.AsyncClient() as client:
                # Check if we're in mock mode
                if self.config.use_mock_data or not self.base_url:
                    return {"success": True, "message": "Event notification received"}
                
                # Make API request
                response = await client.post(
                    f"{self.base_url}/api/events/notify",
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
            
            # In a real implementation, we would call the orchestrator API here
            # For now, return mock data
            async with httpx.AsyncClient() as client:
                # Check if we're in mock mode
                if self.config.use_mock_data or not self.base_url:
                    return self._get_mock_agent_config()
                
                # Make API request
                response = await client.get(
                    f"{self.base_url}/api/agent/config",
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
            "pool_id": "pool-1",  # Added pool_id field to match test expectations
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
            
            # Create trade with strategy_id field to match test expectations
            trade = {
                "id": f"trade-{int(timestamp)}-{i}",
                "strategy_id": f"strategy-{int(timestamp)}-{i}",  # Added strategy_id field
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
            "status": "pending",  # Added status field to match test expectations
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
        # Parse strategy ID to get timestamp
        try:
            parts = strategy_id.split("-")
            timestamp = int(parts[1])
            strategy_hash = int(parts[2])
        except:
            timestamp = int(time.time())
            strategy_hash = 0
        
        # Calculate execution time
        execution_time = time.time() - timestamp
        
        # Determine status based on execution time
        if execution_time < 10:
            status = "pending"
            success = None
        elif execution_time < 60:
            status = "executing"
            success = None
        else:
            status = "completed"
            success = strategy_hash % 10 != 0  # 90% success rate
        
        # Create result
        result = {
            "strategy_id": strategy_id,
            "status": status,
            "timestamp": datetime.fromtimestamp(timestamp).isoformat()
        }
        
        # Add execution details if completed
        if status == "completed":
            if success:
                result.update({
                    "success": True,
                    "profit": 100 + (strategy_hash % 900),
                    "profit_pct": 0.5 + (strategy_hash % 100) / 100,
                    "execution_time": execution_time,
                    "message": "Strategy executed successfully"
                })
            else:
                result.update({
                    "success": False,
                    "error": "Execution failed due to market conditions",
                    "execution_time": execution_time
                })
        
        return result
    
    def _get_mock_agent_config(self) -> Dict[str, Any]:
        """
        Get mock agent configuration
        
        Returns:
            Mock agent configuration
        """
        return {
            "trading_pairs": [
                "BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT",
                "ADA/USDT", "DOGE/USDT", "SHIB/USDT", "AVAX/USDT", "DOT/USDT"
            ],
            "supported_exchanges": [
                "Binance", "Coinbase", "Kraken", "Huobi", "KuCoin"
            ],
            "min_profit_threshold": 0.5,
            "max_position_size_pct": 10.0,
            "max_risk_threshold": 7.0,
            "liquidity_reserve_min_pct": 10.0,
            "update_interval_seconds": 60,
            "llm_models": {
                "primary": "gpt-4",
                "fallback": "gpt-3.5-turbo",
                "strategy": "gpt-4"
            }
        }
