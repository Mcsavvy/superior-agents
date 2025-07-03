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
                    "exchange": "coinbase",
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
