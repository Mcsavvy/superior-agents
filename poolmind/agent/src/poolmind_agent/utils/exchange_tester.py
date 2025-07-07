"""
Exchange API Tester

This script tests the connection to various exchanges using the API credentials from the .env file.
"""
import os
import asyncio
import logging
from typing import Dict, List, Any
import httpx
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

class ExchangeAPITester:
    """Tests connections to various cryptocurrency exchanges"""
    
    def __init__(self):
        """Initialize the exchange tester"""
        # Load environment variables
        load_dotenv()
        
        # Initialize exchange clients
        self.exchange_clients = {}
        self._initialize_clients()
        
        logger.info("Exchange API Tester initialized")
    
    def _initialize_clients(self) -> None:
        """Initialize exchange API clients"""
        # Hotcoin
        if os.getenv("HOTCOIN_ACCESS_KEY") and os.getenv("HOTCOIN_SECRET_KEY"):
            self.exchange_clients["hotcoin"] = {
                "name": "Hotcoin",
                "access_key": os.getenv("HOTCOIN_ACCESS_KEY"),
                "secret_key": os.getenv("HOTCOIN_SECRET_KEY"),
                "base_url": "https://api.hotcoin.com"
            }
        
        # Gate.io
        if os.getenv("GATE_API_KEY") and os.getenv("GATE_API_SECRET"):
            self.exchange_clients["gate"] = {
                "name": "Gate.io",
                "api_key": os.getenv("GATE_API_KEY"),
                "api_secret": os.getenv("GATE_API_SECRET"),
                "base_url": "https://api.gateio.ws/api/v4"
            }
        
        # Binance
        if os.getenv("BINANCE_API_KEY") and os.getenv("BINANCE_API_SECRET"):
            self.exchange_clients["binance"] = {
                "name": "Binance",
                "api_key": os.getenv("BINANCE_API_KEY"),
                "api_secret": os.getenv("BINANCE_API_SECRET"),
                "base_url": "https://api.binance.com/api/v3"
            }
        
        # Coin W
        if os.getenv("COINW_API_KEY") and os.getenv("COINW_SECRET_KEY"):
            self.exchange_clients["coinw"] = {
                "name": "Coin W",
                "api_key": os.getenv("COINW_API_KEY"),
                "secret_key": os.getenv("COINW_SECRET_KEY"),
                "base_url": "https://api.coinw.com"
            }
        
        # Bybit
        if os.getenv("BYBIT_API_KEY") and os.getenv("BYBIT_API_SECRET"):
            self.exchange_clients["bybit"] = {
                "name": "Bybit",
                "api_key": os.getenv("BYBIT_API_KEY"),
                "api_secret": os.getenv("BYBIT_API_SECRET"),
                "base_url": "https://api.bybit.com"
            }
        
        # OrangeX
        if os.getenv("ORANGEX_API_KEY") and os.getenv("ORANGEX_SECRET_KEY"):
            self.exchange_clients["orangex"] = {
                "name": "OrangeX",
                "api_key": os.getenv("ORANGEX_API_KEY"),
                "secret_key": os.getenv("ORANGEX_SECRET_KEY"),
                "base_url": "https://api.orangex.com"
            }
        
        logger.info(f"Initialized {len(self.exchange_clients)} exchange clients")
    
    async def test_all_exchanges(self) -> Dict[str, Dict[str, Any]]:
        """
        Test connection to all configured exchanges
        
        Returns:
            Dictionary of test results
        """
        results = {}
        
        for exchange_id, client in self.exchange_clients.items():
            results[exchange_id] = await self.test_exchange(exchange_id)
        
        return results
    
    async def test_exchange(self, exchange_id: str) -> Dict[str, Any]:
        """
        Test connection to a specific exchange
        
        Args:
            exchange_id: Exchange ID
            
        Returns:
            Test result
        """
        if exchange_id not in self.exchange_clients:
            return {"success": False, "error": f"Exchange {exchange_id} not configured"}
        
        client = self.exchange_clients[exchange_id]
        
        try:
            # Different endpoints for different exchanges
            if exchange_id == "binance":
                return await self._test_binance(client)
            elif exchange_id == "gate":
                return await self._test_gate(client)
            elif exchange_id == "bybit":
                return await self._test_bybit(client)
            elif exchange_id == "hotcoin":
                return await self._test_hotcoin(client)
            elif exchange_id == "coinw":
                return await self._test_coinw(client)
            elif exchange_id == "orangex":
                return await self._test_orangex(client)
            else:
                return {"success": False, "error": f"No test implementation for {exchange_id}"}
        
        except Exception as e:
            logger.error(f"Error testing {exchange_id}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _test_binance(self, client: Dict[str, str]) -> Dict[str, Any]:
        """Test Binance API"""
        try:
            # Test public endpoint first
            async with httpx.AsyncClient() as http_client:
                # Test ping endpoint
                ping_response = await http_client.get(f"{client['base_url']}/ping")
                
                if ping_response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"Ping failed: {ping_response.status_code} {ping_response.text}"
                    }
                
                # Test ticker endpoint
                ticker_response = await http_client.get(f"{client['base_url']}/ticker/price", params={"symbol": "BTCUSDT"})
                
                if ticker_response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"Ticker failed: {ticker_response.status_code} {ticker_response.text}"
                    }
                
                # Get ticker data
                ticker_data = ticker_response.json()
                
                return {
                    "success": True,
                    "message": "Binance API connection successful",
                    "ticker": ticker_data
                }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _test_gate(self, client: Dict[str, str]) -> Dict[str, Any]:
        """Test Gate.io API"""
        try:
            # Test public endpoint
            async with httpx.AsyncClient() as http_client:
                # Test ticker endpoint
                ticker_response = await http_client.get(f"{client['base_url']}/spot/tickers", params={"currency_pair": "BTC_USDT"})
                
                if ticker_response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"Ticker failed: {ticker_response.status_code} {ticker_response.text}"
                    }
                
                # Get ticker data
                ticker_data = ticker_response.json()
                
                return {
                    "success": True,
                    "message": "Gate.io API connection successful",
                    "ticker": ticker_data
                }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _test_bybit(self, client: Dict[str, str]) -> Dict[str, Any]:
        """Test Bybit API"""
        try:
            # Test public endpoint
            async with httpx.AsyncClient() as http_client:
                # Test ticker endpoint
                ticker_response = await http_client.get(f"{client['base_url']}/v5/market/tickers", params={"category": "spot", "symbol": "BTCUSDT"})
                
                if ticker_response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"Ticker failed: {ticker_response.status_code} {ticker_response.text}"
                    }
                
                # Get ticker data
                ticker_data = ticker_response.json()
                
                return {
                    "success": True,
                    "message": "Bybit API connection successful",
                    "ticker": ticker_data
                }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _test_hotcoin(self, client: Dict[str, str]) -> Dict[str, Any]:
        """Test Hotcoin API"""
        try:
            # Test public endpoint
            async with httpx.AsyncClient() as http_client:
                # Test ticker endpoint (using a common endpoint pattern, adjust if needed)
                ticker_response = await http_client.get(f"{client['base_url']}/v1/market/ticker", params={"symbol": "btc_usdt"})
                
                if ticker_response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"Ticker failed: {ticker_response.status_code} {ticker_response.text}"
                    }
                
                # Get ticker data
                ticker_data = ticker_response.json()
                
                return {
                    "success": True,
                    "message": "Hotcoin API connection successful",
                    "ticker": ticker_data
                }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _test_coinw(self, client: Dict[str, str]) -> Dict[str, Any]:
        """Test Coin W API"""
        try:
            # Test public endpoint
            async with httpx.AsyncClient() as http_client:
                # Test ticker endpoint (using a common endpoint pattern, adjust if needed)
                ticker_response = await http_client.get(f"{client['base_url']}/api/v1/ticker", params={"symbol": "btc_usdt"})
                
                if ticker_response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"Ticker failed: {ticker_response.status_code} {ticker_response.text}"
                    }
                
                # Get ticker data
                ticker_data = ticker_response.json()
                
                return {
                    "success": True,
                    "message": "Coin W API connection successful",
                    "ticker": ticker_data
                }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _test_orangex(self, client: Dict[str, str]) -> Dict[str, Any]:
        """Test OrangeX API"""
        try:
            # Test public endpoint
            async with httpx.AsyncClient() as http_client:
                # Test ticker endpoint (using a common endpoint pattern, adjust if needed)
                ticker_response = await http_client.get(f"{client['base_url']}/api/v1/market/ticker", params={"symbol": "BTC_USDT"})
                
                if ticker_response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"Ticker failed: {ticker_response.status_code} {ticker_response.text}"
                    }
                
                # Get ticker data
                ticker_data = ticker_response.json()
                
                return {
                    "success": True,
                    "message": "OrangeX API connection successful",
                    "ticker": ticker_data
                }
        
        except Exception as e:
            return {"success": False, "error": str(e)}

async def main():
    """Main entry point"""
    tester = ExchangeAPITester()
    
    # Test all exchanges
    results = await tester.test_all_exchanges()
    
    # Print results
    print("\n=== Exchange API Test Results ===")
    for exchange_id, result in results.items():
        success = "✅" if result.get("success", False) else "❌"
        print(f"{success} {exchange_id.upper()}: {result.get('message', result.get('error', 'Unknown error'))}")
        
        # Print ticker data if available
        if "ticker" in result:
            print(f"  Ticker: {result['ticker']}")
        
        print()

if __name__ == "__main__":
    asyncio.run(main())
