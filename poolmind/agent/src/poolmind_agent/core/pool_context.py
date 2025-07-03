"""
Pool Context Engine - Maintains real-time pool state
"""
from typing import Dict, List, Optional, Any
import logging
import asyncio
from datetime import datetime

from pydantic import BaseModel
import httpx

from poolmind_agent.utils.config import AgentConfig
from poolmind_agent.services.orchestrator_client import OrchestratorClient
from poolmind_agent.services.blockchain_client import BlockchainClient
from poolmind_agent.services.exchange_client import ExchangeClient

logger = logging.getLogger(__name__)

class PoolContextEngine:
    """
    Maintains real-time pool state including NAV tracking, participant behavior,
    withdrawal queue forecasting, and liquidity reserve calculations.
    """
    
    def __init__(self, config: AgentConfig):
        """
        Initialize the Pool Context Engine
        
        Args:
            config: Agent configuration
        """
        self.config = config
        self.orchestrator_client = OrchestratorClient(config)
        self.blockchain_client = BlockchainClient(config)
        self.exchange_client = ExchangeClient(config)
        
        # Cache for pool state
        self._pool_state_cache: Dict[str, Any] = {}
        self._last_update: Optional[datetime] = None
        self._update_interval = config.pool_context_update_interval
        
        logger.info("Pool Context Engine initialized")
    
    async def update_market_data(self, market_data: List[Dict[str, Any]]) -> bool:
        """
        Update the pool context with new market data
        
        Args:
            market_data: List of market data points
            
        Returns:
            bool: True if update was successful
        """
        try:
            if not market_data:
                logger.warning("No market data provided for update")
                return False
                
            # Update the last update timestamp
            self._last_update = datetime.now()
            
            # Process and store market data in cache
            for data_point in market_data:
                if 'timestamp' in data_point:
                    timestamp = data_point['timestamp']
                    self._pool_state_cache[f"market_data_{timestamp}"] = data_point
            
            logger.info(f"Updated pool context with {len(market_data)} market data points")
            return True
            
        except Exception as e:
            logger.error(f"Error updating market data: {str(e)}")
            return False
    
    async def update_config(self, config_updates: Dict[str, Any]) -> bool:
        """
        Update the pool context configuration
        
        Args:
            config_updates: Dictionary of configuration updates
            
        Returns:
            bool: True if update was successful
        """
        try:
            if not config_updates:
                logger.warning("No configuration updates provided")
                return False
                
            # Update configuration parameters
            for key, value in config_updates.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
                    logger.info(f"Updated config parameter {key} to {value}")
                else:
                    logger.warning(f"Unknown configuration parameter: {key}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating configuration: {str(e)}")
            return False
    
    async def get_current_state(self) -> Dict[str, Any]:
        """
        Get the current state of the pool
        
        Returns:
            Dict containing the current pool state
        """
        # Check if we need to update the cache
        now = datetime.now()
        if (self._last_update is None or 
            (now - self._last_update).total_seconds() > self._update_interval):
            await self._update_pool_state()
        
        return self._pool_state_cache
    
    async def _update_pool_state(self) -> None:
        """Update the cached pool state"""
        logger.debug("Updating pool state")
        
        try:
            # Get pool data from orchestrator
            pool_data = await self.orchestrator_client.get_pool_data()
            
            # Get blockchain data
            blockchain_data = await self.blockchain_client.get_contract_state()
            
            # Calculate derived metrics
            nav = await self._calculate_nav(pool_data, blockchain_data)
            liquidity_reserve = await self._calculate_liquidity_reserve(pool_data)
            withdrawal_forecast = await self._forecast_withdrawals(pool_data)
            participant_metrics = await self._analyze_participant_behavior(pool_data)
            
            # Update cache
            self._pool_state_cache = {
                "nav": nav,
                "total_value": pool_data.get("total_value", 0),
                "participant_count": pool_data.get("participant_count", 0),
                "liquidity_reserve": liquidity_reserve,
                "withdrawal_forecast": withdrawal_forecast,
                "participant_metrics": participant_metrics,
                "blockchain_data": blockchain_data,
                "updated_at": datetime.now().isoformat()
            }
            
            self._last_update = datetime.now()
            logger.info("Pool state updated successfully")
            
        except Exception as e:
            logger.error("Error updating pool state: %s", str(e))
            # If we have no cached state yet, initialize with empty values
            if not self._pool_state_cache:
                self._pool_state_cache = {
                    "nav": 0,
                    "total_value": 0,
                    "participant_count": 0,
                    "liquidity_reserve": 0,
                    "withdrawal_forecast": {"expected": 0, "worst_case": 0},
                    "participant_metrics": {},
                    "blockchain_data": {},
                    "updated_at": datetime.now().isoformat(),
                    "error": str(e)
                }
    
    async def _calculate_nav(self, pool_data: Dict[str, Any], 
                            blockchain_data: Dict[str, Any]) -> float:
        """
        Calculate the Net Asset Value of the pool
        
        Args:
            pool_data: Pool data from orchestrator
            blockchain_data: Blockchain contract state
            
        Returns:
            float: Current NAV
        """
        try:
            # Get total assets from blockchain data
            total_assets = blockchain_data.get("total_assets", 0)
            
            # Get total supply of tokens
            total_supply = blockchain_data.get("total_supply", 1)  # Default to 1 to avoid division by zero
            
            # Calculate NAV
            nav = total_assets / total_supply if total_supply > 0 else 0
            
            return nav
        except Exception as e:
            logger.error("Error calculating NAV: %s", str(e))
            return 0.0
    
    async def _calculate_liquidity_reserve(self, pool_data: Dict[str, Any]) -> float:
        """
        Calculate the liquidity reserve needed based on pool size and participant behavior
        
        Args:
            pool_data: Pool data from orchestrator
            
        Returns:
            float: Recommended liquidity reserve
        """
        try:
            total_value = pool_data.get("total_value", 0)
            participant_count = pool_data.get("participant_count", 0)
            
            # Simple model: higher reserve for more participants
            base_reserve_ratio = 0.10  # 10% base reserve
            participant_factor = min(0.05, 0.01 * (participant_count / 10))  # Additional 1% per 10 participants, max 5%
            
            reserve_ratio = base_reserve_ratio + participant_factor
            liquidity_reserve = total_value * reserve_ratio
            
            return liquidity_reserve
        except Exception as e:
            logger.error("Error calculating liquidity reserve: %s", str(e))
            return 0.0
    
    async def _forecast_withdrawals(self, pool_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Forecast expected withdrawals based on historical patterns
        
        Args:
            pool_data: Pool data from orchestrator
            
        Returns:
            Dict with expected and worst-case withdrawal forecasts
        """
        try:
            total_value = pool_data.get("total_value", 0)
            
            # Simple model for now
            expected_withdrawal_ratio = 0.05  # 5% expected withdrawals
            worst_case_ratio = 0.15  # 15% worst case
            
            return {
                "expected": total_value * expected_withdrawal_ratio,
                "worst_case": total_value * worst_case_ratio
            }
        except Exception as e:
            logger.error("Error forecasting withdrawals: %s", str(e))
            return {"expected": 0, "worst_case": 0}
    
    async def _analyze_participant_behavior(self, pool_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze participant behavior for risk assessment
        
        Args:
            pool_data: Pool data from orchestrator
            
        Returns:
            Dict with participant behavior metrics
        """
        try:
            # This would be a more complex analysis in production
            # For now, return simple metrics
            return {
                "avg_holding_period_days": 30,
                "withdrawal_frequency": "low",
                "new_participants_ratio": 0.1,  # 10% new participants
                "risk_profile": "moderate"
            }
        except Exception as e:
            logger.error("Error analyzing participant behavior: %s", str(e))
            return {}
    
    async def get_market_data(self) -> Dict[str, Any]:
        """
        Get current market data from exchanges
        
        Returns:
            Dict containing market data
        """
        try:
            # Get data from exchanges
            exchange_data = await self.exchange_client.get_market_data(
                self.config.tracked_exchanges,
                self.config.tracked_pairs
            )
            
            # Process and return the data
            return {
                "exchange_data": exchange_data,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error("Error getting market data: %s", str(e))
            return {
                "exchange_data": {},
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
