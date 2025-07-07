"""
Mock implementations for testing
"""
from typing import Dict, Any, Optional, List
import asyncio
from datetime import datetime

class MockLLMService:
    """Mock LLM Service for testing"""
    
    def __init__(self, config):
        self.config = config
        self.primary_model = "mock-llama3-70b-8192"
        self.fallback_model = "mock-mixtral-8x7b-32768"
        self.strategy_model = "mock-llama3-70b-8192"
    
    async def generate_strategy(self, prompt: str) -> str:
        """Mock strategy generation"""
        return """
        {
            "position_size_pct": 2.0,
            "risk_score": 3,
            "execution_priority": 7,
            "rationale": "This is a mock strategy generated for testing"
        }
        """
    
    async def assess_risk(self, prompt: str) -> str:
        """Mock risk assessment"""
        return """
        {
            "overall_risk": 4.5,
            "liquidity_risk": 3.0,
            "market_risk": 5.0,
            "counterparty_risk": 2.0,
            "proceed": true,
            "rationale": "This is a mock risk assessment generated for testing"
        }
        """
    
    async def optimize_execution(self, prompt: str) -> str:
        """Mock execution optimization"""
        return """
        {
            "execution_plan": {
                "buy_order": {
                    "exchange": "binance",
                    "order_type": "limit",
                    "price": 50050.0,
                    "size": 0.1
                },
                "sell_order": {
                    "exchange": "gate",
                    "order_type": "limit",
                    "price": 50150.0,
                    "size": 0.1
                },
                "estimated_profit": 10.0,
                "estimated_fees": 2.0
            }
        }
        """
    
    async def generate_insights(self, prompt: str) -> str:
        """Mock insights generation"""
        return """
        {
            "insights": [
                "The strategy performed well with minimal slippage",
                "Consider increasing position size for similar opportunities",
                "Market liquidity was sufficient for execution"
            ],
            "recommendations": [
                "Continue monitoring this trading pair",
                "Adjust risk parameters to allow for larger positions"
            ]
        }
        """
    
    async def parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response"""
        # In a mock, we can just return a predefined dictionary
        return {
            "success": True,
            "data": {
                "result": "This is a mock parsed JSON response"
            }
        }


class MockRAGService:
    """Mock RAG Service for testing"""
    
    def __init__(self, config):
        self.config = config
        self.client = "mock-chroma-client"
        self.collections = {
            "strategies": [],
            "market_conditions": [],
            "trade_outcomes": []
        }
        
    async def close(self):
        """Mock close method"""
        return True
    
    async def initialize_collections(self) -> bool:
        """Initialize collections"""
        return True
    
    async def store_strategy(self, strategy: Dict[str, Any]) -> bool:
        """Store strategy"""
        self.collections["strategies"].append(strategy)
        return True
    
    async def store_market_condition(self, condition: Dict[str, Any]) -> bool:
        """Store market condition"""
        self.collections["market_conditions"].append(condition)
        return True
    
    async def store_trade_outcome(self, outcome: Dict[str, Any]) -> bool:
        """Store trade outcome"""
        self.collections["trade_outcomes"].append(outcome)
        return True
    
    async def retrieve_similar_strategies(self, strategy: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieve similar strategies"""
        return self.collections["strategies"][:min(limit, len(self.collections["strategies"]))]
    
    async def retrieve_similar_market_conditions(self, condition: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieve similar market conditions"""
        return self.collections["market_conditions"][:min(limit, len(self.collections["market_conditions"]))]
    
    async def retrieve_similar_trade_outcomes(self, outcome: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieve similar trade outcomes"""
        return self.collections["trade_outcomes"][:min(limit, len(self.collections["trade_outcomes"]))]


class MockExchangeAdapter:
    """Mock Exchange Adapter for testing"""
    
    def __init__(self, exchange_id: str, api_key: str, api_secret: str):
        self.exchange_id = exchange_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.initialized = True
        
    async def initialize(self) -> bool:
        """Initialize the exchange adapter"""
        self.initialized = True
        return True
        
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get ticker data for a symbol"""
        return {
            "price": 50000.0 if symbol == "BTC/USDT" else 3000.0,
            "volume": 100.0 if symbol == "BTC/USDT" else 500.0,
            "bid": 49950.0 if symbol == "BTC/USDT" else 2990.0,
            "ask": 50050.0 if symbol == "BTC/USDT" else 3010.0,
            "timestamp": datetime.now().timestamp()
        }
        
    async def get_order_book(self, symbol: str, limit: int = 20) -> Dict[str, Any]:
        """Get order book for a symbol"""
        base_price = 50000.0 if symbol == "BTC/USDT" else 3000.0
        
        bids = []
        asks = []
        
        for i in range(limit):
            bids.append([base_price - (i * 10), 1.0 / (i + 1)])
            asks.append([base_price + (i * 10), 1.0 / (i + 1)])
            
        return {
            "bids": bids,
            "asks": asks,
            "timestamp": datetime.now().timestamp()
        }
        
    async def get_balance(self, currency: str) -> Dict[str, Any]:
        """Get balance for a currency"""
        return {
            "free": 10.0 if currency == "BTC" else 50000.0,
            "used": 1.0 if currency == "BTC" else 10000.0,
            "total": 11.0 if currency == "BTC" else 60000.0
        }
        
    async def execute_order(self, symbol: str, order_type: str, side: str, amount: float, price: Optional[float] = None) -> Dict[str, Any]:
        """Execute an order"""
        return {
            "order_id": f"mock-{self.exchange_id}-{side}-{datetime.now().timestamp()}",
            "symbol": symbol,
            "type": order_type,
            "side": side,
            "amount": amount,
            "executed_price": price if price else 50000.0 if symbol == "BTC/USDT" else 3000.0,
            "status": "closed",
            "timestamp": datetime.now().timestamp(),
            "success": True
        }
        
    async def get_markets(self) -> Dict[str, Any]:
        """Get available markets"""
        return {
            "BTC/USDT": {
                "symbol": "BTC/USDT",
                "base": "BTC",
                "quote": "USDT",
                "active": True,
                "precision": {
                    "price": 2,
                    "amount": 6
                },
                "limits": {
                    "amount": {
                        "min": 0.000001,
                        "max": 1000.0
                    },
                    "price": {
                        "min": 0.01,
                        "max": 1000000.0
                    }
                }
            },
            "ETH/USDT": {
                "symbol": "ETH/USDT",
                "base": "ETH",
                "quote": "USDT",
                "active": True,
                "precision": {
                    "price": 2,
                    "amount": 5
                },
                "limits": {
                    "amount": {
                        "min": 0.00001,
                        "max": 10000.0
                    },
                    "price": {
                        "min": 0.01,
                        "max": 100000.0
                    }
                }
            }
        }
