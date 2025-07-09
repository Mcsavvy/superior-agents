import hashlib
import hmac
import json
from typing import Any, Dict, List, Optional
from decimal import Decimal
import time
import requests
from loguru import logger
from functools import partial
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PoolState:
    """
    Data class representing the current state of the PoolMind pool.
    """
    current_nav: float
    available_stx: float
    total_shares: float
    pool_size: float
    recent_deposits: List[Dict]
    recent_withdrawals: List[Dict]
    performance_metrics: Dict[str, Any]
    timestamp: int


@dataclass
class ExchangePrice:
    """
    Data class representing price data from a specific exchange.
    """
    exchange: str
    bid: float
    ask: float
    volume_24h: float
    liquidity_depth: float
    timestamp: int


@dataclass
class ArbitrageOpportunity:
    """
    Data class representing an arbitrage opportunity.
    """
    buy_exchange: str
    sell_exchange: str
    buy_price: float
    sell_price: float
    profit_percentage: float
    required_amount: float
    expected_profit: float
    risk_score: int
    execution_time_estimate: int  # seconds
    timestamp: int


class PoolMindSensor:
    """
    Sensor for monitoring PoolMind pool state and STX arbitrage opportunities.
    
    This sensor collects data from the PoolMind API and various exchanges to
    provide comprehensive information for arbitrage trading decisions.
    """
    
    def __init__(
        self,
        poolmind_api_url: str,
        supported_exchanges: List[str],
        exchange_configs: Dict[str, Dict[str, Any]],
        hmac_secret: str,
    ):
        """
        Initialize the PoolMind sensor.
        
        Args:
            poolmind_api_url (str): Base URL for PoolMind API
            supported_exchanges (List[str]): List of supported exchanges
            exchange_configs (Dict[str, Dict[str, Any]]): Configuration for each exchange
        """
        self.poolmind_api_url = poolmind_api_url.rstrip('/')
        self.supported_exchanges = supported_exchanges
        self.exchange_configs = exchange_configs
        self.hmac_secret = hmac_secret
        self.session = requests.Session()
        self.timeout = 30
        
        # Mock data for development/testing
        self.mock_pool_state = PoolState(
            current_nav=1.05,
            available_stx=50000.0,
            total_shares=47619.0,  # 50000 / 1.05
            pool_size=52500.0,  # 50000 * 1.05
            recent_deposits=[
                {"amount": 1000, "timestamp": int(time.time()) - 3600, "user": "SP1..."},
                {"amount": 5000, "timestamp": int(time.time()) - 7200, "user": "SP2..."}
            ],
            recent_withdrawals=[
                {"amount": 500, "timestamp": int(time.time()) - 1800, "user": "SP3..."}
            ],
            performance_metrics={
                "total_profit": 2500.0,
                "daily_return": 0.02,
                "weekly_return": 0.08,
                "monthly_return": 0.15,
                "sharpe_ratio": 1.2,
                "max_drawdown": 0.03
            },
            timestamp=int(time.time())
        )
        
        # Mock exchange prices for development
        self.mock_exchange_prices = {
            "binance": ExchangePrice("binance", 2.45, 2.46, 1500000, 50000, int(time.time())),
            "okx": ExchangePrice("okx", 2.44, 2.45, 800000, 30000, int(time.time())),
            "gate": ExchangePrice("gate", 2.46, 2.47, 600000, 25000, int(time.time())),
            "hotcoin": ExchangePrice("hotcoin", 2.43, 2.44, 400000, 20000, int(time.time())),
            "bybit": ExchangePrice("bybit", 2.45, 2.46, 700000, 35000, int(time.time())),
            "coinw": ExchangePrice("coinw", 2.47, 2.48, 300000, 15000, int(time.time())),
            "orangex": ExchangePrice("orangex", 2.44, 2.45, 200000, 10000, int(time.time()))
        }

    def _generate_hmac_signature(self, method: str, path: str, body: str = "", timestamp: str = None) -> str:
        """
        Generate HMAC signature for request authentication.
        
        Args:
            method (str): HTTP method (GET, POST, etc.)
            path (str): API endpoint path
            body (str): Request body (for POST requests)
            timestamp (str): Request timestamp (in milliseconds)
            
        Returns:
            str: HMAC signature
        """
        if timestamp is None:
            timestamp = str(int(time.time() * 1000))  # Use milliseconds
        
        # Create message to sign: method + path + timestamp + body
        message = f"{method.upper()}{path}{timestamp}{body}"
        
        # Generate HMAC signature
        signature = hmac.new(
            self.hmac_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def _make_authenticated_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None
    ) -> requests.Response:
        """
        Make an authenticated request to the PoolMind API.
        
        Args:
            method (str): HTTP method
            endpoint (str): API endpoint
            data (Optional[Dict[str, Any]]): Request data
            
        Returns:
            requests.Response: API response
            
        Raises:
            requests.HTTPError: If the request fails
        """
        url = f"{self.poolmind_api_url}{endpoint}"
        timestamp = str(int(time.time() * 1000))  # Use milliseconds
        
        # Prepare request body
        body = json.dumps(data) if data else ""
        
        # Generate HMAC signature
        signature = self._generate_hmac_signature(method, endpoint, body, timestamp)
        
        # Set authentication headers - using the correct format from the API spec
        headers = {
            'x-signature': f'sha256={signature}',
            'x-timestamp': timestamp
        }
        
        # Make request
        response = self.session.request(
            method=method,
            url=url,
            headers=headers,
            data=body if body else None,
            timeout=self.timeout
        )
        
        response.raise_for_status()
        return response
    
    def get_pool_state(self) -> Dict[str, Any]:
        """
        Get current PoolMind pool state.
        
        Returns:
            Dict[str, Any]: Current pool state information
        """
        try:
            # Try to fetch from actual API
            response = self._make_authenticated_request(
                method="GET",
                endpoint="/api/v1/pool/state",
                data=None
            )
            if response.status_code == 200:
                pool_data = response.json()
                return {
                    "current_nav": pool_data.get("nav", 1.0),
                    "available_stx": pool_data.get("available_stx", 0),
                    "total_shares": pool_data.get("total_shares", 0),
                    "pool_size": pool_data.get("pool_size", 0),
                    "recent_activity": pool_data.get("recent_activity", []),
                    "performance": pool_data.get("performance", {}),
                    "timestamp": int(time.time())
                }
        except Exception as e:
            logger.warning(f"Failed to fetch pool state from API: {e}, using mock data")
        
        # Return mock data as fallback
        return {
            "current_nav": self.mock_pool_state.current_nav,
            "available_stx": self.mock_pool_state.available_stx,
            "total_shares": self.mock_pool_state.total_shares,
            "pool_size": self.mock_pool_state.pool_size,
            "recent_activity": {
                "deposits": self.mock_pool_state.recent_deposits,
                "withdrawals": self.mock_pool_state.recent_withdrawals
            },
            "performance": self.mock_pool_state.performance_metrics,
            "timestamp": self.mock_pool_state.timestamp
        }
    
    def get_exchange_prices(self) -> Dict[str, ExchangePrice]:
        """
        Get current STX prices from all supported exchanges.
        
        Returns:
            Dict[str, ExchangePrice]: Price data from each exchange
        """
        exchange_prices = {}
        
        for exchange in self.supported_exchanges:
            try:
                # Try to fetch real price data
                price_data = self._fetch_exchange_price(exchange)
                if price_data:
                    exchange_prices[exchange] = price_data
                else:
                    # Use mock data as fallback
                    exchange_prices[exchange] = self.mock_exchange_prices.get(
                        exchange, 
                        ExchangePrice(exchange, 2.45, 2.46, 100000, 10000, int(time.time()))
                    )
            except Exception as e:
                logger.warning(f"Failed to fetch price from {exchange}: {e}, using mock data")
                exchange_prices[exchange] = self.mock_exchange_prices.get(
                    exchange,
                    ExchangePrice(exchange, 2.45, 2.46, 100000, 10000, int(time.time()))
                )
        
        return exchange_prices
    
    def _fetch_exchange_price(self, exchange: str) -> Optional[ExchangePrice]:
        """
        Fetch price data from a specific exchange.
        
        Args:
            exchange (str): Exchange name
            
        Returns:
            Optional[ExchangePrice]: Price data if successful, None otherwise
        """
        config = self.exchange_configs.get(exchange, {})
        api_endpoint = config.get("api_endpoint")
        
        if not api_endpoint:
            return None
        
        try:
            # This is a placeholder - in real implementation, each exchange
            # would have its own API integration
            if exchange == "binance":
                return self._fetch_binance_price()
            elif exchange == "okx":
                return self._fetch_okx_price()
            elif exchange == "gate":
                return self._fetch_gate_price()
            # Add other exchanges as needed
            
        except Exception as e:
            logger.error(f"Error fetching price from {exchange}: {e}")
            return None
    
    def _fetch_binance_price(self) -> Optional[ExchangePrice]:
        """Fetch STX price from Binance."""
        try:
            # Placeholder for Binance API integration
            # In real implementation, this would call Binance API
            return ExchangePrice("binance", 2.45, 2.46, 1500000, 50000, int(time.time()))
        except Exception:
            return None
    
    def _fetch_okx_price(self) -> Optional[ExchangePrice]:
        """Fetch STX price from OKX."""
        try:
            # Placeholder for OKX API integration
            return ExchangePrice("okx", 2.44, 2.45, 800000, 30000, int(time.time()))
        except Exception:
            return None
    
    def _fetch_gate_price(self) -> Optional[ExchangePrice]:
        """Fetch STX price from Gate.io."""
        try:
            # Placeholder for Gate.io API integration
            return ExchangePrice("gate", 2.46, 2.47, 600000, 25000, int(time.time()))
        except Exception:
            return None
    
    def identify_arbitrage_opportunities(self) -> List[ArbitrageOpportunity]:
        """
        Identify arbitrage opportunities across exchanges.
        
        Returns:
            List[ArbitrageOpportunity]: List of identified opportunities
        """
        exchange_prices = self.get_exchange_prices()
        opportunities = []
        
        # Compare all exchange pairs
        exchanges = list(exchange_prices.keys())
        for i, buy_exchange in enumerate(exchanges):
            for sell_exchange in exchanges[i+1:]:
                buy_price = exchange_prices[buy_exchange]
                sell_price = exchange_prices[sell_exchange]
                
                # Check if buying from buy_exchange and selling to sell_exchange is profitable
                profit_pct = ((sell_price.bid - buy_price.ask) / buy_price.ask) * 100
                
                if profit_pct > 0.1:  # Minimum 0.1% profit to consider
                    # Calculate trade size based on liquidity
                    max_trade_size = min(buy_price.liquidity_depth, sell_price.liquidity_depth) * 0.1
                    
                    opportunity = ArbitrageOpportunity(
                        buy_exchange=buy_exchange.exchange,
                        sell_exchange=sell_exchange.exchange,
                        buy_price=buy_price.ask,
                        sell_price=sell_price.bid,
                        profit_percentage=profit_pct,
                        required_amount=max_trade_size,
                        expected_profit=max_trade_size * (sell_price.bid - buy_price.ask),
                        risk_score=self._calculate_risk_score(buy_price, sell_price),
                        execution_time_estimate=300,  # 5 minutes estimate
                        timestamp=int(time.time())
                    )
                    opportunities.append(opportunity)
                
                # Check reverse direction
                reverse_profit_pct = ((buy_price.bid - sell_price.ask) / sell_price.ask) * 100
                
                if reverse_profit_pct > 0.1:
                    max_trade_size = min(sell_price.liquidity_depth, buy_price.liquidity_depth) * 0.1
                    
                    opportunity = ArbitrageOpportunity(
                        buy_exchange=sell_exchange.exchange,
                        sell_exchange=buy_exchange.exchange,
                        buy_price=sell_price.ask,
                        sell_price=buy_price.bid,
                        profit_percentage=reverse_profit_pct,
                        required_amount=max_trade_size,
                        expected_profit=max_trade_size * (buy_price.bid - sell_price.ask),
                        risk_score=self._calculate_risk_score(sell_price, buy_price),
                        execution_time_estimate=300,
                        timestamp=int(time.time())
                    )
                    opportunities.append(opportunity)
        
        # Sort by profit percentage (descending)
        opportunities.sort(key=lambda x: x.profit_percentage, reverse=True)
        
        return opportunities
    
    def _calculate_risk_score(self, buy_price: ExchangePrice, sell_price: ExchangePrice) -> int:
        """
        Calculate risk score for an arbitrage opportunity.
        
        Args:
            buy_price (ExchangePrice): Buy exchange price data
            sell_price (ExchangePrice): Sell exchange price data
            
        Returns:
            int: Risk score (1-10, where 1 is lowest risk)
        """
        # Base risk score
        risk_score = 3
        
        # Adjust based on liquidity
        min_liquidity = min(buy_price.liquidity_depth, sell_price.liquidity_depth)
        if min_liquidity < 10000:
            risk_score += 2
        elif min_liquidity < 20000:
            risk_score += 1
        
        # Adjust based on volume
        min_volume = min(buy_price.volume_24h, sell_price.volume_24h)
        if min_volume < 100000:
            risk_score += 2
        elif min_volume < 500000:
            risk_score += 1
        
        # Adjust based on spread
        buy_spread = (buy_price.ask - buy_price.bid) / buy_price.bid
        sell_spread = (sell_price.ask - sell_price.bid) / sell_price.bid
        avg_spread = (buy_spread + sell_spread) / 2
        
        if avg_spread > 0.01:  # 1% spread
            risk_score += 2
        elif avg_spread > 0.005:  # 0.5% spread
            risk_score += 1
        
        return min(risk_score, 10)  # Cap at 10
    
    def get_market_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive market metrics for STX.
        
        Returns:
            Dict[str, Any]: Market metrics including volatility, volume, etc.
        """
        exchange_prices = self.get_exchange_prices()
        
        # Calculate aggregate metrics
        all_prices = [price.bid for price in exchange_prices.values()]
        avg_price = sum(all_prices) / len(all_prices)
        
        # Calculate price variance
        price_variance = sum((price - avg_price) ** 2 for price in all_prices) / len(all_prices)
        price_volatility = (price_variance ** 0.5) / avg_price
        
        total_volume = sum(price.volume_24h for price in exchange_prices.values())
        total_liquidity = sum(price.liquidity_depth for price in exchange_prices.values())
        
        return {
            "average_price": avg_price,
            "price_volatility": price_volatility,
            "total_volume_24h": total_volume,
            "total_liquidity": total_liquidity,
            "exchange_count": len(exchange_prices),
            "price_spread": max(all_prices) - min(all_prices),
            "timestamp": int(time.time())
        }
    
    def get_metric_fn(self, metric_name: str = "pool_state"):
        """
        Get a callable function for a specific metric.
        
        Args:
            metric_name (str): Name of the metric to retrieve
            
        Returns:
            callable: Function that returns the requested metric
        """
        metrics = {
            "pool_state": partial(self.get_pool_state),
            "exchange_prices": partial(self.get_exchange_prices),
            "arbitrage_opportunities": partial(self.identify_arbitrage_opportunities),
            "market_metrics": partial(self.get_market_metrics)
        }
        
        if metric_name not in metrics:
            raise ValueError(f"Unsupported metric: {metric_name}")
        
        return metrics[metric_name] 