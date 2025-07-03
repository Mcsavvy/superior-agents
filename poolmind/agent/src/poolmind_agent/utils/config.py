"""
Configuration utilities for the PoolMind agent
"""
from typing import Dict, List, Any, Optional, Set
import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class AgentConfig:
    """
    Configuration for the PoolMind agent
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize agent configuration
        
        Args:
            config_path: Path to config file (optional)
        """
        # Load environment variables
        load_dotenv()
        
        # Set default values
        self._set_defaults()
        
        # Load config from file if provided
        if config_path:
            self._load_from_file(config_path)
        
        # Load config from environment variables
        self._load_from_env()
        
        # Validate config
        self._validate()
        
        logger.info("Agent configuration loaded")
    
    def _set_defaults(self) -> None:
        """
        Set default configuration values
        """
        # Version
        self.version = "0.1.0"
        
        # General settings
        self.debug = False
        self.use_mock_data = False
        
        # Mock settings for testing
        self.use_mock_exchange = True
        self.use_mock_blockchain = True
        self.use_mock_orchestrator = True
        
        # API settings
        self.api_host = "0.0.0.0"
        self.api_port = 8000
        
        # Logging
        self.log_level = "INFO"
        self.verbose_llm = False
        self.enable_streaming = False
        
        # Trading settings
        self.trading_pairs = [
            "BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT",
            "ADA/USDT", "DOGE/USDT", "SHIB/USDT", "AVAX/USDT", "DOT/USDT"
        ]
        self.supported_exchanges = [
            "Binance", "Coinbase", "Kraken", "Huobi", "KuCoin"
        ]
        self.supported_chains = [
            "Ethereum", "Binance Smart Chain", "Solana", "Polygon", "Avalanche"
        ]
        self.primary_chain = "Ethereum"
        
        # Risk settings
        self.min_profit_threshold = 0.5  # Minimum profit percentage
        self.max_position_size_pct = 10.0  # Maximum position size as percentage of total capital
        self.max_risk_threshold = 7.0  # Maximum risk score (0-10)
        self.liquidity_reserve_min_pct = 10.0  # Minimum liquidity reserve percentage
        
        # LLM settings
        self.primary_llm_model = "gpt-4"
        self.primary_llm_temperature = 0.2
        self.fallback_llm_model = "gpt-3.5-turbo"
        self.fallback_llm_temperature = 0.3
        self.strategy_llm_model = "gpt-4"
        self.strategy_llm_temperature = 0.4
        
        # RAG settings
        self.rag_data_path = "./data/rag"
        self.rag_enable_telemetry = False
        
        # Pool context settings
        self.pool_context_update_interval = 60  # Update interval in seconds
        self.pool_context_cache_ttl = 300  # Cache TTL in seconds
        
        # Execution settings
        self.max_slippage_pct = 1.0  # Maximum allowed slippage percentage
        self.execution_timeout_seconds = 60  # Execution timeout in seconds
        self.gas_price_level = "medium"  # Gas price level (low, medium, high)
        
        # Exchange settings
        self.exchange_fees = {
            "Binance": 0.1,
            "Coinbase": 0.5,
            "Kraken": 0.26,
            "Huobi": 0.2,
            "KuCoin": 0.1
        }
        self.exchange_rate_limits = {
            "Binance": 10,
            "Coinbase": 5,
            "Kraken": 5,
            "Huobi": 10,
            "KuCoin": 10
        }
        
        # Blockchain settings
        self.chain_rate_limits = {
            "Ethereum": 5,
            "Binance Smart Chain": 10,
            "Solana": 20,
            "Polygon": 10,
            "Avalanche": 10
        }
        
        # LLM settings
        self.llm_models = {
            "primary": "gpt-4",
            "fallback": "gpt-3.5-turbo",
            "strategy": "gpt-4"
        }
        self.llm_timeout_seconds = 30
        self.llm_temperature = 0.2
        self.llm_max_tokens = 2000
        
        # RAG settings
        self.rag_collection_names = {
            "strategies": "poolmind_strategies",
            "trades": "poolmind_trades",
            "market_conditions": "poolmind_market_conditions"
        }
        self.rag_similarity_threshold = 0.85
        self.rag_max_results = 5
        
        # API settings
        self.api_host = "0.0.0.0"
        self.api_port = 8000
        
        # Orchestrator settings
        self.orchestrator_url = ""
        self.orchestrator_api_key = ""
        self.orchestrator_rate_limit = 10
        
        # Update interval
        self.update_interval_seconds = 60
    
    def _load_from_file(self, config_path: str) -> None:
        """
        Load configuration from file
        
        Args:
            config_path: Path to config file
        """
        try:
            # Check if file exists
            if not os.path.exists(config_path):
                logger.warning(f"Config file not found: {config_path}")
                return
            
            # Load config from file
            with open(config_path, "r") as f:
                config = json.load(f)
            
            # Update config values
            for key, value in config.items():
                if hasattr(self, key):
                    setattr(self, key, value)
                else:
                    logger.warning(f"Unknown config key: {key}")
            
            logger.info(f"Loaded config from file: {config_path}")
            
        except Exception as e:
            logger.error(f"Error loading config from file: {str(e)}")
    
    def _load_from_env(self) -> None:
        """
        Load configuration from environment variables
        """
        try:
            # Debug mode
            if os.getenv("POOLMIND_DEBUG"):
                self.debug = os.getenv("POOLMIND_DEBUG").lower() == "true"
            
            # Mock data
            if os.getenv("POOLMIND_USE_MOCK_DATA"):
                self.use_mock_data = os.getenv("POOLMIND_USE_MOCK_DATA").lower() == "true"
            
            # LLM settings
            if os.getenv("POOLMIND_LLM_PRIMARY_MODEL"):
                self.llm_models["primary"] = os.getenv("POOLMIND_LLM_PRIMARY_MODEL")
            
            if os.getenv("POOLMIND_LLM_FALLBACK_MODEL"):
                self.llm_models["fallback"] = os.getenv("POOLMIND_LLM_FALLBACK_MODEL")
            
            if os.getenv("POOLMIND_LLM_STRATEGY_MODEL"):
                self.llm_models["strategy"] = os.getenv("POOLMIND_LLM_STRATEGY_MODEL")
            
            if os.getenv("POOLMIND_LLM_TIMEOUT"):
                self.llm_timeout_seconds = int(os.getenv("POOLMIND_LLM_TIMEOUT"))
            
            if os.getenv("POOLMIND_LLM_TEMPERATURE"):
                self.llm_temperature = float(os.getenv("POOLMIND_LLM_TEMPERATURE"))
            
            # API settings
            if os.getenv("POOLMIND_API_HOST"):
                self.api_host = os.getenv("POOLMIND_API_HOST")
            
            if os.getenv("POOLMIND_API_PORT"):
                self.api_port = int(os.getenv("POOLMIND_API_PORT"))
            
            # Orchestrator settings
            if os.getenv("POOLMIND_ORCHESTRATOR_URL"):
                self.orchestrator_url = os.getenv("POOLMIND_ORCHESTRATOR_URL")
            
            if os.getenv("POOLMIND_ORCHESTRATOR_API_KEY"):
                self.orchestrator_api_key = os.getenv("POOLMIND_ORCHESTRATOR_API_KEY")
            
            # Risk settings
            if os.getenv("POOLMIND_MIN_PROFIT_THRESHOLD"):
                self.min_profit_threshold = float(os.getenv("POOLMIND_MIN_PROFIT_THRESHOLD"))
            
            if os.getenv("POOLMIND_MAX_POSITION_SIZE_PCT"):
                self.max_position_size_pct = float(os.getenv("POOLMIND_MAX_POSITION_SIZE_PCT"))
            
            if os.getenv("POOLMIND_MAX_RISK_THRESHOLD"):
                self.max_risk_threshold = float(os.getenv("POOLMIND_MAX_RISK_THRESHOLD"))
            
            logger.info("Loaded config from environment variables")
            
        except Exception as e:
            logger.error(f"Error loading config from environment variables: {str(e)}")
    
    def _validate(self) -> None:
        """
        Validate configuration
        """
        # Check if required LLM models are set
        if not self.llm_models.get("primary"):
            logger.warning("Primary LLM model not set")
        
        if not self.llm_models.get("fallback"):
            logger.warning("Fallback LLM model not set")
        
        # Check if trading pairs are set
        if not self.trading_pairs:
            logger.warning("No trading pairs configured")
        
        # Check if supported exchanges are set
        if not self.supported_exchanges:
            logger.warning("No supported exchanges configured")
    
    def update(self, updates: Dict[str, Any]) -> bool:
        """
        Update configuration
        
        Args:
            updates: Configuration updates
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update config values
            for key, value in updates.items():
                if hasattr(self, key):
                    setattr(self, key, value)
                else:
                    logger.warning(f"Unknown config key: {key}")
            
            # Validate updated config
            self._validate()
            
            logger.info("Configuration updated")
            return True
            
        except Exception as e:
            logger.error(f"Error updating configuration: {str(e)}")
            return False
    
    def to_dict(self, exclude_sensitive: bool = False) -> Dict[str, Any]:
        """
        Convert configuration to dictionary
        
        Args:
            exclude_sensitive: Whether to exclude sensitive fields
            
        Returns:
            Configuration as dictionary
        """
        # Get all attributes
        config_dict = {}
        
        # Sensitive fields to exclude
        sensitive_fields = {"orchestrator_api_key"}
        
        for key, value in self.__dict__.items():
            # Skip private attributes
            if key.startswith("_"):
                continue
            
            # Skip sensitive fields if requested
            if exclude_sensitive and key in sensitive_fields:
                continue
            
            config_dict[key] = value
        
        return config_dict
    
    def save_to_file(self, config_path: str) -> bool:
        """
        Save configuration to file
        
        Args:
            config_path: Path to config file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            # Convert config to dict
            config_dict = self.to_dict()
            
            # Save config to file
            with open(config_path, "w") as f:
                json.dump(config_dict, f, indent=2)
            
            logger.info(f"Saved config to file: {config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving config to file: {str(e)}")
            return False
