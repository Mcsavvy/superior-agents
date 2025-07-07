"""
Exchange Adapter - Simplified interface for interacting with cryptocurrency exchanges
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

logger = logging.getLogger(__name__)

class ExchangeAdapter:
    """
    Adapter for interacting with a specific cryptocurrency exchange
    """
    
    def __init__(self, exchange_id: str):
        """
        Initialize the Exchange Adapter
        
        Args:
            exchange_id: Exchange identifier
        """
        self.exchange_id = exchange_id
        self.client_config = {}
        self.last_request_time = 0
        self.rate_limit = 10  # Default: 10 requests per second
        
        # Load environment variables
        load_dotenv()
        
        # Initialize client configuration
        self._initialize()
        
        logger.info(f"Exchange Adapter initialized for {exchange_id}")
    
    def _initialize(self) -> None:
        """Initialize the exchange client configuration"""
        try:
            if self.exchange_id == "binance":
                self.client_config = {
                    "api_key": os.getenv("BINANCE_API_KEY", ""),
                    "api_secret": os.getenv("BINANCE_API_SECRET", ""),
                    "base_url": "https://api.binance.com/api/v3"
                }
            elif self.exchange_id == "gate":
                self.client_config = {
                    "api_key": os.getenv("GATE_API_KEY", ""),
                    "api_secret": os.getenv("GATE_API_SECRET", ""),
                    "base_url": "https://api.gateio.ws/api/v4"
                }
            elif self.exchange_id == "bybit":
                self.client_config = {
                    "api_key": os.getenv("BYBIT_API_KEY", ""),
                    "api_secret": os.getenv("BYBIT_API_SECRET", ""),
                    "base_url": "https://api.bybit.com"
                }
            elif self.exchange_id == "hotcoin":
                self.client_config = {
                    "access_key": os.getenv("HOTCOIN_ACCESS_KEY", ""),
                    "secret_key": os.getenv("HOTCOIN_SECRET_KEY", ""),
                    "base_url": "https://api.hotcoin.com"
                }
            elif self.exchange_id == "coinw":
                self.client_config = {
                    "api_key": os.getenv("COINW_API_KEY", ""),
                    "secret_key": os.getenv("COINW_SECRET_KEY", ""),
                    "base_url": "https://api.coinw.com"
                }
            elif self.exchange_id == "orangex":
                self.client_config = {
                    "api_key": os.getenv("ORANGEX_API_KEY", ""),
                    "secret_key": os.getenv("ORANGEX_SECRET_KEY", ""),
                    "base_url": "https://api.orangex.com"
                }
            else:
                logger.warning(f"Unsupported exchange: {self.exchange_id}")
        
        except Exception as e:
            logger.error(f"Error initializing {self.exchange_id} adapter: {str(e)}")
    
    async def apply_rate_limiting(self) -> None:
        """Apply rate limiting for API calls"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        min_time_between_requests = 1.0 / self.rate_limit
        
        if time_since_last_request < min_time_between_requests:
            await asyncio.sleep(min_time_between_requests - time_since_last_request)
        
        self.last_request_time = time.time()
    
    def format_pair(self, pair: str) -> str:
        """
        Format trading pair according to exchange requirements
        
        Args:
            pair: Trading pair (e.g., 'BTC/USDT')
            
        Returns:
            Formatted pair
        """
        if '/' not in pair:
            return pair  # Already formatted
            
        base, quote = pair.split('/')
        
        if self.exchange_id == "binance":
            return f"{base}{quote}"  # BTCUSDT
        elif self.exchange_id == "gate":
            return f"{base}_{quote}"  # BTC_USDT
        elif self.exchange_id == "bybit":
            return f"{base}{quote}"  # BTCUSDT
        elif self.exchange_id == "hotcoin":
            return f"{base.lower()}_{quote.lower()}"  # btc_usdt
        elif self.exchange_id == "coinw":
            return f"{base.lower()}_{quote.lower()}"  # btc_usdt
        elif self.exchange_id == "orangex":
            return f"{base}_{quote}"  # BTC_USDT
        else:
            return pair
    
    async def get_ticker(self, pair: str) -> Dict[str, Any]:
        """
        Get ticker data for a trading pair
        
        Args:
            pair: Trading pair (e.g., 'BTC/USDT')
            
        Returns:
            Ticker data
        """
        try:
            await self.apply_rate_limiting()
            
            formatted_pair = self.format_pair(pair)
            
            if self.exchange_id == "binance":
                return await self._get_binance_ticker(formatted_pair)
            elif self.exchange_id == "gate":
                return await self._get_gate_ticker(formatted_pair)
            elif self.exchange_id == "bybit":
                return await self._get_bybit_ticker(formatted_pair)
            elif self.exchange_id == "hotcoin":
                return await self._get_hotcoin_ticker(formatted_pair)
            elif self.exchange_id == "coinw":
                return await self._get_coinw_ticker(formatted_pair)
            elif self.exchange_id == "orangex":
                return await self._get_orangex_ticker(formatted_pair)
            else:
                logger.warning(f"No implementation for {self.exchange_id} ticker")
                return {}
        
        except Exception as e:
            logger.error(f"Error getting ticker for {pair} on {self.exchange_id}: {str(e)}")
            return {}
    
    async def get_all_tickers(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all tickers for the exchange
        
        Returns:
            Dictionary of tickers keyed by symbol
        """
        try:
            await self.apply_rate_limiting()
            
            if self.exchange_id == "binance":
                return await self._get_binance_all_tickers()
            elif self.exchange_id == "gate":
                return await self._get_gate_all_tickers()
            elif self.exchange_id == "bybit":
                return await self._get_bybit_all_tickers()
            elif self.exchange_id == "hotcoin":
                return await self._get_hotcoin_all_tickers()
            elif self.exchange_id == "coinw":
                return await self._get_coinw_all_tickers()
            elif self.exchange_id == "orangex":
                return await self._get_orangex_all_tickers()
            else:
                logger.warning(f"No implementation for {self.exchange_id} all tickers")
                return {}
        
        except Exception as e:
            logger.error(f"Error getting all tickers for {self.exchange_id}: {str(e)}")
            return {}
    
    async def execute_order(self, pair: str, side: str, amount: float, price: Optional[float] = None, order_type: str = "market") -> Dict[str, Any]:
        """
        Execute an order on the exchange
        
        Args:
            pair: Trading pair
            side: Order side (buy/sell)
            amount: Order amount
            price: Order price (None for market orders)
            order_type: Order type (market/limit)
            
        Returns:
            Order result
        """
        try:
            await self.apply_rate_limiting()
            
            formatted_pair = self.format_pair(pair)
            
            if self.exchange_id == "binance":
                return await self._execute_binance_order(formatted_pair, side, amount, price, order_type)
            elif self.exchange_id == "gate":
                return await self._execute_gate_order(formatted_pair, side, amount, price, order_type)
            elif self.exchange_id == "bybit":
                return await self._execute_bybit_order(formatted_pair, side, amount, price, order_type)
            elif self.exchange_id == "hotcoin":
                return await self._execute_hotcoin_order(formatted_pair, side, amount, price, order_type)
            elif self.exchange_id == "coinw":
                return await self._execute_coinw_order(formatted_pair, side, amount, price, order_type)
            elif self.exchange_id == "orangex":
                return await self._execute_orangex_order(formatted_pair, side, amount, price, order_type)
            else:
                logger.warning(f"No implementation for {self.exchange_id} order execution")
                return {"success": False, "error": f"No implementation for {self.exchange_id} order execution"}
        
        except Exception as e:
            logger.error(f"Error executing order for {pair} on {self.exchange_id}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_balance(self) -> Dict[str, float]:
        """
        Get account balance
        
        Returns:
            Dictionary of balances keyed by asset
        """
        try:
            await self.apply_rate_limiting()
            
            if self.exchange_id == "binance":
                return await self._get_binance_balance()
            elif self.exchange_id == "gate":
                return await self._get_gate_balance()
            elif self.exchange_id == "bybit":
                return await self._get_bybit_balance()
            elif self.exchange_id == "hotcoin":
                return await self._get_hotcoin_balance()
            elif self.exchange_id == "coinw":
                return await self._get_coinw_balance()
            elif self.exchange_id == "orangex":
                return await self._get_orangex_balance()
            else:
                logger.warning(f"No implementation for {self.exchange_id} balance")
                return {}
        
        except Exception as e:
            logger.error(f"Error getting balance for {self.exchange_id}: {str(e)}")
            return {}
    
    # Binance API implementations
    async def _get_binance_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get ticker data from Binance"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.client_config['base_url']}/ticker/price",
                    params={"symbol": symbol}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "exchange": "binance",
                        "pair": symbol,
                        "price": float(data["price"]),
                        "timestamp": datetime.now().timestamp()
                    }
                else:
                    logger.error(f"Error getting Binance ticker: {response.status_code} {response.text}")
                    return {}
        
        except Exception as e:
            logger.error(f"Error in Binance ticker request: {str(e)}")
            return {}
    
    async def _get_binance_all_tickers(self) -> Dict[str, Dict[str, Any]]:
        """Get all tickers from Binance"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.client_config['base_url']}/ticker/price")
                
                if response.status_code == 200:
                    data = response.json()
                    tickers = {}
                    
                    for item in data:
                        symbol = item["symbol"]
                        tickers[symbol] = {
                            "exchange": "binance",
                            "pair": symbol,
                            "price": float(item["price"]),
                            "timestamp": datetime.now().timestamp()
                        }
                    
                    return tickers
                else:
                    logger.error(f"Error getting Binance tickers: {response.status_code} {response.text}")
                    return {}
        
        except Exception as e:
            logger.error(f"Error in Binance tickers request: {str(e)}")
            return {}
    
    # Gate.io API implementations
    async def _get_gate_ticker(self, currency_pair: str) -> Dict[str, Any]:
        """Get ticker data from Gate.io"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.client_config['base_url']}/spot/tickers",
                    params={"currency_pair": currency_pair}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data:
                        return {
                            "exchange": "gate",
                            "pair": currency_pair,
                            "price": float(data[0]["last"]),
                            "timestamp": datetime.now().timestamp()
                        }
                    return {}
                else:
                    logger.error(f"Error getting Gate.io ticker: {response.status_code} {response.text}")
                    return {}
        
        except Exception as e:
            logger.error(f"Error in Gate.io ticker request: {str(e)}")
            return {}
    
    async def _get_gate_all_tickers(self) -> Dict[str, Dict[str, Any]]:
        """Get all tickers from Gate.io"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.client_config['base_url']}/spot/tickers")
                
                if response.status_code == 200:
                    data = response.json()
                    tickers = {}
                    
                    for item in data:
                        symbol = item["currency_pair"]
                        tickers[symbol] = {
                            "exchange": "gate",
                            "pair": symbol,
                            "price": float(item["last"]),
                            "timestamp": datetime.now().timestamp()
                        }
                    
                    return tickers
                else:
                    logger.error(f"Error getting Gate.io tickers: {response.status_code} {response.text}")
                    return {}
        
        except Exception as e:
            logger.error(f"Error in Gate.io tickers request: {str(e)}")
            return {}
    
    # Bybit API implementations
    async def _get_bybit_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get ticker data from Bybit"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.client_config['base_url']}/v5/market/tickers",
                    params={"category": "spot", "symbol": symbol}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("result") and data["result"].get("list"):
                        ticker = data["result"]["list"][0]
                        return {
                            "exchange": "bybit",
                            "pair": symbol,
                            "price": float(ticker["lastPrice"]),
                            "timestamp": datetime.now().timestamp()
                        }
                    return {}
                else:
                    logger.error(f"Error getting Bybit ticker: {response.status_code} {response.text}")
                    return {}
        
        except Exception as e:
            logger.error(f"Error in Bybit ticker request: {str(e)}")
            return {}
    
    async def _get_bybit_all_tickers(self) -> Dict[str, Dict[str, Any]]:
        """Get all tickers from Bybit"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.client_config['base_url']}/v5/market/tickers",
                    params={"category": "spot"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    tickers = {}
                    
                    if data.get("result") and data["result"].get("list"):
                        for item in data["result"]["list"]:
                            symbol = item["symbol"]
                            tickers[symbol] = {
                                "exchange": "bybit",
                                "pair": symbol,
                                "price": float(item["lastPrice"]),
                                "timestamp": datetime.now().timestamp()
                            }
                    
                    return tickers
                else:
                    logger.error(f"Error getting Bybit tickers: {response.status_code} {response.text}")
                    return {}
        
        except Exception as e:
            logger.error(f"Error in Bybit tickers request: {str(e)}")
            return {}
