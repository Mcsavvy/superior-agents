"""
Real Exchange Client - Interface for interacting with cryptocurrency exchanges
"""
from typing import Dict, List, Any, Optional
import logging
import asyncio
import time
import os
import hmac
import hashlib
import json
import base64
import urllib.parse
from datetime import datetime

import httpx
from dotenv import load_dotenv

from poolmind_agent.utils.config import AgentConfig

logger = logging.getLogger(__name__)

class RealExchangeClient:
    """
    Client for interacting with cryptocurrency exchanges using real API credentials
    """
    
    def __init__(self, config: AgentConfig):
        """
        Initialize the Exchange Client
        
        Args:
            config: Agent configuration
        """
        self.config = config
        
        # Load environment variables
        load_dotenv()
        
        # Initialize exchange clients
        self.exchange_clients = {}
        self._initialize_clients()
        
        logger.info("Real Exchange Client initialized")
    
    def _initialize_clients(self) -> None:
        """
        Initialize exchange API clients using environment variables
        """
        try:
            # Hotcoin
            if os.getenv("HOTCOIN_ACCESS_KEY") and os.getenv("HOTCOIN_SECRET_KEY"):
                self.exchange_clients["hotcoin"] = {
                    "name": "Hotcoin",
                    "access_key": os.getenv("HOTCOIN_ACCESS_KEY"),
                    "secret_key": os.getenv("HOTCOIN_SECRET_KEY"),
                    "base_url": "https://api.hotcoin.com",
                    "last_request": 0
                }
                logger.info("Initialized Hotcoin client")
            
            # Gate.io
            if os.getenv("GATE_API_KEY") and os.getenv("GATE_API_SECRET"):
                self.exchange_clients["gate"] = {
                    "name": "Gate.io",
                    "api_key": os.getenv("GATE_API_KEY"),
                    "api_secret": os.getenv("GATE_API_SECRET"),
                    "base_url": "https://api.gateio.ws/api/v4",
                    "last_request": 0
                }
                logger.info("Initialized Gate.io client")
            
            # Binance
            if os.getenv("BINANCE_API_KEY") and os.getenv("BINANCE_API_SECRET"):
                self.exchange_clients["binance"] = {
                    "name": "Binance",
                    "api_key": os.getenv("BINANCE_API_KEY"),
                    "api_secret": os.getenv("BINANCE_API_SECRET"),
                    "base_url": "https://api.binance.com/api/v3",
                    "last_request": 0
                }
                logger.info("Initialized Binance client")
            
            # Coin W
            if os.getenv("COINW_API_KEY") and os.getenv("COINW_SECRET_KEY"):
                self.exchange_clients["coinw"] = {
                    "name": "Coin W",
                    "api_key": os.getenv("COINW_API_KEY"),
                    "secret_key": os.getenv("COINW_SECRET_KEY"),
                    "base_url": "https://api.coinw.com",
                    "last_request": 0
                }
                logger.info("Initialized Coin W client")
            
            # Bybit
            if os.getenv("BYBIT_API_KEY") and os.getenv("BYBIT_API_SECRET"):
                self.exchange_clients["bybit"] = {
                    "name": "Bybit",
                    "api_key": os.getenv("BYBIT_API_KEY"),
                    "api_secret": os.getenv("BYBIT_API_SECRET"),
                    "base_url": "https://api.bybit.com",
                    "last_request": 0
                }
                logger.info("Initialized Bybit client")
            
            # OrangeX
            if os.getenv("ORANGEX_API_KEY") and os.getenv("ORANGEX_SECRET_KEY"):
                self.exchange_clients["orangex"] = {
                    "name": "OrangeX",
                    "api_key": os.getenv("ORANGEX_API_KEY"),
                    "secret_key": os.getenv("ORANGEX_SECRET_KEY"),
                    "base_url": "https://api.orangex.com",
                    "last_request": 0
                }
                logger.info("Initialized OrangeX client")
            
            logger.info(f"Initialized {len(self.exchange_clients)} exchange clients")
            
        except Exception as e:
            logger.error(f"Error initializing exchange clients: {str(e)}")
            raise
    
    async def _apply_rate_limiting(self, exchange: str) -> None:
        """
        Apply rate limiting for exchange API calls
        
        Args:
            exchange: Exchange name
        """
        try:
            # Get rate limit for exchange
            rate_limit = self.config.exchange_rate_limits.get(exchange, 10)  # Default: 10 requests per second
            
            # Calculate minimum time between requests
            min_time_between_requests = 1.0 / rate_limit
            
            # Get last request time
            last_request_time = self.exchange_clients[exchange]["last_request"]
            
            # Calculate time since last request
            time_since_last_request = time.time() - last_request_time
            
            # Sleep if needed
            if time_since_last_request < min_time_between_requests:
                sleep_time = min_time_between_requests - time_since_last_request
                await asyncio.sleep(sleep_time)
            
            # Update last request time
            self.exchange_clients[exchange]["last_request"] = time.time()
            
        except Exception as e:
            logger.error(f"Error applying rate limiting for {exchange}: {str(e)}")
    
    async def get_ticker(self, exchange: str, pair: str) -> Dict[str, Any]:
        """
        Get ticker data for a trading pair
        
        Args:
            exchange: Exchange name
            pair: Trading pair
            
        Returns:
            Ticker data
        """
        try:
            # Ensure exchange is supported
            if exchange not in self.exchange_clients:
                logger.warning(f"Exchange {exchange} not supported")
                return {}
            
            # Rate limiting
            await self._apply_rate_limiting(exchange)
            
            # Format pair according to exchange requirements
            formatted_pair = self._format_pair(exchange, pair)
            
            # Call exchange-specific method
            if exchange == "binance":
                return await self._get_binance_ticker(formatted_pair)
            elif exchange == "gate":
                return await self._get_gate_ticker(formatted_pair)
            elif exchange == "bybit":
                return await self._get_bybit_ticker(formatted_pair)
            elif exchange == "hotcoin":
                return await self._get_hotcoin_ticker(formatted_pair)
            elif exchange == "coinw":
                return await self._get_coinw_ticker(formatted_pair)
            elif exchange == "orangex":
                return await self._get_orangex_ticker(formatted_pair)
            else:
                logger.warning(f"No implementation for {exchange} ticker")
                return {}
            
        except Exception as e:
            logger.error(f"Error getting ticker for {pair} on {exchange}: {str(e)}")
            return {}
    
    def _format_pair(self, exchange: str, pair: str) -> str:
        """
        Format trading pair according to exchange requirements
        
        Args:
            exchange: Exchange name
            pair: Trading pair
            
        Returns:
            Formatted pair
        """
        # Default format is BTC/USDT
        base, quote = pair.split("/")
        
        if exchange == "binance":
            return f"{base}{quote}"  # BTCUSDT
        elif exchange == "gate":
            return f"{base}_{quote}"  # BTC_USDT
        elif exchange == "bybit":
            return f"{base}{quote}"  # BTCUSDT
        elif exchange == "hotcoin":
            return f"{base.lower()}_{quote.lower()}"  # btc_usdt
        elif exchange == "coinw":
            return f"{base.lower()}_{quote.lower()}"  # btc_usdt
        elif exchange == "orangex":
            return f"{base}_{quote}"  # BTC_USDT
        else:
            return pair  # Default
