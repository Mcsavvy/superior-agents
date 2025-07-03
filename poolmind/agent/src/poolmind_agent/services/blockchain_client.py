"""
Blockchain Client - Interface for interacting with blockchain contracts
"""
from typing import Dict, List, Any, Optional
import logging
import asyncio
import time
from datetime import datetime

from poolmind_agent.utils.config import AgentConfig

logger = logging.getLogger(__name__)

class BlockchainClient:
    """
    Client for interacting with blockchain contracts
    """
    
    def __init__(self, config: AgentConfig):
        """
        Initialize the Blockchain Client
        
        Args:
            config: Agent configuration
        """
        self.config = config
        self.use_mock = True  # Always use mock implementations for testing
        self._initialize_providers()
        
        logger.info("Blockchain Client initialized")
    
    def _initialize_providers(self) -> None:
        """
        Initialize blockchain providers
        """
        try:
            # In a real implementation, we would initialize web3 providers here
            # For now, we'll just log that we're using mock providers
            self.providers = {}
            
            for chain in self.config.supported_chains:
                # Mock provider initialization
                self.providers[chain] = {
                    "name": chain,
                    "initialized": True,
                    "last_request": 0
                }
            
            logger.info(f"Initialized {len(self.providers)} blockchain providers")
            
        except Exception as e:
            logger.error(f"Error initializing blockchain providers: {str(e)}")
            raise
    
    async def get_pool_state(self) -> Dict[str, Any]:
        """
        Get current state of the pool from blockchain
        
        Returns:
            Pool state data
        """
        try:
            # In a real implementation, we would call the blockchain contract here
            # For now, return mock data
            
            # Apply rate limiting
            await self._apply_rate_limiting(self.config.primary_chain)
            
            # Mock pool state
            pool_state = {
                "total_value": self._get_mock_total_value(),
                "liquidity_reserve": self._get_mock_liquidity_reserve(),
                "participant_count": self._get_mock_participant_count(),
                "last_updated": datetime.now().timestamp()
            }
            
            logger.debug(f"Got pool state: {pool_state}")
            return pool_state
            
        except Exception as e:
            logger.error(f"Error getting pool state: {str(e)}")
            return {}
    
    async def get_participant_metrics(self) -> Dict[str, Any]:
        """
        Get metrics about pool participants
        
        Returns:
            Participant metrics
        """
        try:
            # Apply rate limiting
            await self._apply_rate_limiting(self.config.primary_chain)
            
            # Mock participant metrics
            metrics = {
                "avg_holding_period": 30 + (time.time() % 30),  # Changed key name to match test expectations
                "withdrawal_frequency": self._get_mock_withdrawal_frequency(),
                "new_participants_ratio": 0.1 + (time.time() % 100) / 1000,
                "top_participants": [
                    {"address": f"0x{i}{'0' * 39}", "share": 0.1 - (i * 0.01)} 
                    for i in range(5)
                ],
                "avg_holding_period_days": 30 + (time.time() % 30)  # Keep original key for backward compatibility
            }
            
            logger.debug(f"Got participant metrics")
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting participant metrics: {str(e)}")
            return {}
    
    async def get_withdrawal_forecast(self) -> Dict[str, Any]:
        """
        Get forecast of upcoming withdrawals
        
        Returns:
            Withdrawal forecast
        """
        try:
            # Apply rate limiting
            await self._apply_rate_limiting(self.config.primary_chain)
            
            # Get pool state for reference
            pool_state = await self.get_pool_state()
            total_value = pool_state.get("total_value", 1000000)
            
            # Mock withdrawal forecast
            forecast = {
                "expected": total_value * 0.05,  # 5% of total value
                "pending": total_value * 0.02,   # 2% of total value
                "probability": 0.8,              # 80% probability
                "timeframe_hours": 24
            }
            
            logger.debug(f"Got withdrawal forecast")
            return forecast
            
        except Exception as e:
            logger.error(f"Error getting withdrawal forecast: {str(e)}")
            return {}
    
    async def execute_transaction(self, 
                                transaction: Dict[str, Any], 
                                gas_price: str = "medium") -> Dict[str, Any]:
        """
        Execute a blockchain transaction
        
        Args:
            transaction: Transaction data
            gas_price: Gas price level (low, medium, high)
            
        Returns:
            Transaction result
        """
        try:
            # Extract transaction details
            chain = transaction.get("chain", self.config.primary_chain)
            contract_address = transaction.get("contract_address", "")
            method = transaction.get("method", "")
            params = transaction.get("params", {})
            
            # Validate chain
            if chain not in self.providers:
                logger.warning(f"Chain {chain} not supported")
                return {"success": False, "error": f"Chain {chain} not supported"}
            
            # Apply rate limiting
            await self._apply_rate_limiting(chain)
            
            # Log transaction
            logger.info(f"Executing transaction on {chain}: {method}")
            
            # Simulate transaction execution
            await asyncio.sleep(2)  # Simulate blockchain delay
            
            # Generate mock transaction hash
            tx_hash = f"0x{''.join([hex(int(time.time() * 1000))[2:] for _ in range(4)])}"
            
            # Create transaction result
            tx_result = {
                "success": True,
                "chain": chain,
                "contract_address": contract_address,
                "method": method,
                "tx_hash": tx_hash,
                "gas_used": 100000 + int(time.time() % 100000),
                "timestamp": datetime.now().timestamp()
            }
            
            logger.info(f"Transaction executed successfully: {tx_hash}")
            return tx_result
            
        except Exception as e:
            logger.error(f"Error executing transaction: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_gas_price(self, chain: str = None) -> Dict[str, float]:
        """
        Get current gas prices for a blockchain
        
        Args:
            chain: Blockchain name
            
        Returns:
            Gas price data
        """
        try:
            # Use primary chain if none specified
            if chain is None:
                chain = self.config.primary_chain
                
            # Validate chain
            if chain not in self.providers:
                logger.warning(f"Chain {chain} not supported")
                return {}
            
            # Apply rate limiting
            await self._apply_rate_limiting(chain)
            
            # Mock gas prices (in gwei) with keys matching test expectations
            gas_prices = {
                "slow": 10 + (time.time() % 10),
                "standard": 20 + (time.time() % 20),
                "fast": 30 + (time.time() % 30),
                "timestamp": datetime.now().timestamp()
            }
            
            logger.debug(f"Got gas prices for {chain}")
            return gas_prices
            
        except Exception as e:
            logger.error(f"Error getting gas prices for {chain}: {str(e)}")
            return {}
    
    async def verify_double_signature(self, 
                                    transaction: Dict[str, Any], 
                                    signatures: List[str]) -> bool:
        """
        Verify double signatures for a transaction
        
        Args:
            transaction: Transaction data
            signatures: List of signatures
            
        Returns:
            True if signatures are valid, False otherwise
        """
        try:
            # In a real implementation, we would verify signatures here
            # For now, just check if we have at least 2 signatures
            if len(signatures) < 2:
                logger.warning(f"Insufficient signatures: {len(signatures)}")
                return False
            
            # Simulate verification
            await asyncio.sleep(0.5)
            
            logger.info(f"Verified {len(signatures)} signatures")
            return True
            
        except Exception as e:
            logger.error(f"Error verifying signatures: {str(e)}")
            return False
    
    async def _apply_rate_limiting(self, chain: str) -> None:
        """
        Apply rate limiting for blockchain API calls
        
        Args:
            chain: Blockchain name
        """
        try:
            # Get rate limit for chain
            rate_limit = self.config.chain_rate_limits.get(chain, 5)  # Default: 5 requests per second
            
            # Calculate minimum time between requests
            min_time_between_requests = 1.0 / rate_limit
            
            # Get last request time
            last_request_time = self.providers[chain]["last_request"]
            
            # Calculate time since last request
            time_since_last_request = time.time() - last_request_time
            
            # Sleep if needed
            if time_since_last_request < min_time_between_requests:
                sleep_time = min_time_between_requests - time_since_last_request
                await asyncio.sleep(sleep_time)
            
            # Update last request time
            self.providers[chain]["last_request"] = time.time()
            
        except Exception as e:
            logger.error(f"Error applying rate limiting for {chain}: {str(e)}")
    
    def _get_mock_total_value(self) -> float:
        """
        Get mock total value of the pool
        
        Returns:
            Mock total value
        """
        # Base value
        base_value = 1000000.0
        
        # Add time-based variation (±10%)
        time_factor = 1.0 + (time.time() % 1000) / 5000.0 - 0.1
        
        return base_value * time_factor
    
    def _get_mock_liquidity_reserve(self) -> float:
        """
        Get mock liquidity reserve of the pool
        
        Returns:
            Mock liquidity reserve
        """
        # Get total value
        total_value = self._get_mock_total_value()
        
        # Reserve is 10-20% of total value
        reserve_ratio = 0.1 + (time.time() % 100) / 1000.0
        
        return total_value * reserve_ratio
    
    def _get_mock_participant_count(self) -> int:
        """
        Get mock participant count
        
        Returns:
            Mock participant count
        """
        # Base count
        base_count = 100
        
        # Add time-based variation (±20)
        time_variation = int(time.time() % 40) - 20
        
        return base_count + time_variation
    
    def _get_mock_withdrawal_frequency(self) -> str:
        """
        Get mock withdrawal frequency
        
        Returns:
            Mock withdrawal frequency (low, medium, high)
        """
        # Get random value
        random_value = time.time() % 3
        
        if random_value < 1:
            return "low"
        elif random_value < 2:
            return "medium"
        else:
            return "high"
