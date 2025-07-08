#!/usr/bin/env python3
"""
PoolMind Arbitrage Agent Starter

This script initializes and runs the PoolMind arbitrage agent for STX trading
across multiple exchanges with automatic fund management and profit reporting.
"""

import os
import sys
import time
import signal
from pathlib import Path
from typing import Dict, Any, List
from loguru import logger
from datetime import datetime, timedelta

# Add the parent directory to the path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent.poolmind_arbitrage import PoolMindArbitrageAgent, PoolMindArbitragePromptGenerator
from src.sensor.poolmind import PoolMindSensor
from src.client.poolmind import PoolMindClient
from src.client.rag import RAGClient
from src.flows.poolmind_arbitrage import poolmind_arbitrage_flow, poolmind_monitoring_flow
from src.genner import get_genner
from src.db.interface import DBInterface
from src.db.sqlite import SQLiteDB
from src.container import ContainerManager
from src.helper import nanoid

import docker
from anthropic import Anthropic
from openai import OpenAI


class PoolMindArbitrageStarter:
    """
    Starter class for PoolMind arbitrage agent.
    
    This class handles the initialization and execution of the PoolMind arbitrage agent
    with all necessary components and configurations.
    """
    
    def __init__(self):
        """Initialize the PoolMind arbitrage starter."""
        self.agent_id = os.getenv("POOLMIND_AGENT_ID", "poolmind-arbitrage-agent")
        self.session_id = f"{self.agent_id}-{nanoid(8)}"
        self.running = True
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info(f"Initializing PoolMind Arbitrage Agent - ID: {self.agent_id}")
        logger.info(f"Session ID: {self.session_id}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    def _load_environment_config(self) -> Dict[str, Any]:
        """
        Load configuration from environment variables.
        
        Returns:
            Dict[str, Any]: Configuration dictionary
        """
        config = {
            # LLM Configuration
            "model_backend": os.getenv("POOLMIND_MODEL_BACKEND", "deepseek_v3_or"),
            "openai_api_key": os.getenv("OPENAI_API_KEY"),
            "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
            "openrouter_api_key": os.getenv("OPENROUTER_API_KEY"),
            
            # PoolMind Configuration
            "poolmind_api_url": os.getenv("POOLMIND_API_URL", "http://localhost:3000"),
            "poolmind_hmac_secret": os.getenv("POOLMIND_HMAC_SECRET"),
            
            # Trading Configuration
            "supported_exchanges": os.getenv(
                "POOLMIND_SUPPORTED_EXCHANGES", 
                "binance,okx,gate,hotcoin,bybit,coinw,orangex"
            ).split(","),
            "min_profit_threshold": float(os.getenv("POOLMIND_MIN_PROFIT_THRESHOLD", "0.5")),
            "max_trade_size_percent": float(os.getenv("POOLMIND_MAX_TRADE_SIZE_PERCENT", "10.0")),
            "stop_loss_threshold": float(os.getenv("POOLMIND_STOP_LOSS_THRESHOLD", "5.0")),
            
            # Database Configuration
            "database_path": os.getenv("POOLMIND_DATABASE_PATH", "data/poolmind_arbitrage.db"),
            
            # RAG Configuration
            "rag_api_url": os.getenv("RAG_API_URL", "http://localhost:8080"),
            
            # Container Configuration
            "container_image": os.getenv("CONTAINER_IMAGE", "superioragents/agent-executor:latest"),
            "container_cache_folder": os.getenv("CONTAINER_CACHE_FOLDER", "/tmp/poolmind_cache"),
            
            # Exchange API Configuration
            "exchange_configs": self._load_exchange_configs(),
            
            # Monitoring Configuration
            "monitoring_interval": int(os.getenv("POOLMIND_MONITORING_INTERVAL", "60")),
            "continuous_mode": os.getenv("POOLMIND_CONTINUOUS_MODE", "false").lower() == "true",
        }
        
        # Validate required configuration
        required_keys = ["poolmind_hmac_secret"]
        for key in required_keys:
            if not config.get(key):
                raise ValueError(f"Required environment variable {key.upper()} is not set")
        
        return config
    
    def _load_exchange_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        Load exchange-specific configurations.
        
        Returns:
            Dict[str, Dict[str, Any]]: Exchange configurations
        """
        return {
            "binance": {
                "api_endpoint": "https://api.binance.com",
                "api_key": os.getenv("BINANCE_API_KEY"),
                "api_secret": os.getenv("BINANCE_API_SECRET"),
                "rate_limits": {"requests_per_second": 10},
                "supported_pairs": ["STX/USDT"],
                "min_order_size": 10,
            },
            "okx": {
                "api_endpoint": "https://www.okx.com",
                "api_key": os.getenv("OKX_API_KEY"),
                "api_secret": os.getenv("OKX_API_SECRET"),
                "passphrase": os.getenv("OKX_PASSPHRASE"),
                "rate_limits": {"requests_per_second": 20},
                "supported_pairs": ["STX/USDT"],
                "min_order_size": 1,
            },
            "gate": {
                "api_endpoint": "https://api.gateio.ws",
                "api_key": os.getenv("GATE_API_KEY"),
                "api_secret": os.getenv("GATE_API_SECRET"),
                "rate_limits": {"requests_per_second": 100},
                "supported_pairs": ["STX/USDT"],
                "min_order_size": 1,
            },
            "hotcoin": {
                "api_endpoint": "https://api.hotcoin.com",
                "api_key": os.getenv("HOTCOIN_API_KEY"),
                "api_secret": os.getenv("HOTCOIN_API_SECRET"),
                "rate_limits": {"requests_per_second": 10},
                "supported_pairs": ["STX/USDT"],
                "min_order_size": 10,
            },
            "bybit": {
                "api_endpoint": "https://api.bybit.com",
                "api_key": os.getenv("BYBIT_API_KEY"),
                "api_secret": os.getenv("BYBIT_API_SECRET"),
                "rate_limits": {"requests_per_second": 50},
                "supported_pairs": ["STX/USDT"],
                "min_order_size": 1,
            },
            "coinw": {
                "api_endpoint": "https://api.coinw.com",
                "api_key": os.getenv("COINW_API_KEY"),
                "api_secret": os.getenv("COINW_API_SECRET"),
                "rate_limits": {"requests_per_second": 20},
                "supported_pairs": ["STX/USDT"],
                "min_order_size": 1,
            },
            "orangex": {
                "api_endpoint": "https://api.orangex.com",
                "api_key": os.getenv("ORANGEX_API_KEY"),
                "api_secret": os.getenv("ORANGEX_API_SECRET"),
                "rate_limits": {"requests_per_second": 10},
                "supported_pairs": ["STX/USDT"],
                "min_order_size": 1,
            },
        }
    
    def _initialize_components(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initialize all required components for the agent.
        
        Args:
            config (Dict[str, Any]): Configuration dictionary
            
        Returns:
            Dict[str, Any]: Initialized components
        """
        components = {}
        
        # Initialize database
        logger.info("Initializing database...")
        os.makedirs(os.path.dirname(config["database_path"]), exist_ok=True)
        components["db"] = SQLiteDB(config["database_path"])
        
        # Initialize RAG client
        logger.info("Initializing RAG client...")
        components["rag"] = RAGClient(
            agent_id=self.agent_id,
            session_id=self.session_id,
            base_url=config["rag_api_url"]
        )
        
        # Initialize PoolMind sensor
        logger.info("Initializing PoolMind sensor...")
        components["sensor"] = PoolMindSensor(
            poolmind_api_url=config["poolmind_api_url"],
            supported_exchanges=config["supported_exchanges"],
            exchange_configs=config["exchange_configs"]
        )
        
        # Initialize PoolMind client
        logger.info("Initializing PoolMind client...")
        components["poolmind_client"] = PoolMindClient(
            base_url=config["poolmind_api_url"],
            agent_id=self.agent_id,
            hmac_secret=config["poolmind_hmac_secret"]
        )
        
        # Initialize LLM generator
        logger.info(f"Initializing LLM generator ({config['model_backend']})...")
        components["genner"] = self._initialize_genner(config)
        
        # Initialize Docker client and container manager
        logger.info("Initializing container manager...")
        docker_client = docker.from_env()
        components["container_manager"] = ContainerManager(
            client=docker_client,
            container_identifier=config["container_image"],
            host_cache_folder=config["container_cache_folder"],
            in_con_env={}
        )
        
        # Initialize prompt generator
        logger.info("Initializing prompt generator...")
        components["prompt_generator"] = PoolMindArbitragePromptGenerator()
        
        # Initialize the main agent
        logger.info("Initializing PoolMind arbitrage agent...")
        components["agent"] = PoolMindArbitrageAgent(
            agent_id=self.agent_id,
            rag=components["rag"],
            db=components["db"],
            sensor=components["sensor"],
            genner=components["genner"],
            container_manager=components["container_manager"],
            prompt_generator=components["prompt_generator"],
            poolmind_api_url=config["poolmind_api_url"],
            hmac_secret=config["poolmind_hmac_secret"],
            supported_exchanges=config["supported_exchanges"],
            min_profit_threshold=config["min_profit_threshold"],
            max_trade_size_percent=config["max_trade_size_percent"],
            stop_loss_threshold=config["stop_loss_threshold"]
        )
        
        return components
    
    def _initialize_genner(self, config: Dict[str, Any]):
        """
        Initialize the LLM generator based on configuration.
        
        Args:
            config (Dict[str, Any]): Configuration dictionary
            
        Returns:
            Genner: Initialized LLM generator
        """
        backend = config["model_backend"]
        
        # Initialize clients based on backend
        clients = {}
        if config.get("openai_api_key"):
            clients["openai_client"] = OpenAI(api_key=config["openai_api_key"])
        if config.get("anthropic_api_key"):
            clients["anthropic_client"] = Anthropic(api_key=config["anthropic_api_key"])
        
        # Stream function for real-time output
        def stream_fn(token: str):
            print(token, end="", flush=True)
        
        return get_genner(
            backend=backend,
            stream_fn=stream_fn,
            **clients
        )
    
    def _run_single_cycle(self, components: Dict[str, Any], config: Dict[str, Any]):
        """
        Run a single arbitrage cycle.
        
        Args:
            components (Dict[str, Any]): Initialized components
            config (Dict[str, Any]): Configuration dictionary
        """
        logger.info("Starting single arbitrage cycle...")
        
        # Simple summarizer function
        def summarizer(text_list: List[str]) -> str:
            if isinstance(text_list, list):
                return " ".join(text_list)
            return str(text_list)
        
        try:
            poolmind_arbitrage_flow(
                agent=components["agent"],
                session_id=self.session_id,
                role="professional STX arbitrage trader",
                supported_exchanges=config["supported_exchanges"],
                min_profit_threshold=config["min_profit_threshold"],
                max_trade_size_percent=config["max_trade_size_percent"],
                prev_strat=None,  # Could be enhanced to fetch previous strategy
                notif_str="STX arbitrage opportunity monitoring",
                poolmind_client=components["poolmind_client"],
                summarizer=summarizer
            )
            logger.info("Single arbitrage cycle completed successfully")
        except Exception as e:
            logger.error(f"Error in arbitrage cycle: {e}")
    
    def _run_continuous_monitoring(self, components: Dict[str, Any], config: Dict[str, Any]):
        """
        Run continuous monitoring mode.
        
        Args:
            components (Dict[str, Any]): Initialized components
            config (Dict[str, Any]): Configuration dictionary
        """
        logger.info("Starting continuous monitoring mode...")
        
        try:
            poolmind_monitoring_flow(
                agent=components["agent"],
                session_id=self.session_id,
                poolmind_client=components["poolmind_client"],
                monitoring_interval=config["monitoring_interval"]
            )
        except Exception as e:
            logger.error(f"Error in continuous monitoring: {e}")
    
    def run(self):
        """
        Main execution method for the PoolMind arbitrage agent.
        """
        try:
            # Load configuration
            logger.info("Loading configuration...")
            config = self._load_environment_config()
            
            # Initialize components
            logger.info("Initializing components...")
            components = self._initialize_components(config)
            
            # Log startup information
            logger.info(f"PoolMind Arbitrage Agent started successfully!")
            logger.info(f"Agent ID: {self.agent_id}")
            logger.info(f"Session ID: {self.session_id}")
            logger.info(f"Supported exchanges: {', '.join(config['supported_exchanges'])}")
            logger.info(f"Min profit threshold: {config['min_profit_threshold']}%")
            logger.info(f"Max trade size: {config['max_trade_size_percent']}%")
            logger.info(f"Continuous mode: {config['continuous_mode']}")
            
            # Run based on mode
            if config["continuous_mode"]:
                self._run_continuous_monitoring(components, config)
            else:
                self._run_single_cycle(components, config)
            
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            sys.exit(1)
        finally:
            logger.info("PoolMind Arbitrage Agent shutdown complete")


def main():
    """
    Main entry point for the PoolMind arbitrage agent.
    """
    # Configure logging
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    # Add file logging
    log_file = os.getenv("POOLMIND_LOG_FILE", "logs/poolmind_arbitrage.log")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logger.add(
        log_file,
        rotation="100 MB",
        retention="30 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG"
    )
    
    # Create and run the starter
    starter = PoolMindArbitrageStarter()
    starter.run()


if __name__ == "__main__":
    main() 