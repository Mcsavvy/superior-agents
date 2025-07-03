"""
Pytest configuration for PoolMind Agent tests
"""
import os
import pytest
import asyncio
import sys
import json
from unittest.mock import patch, MagicMock
from typing import Dict, Any, List, Optional

from poolmind_agent.utils.config import AgentConfig
from poolmind_agent.core.agent import PoolMindAgent
from poolmind_agent.services.exchange_client import ExchangeClient
from poolmind_agent.services.blockchain_client import BlockchainClient
from poolmind_agent.services.orchestrator_client import OrchestratorClient
from poolmind_agent.services.llm_service import LLMService
from poolmind_agent.services.rag_service import RAGService

# Import mock services
from tests.mocks import MockLLMService, MockRAGService

# No mock classes needed - we'll use real implementations


@pytest.fixture
def test_config() -> AgentConfig:
    """Fixture for test configuration"""
    # Load config from .env
    config = AgentConfig()
    
    # Ensure we have mock services for testing external APIs
    config.use_mock_exchange = True
    config.use_mock_blockchain = True
    config.use_mock_orchestrator = True
    
    # Enable debug for testing
    config.debug = True
    
    return config


@pytest.fixture
def agent(test_config, event_loop) -> PoolMindAgent:
    """Fixture for PoolMind Agent"""
    # Create agent with real services
    agent = PoolMindAgent(test_config)
    
    # Initialize the agent with real services
    event_loop.run_until_complete(agent.initialize())
    
    yield agent
    
    # Clean up
    event_loop.run_until_complete(agent.stop())


@pytest.fixture
def exchange_client(test_config) -> ExchangeClient:
    """Fixture for Exchange Client"""
    return ExchangeClient(test_config)


@pytest.fixture
def blockchain_client(test_config) -> BlockchainClient:
    """Fixture for Blockchain Client"""
    return BlockchainClient(test_config)


@pytest.fixture
def orchestrator_client(test_config) -> OrchestratorClient:
    """Fixture for Orchestrator Client"""
    return OrchestratorClient(test_config)


@pytest.fixture
def llm_service(test_config) -> LLMService:
    """Fixture for LLM Service"""
    return LLMService(test_config)


@pytest.fixture
def rag_service(test_config) -> RAGService:
    """Fixture for RAG Service"""
    import tempfile
    test_config.rag_data_path = tempfile.mkdtemp()
    service = RAGService(test_config)
    yield service
    # Clean up test data
    import shutil
    shutil.rmtree(test_config.rag_data_path)


@pytest.fixture
def sample_market_data() -> Dict[str, Any]:
    """Fixture for sample market data"""
    return {
        "exchange_data": {
            "binance": {
                "BTC/USDT": {
                    "price": 50000.0,
                    "volume": 100.0,
                    "bid": 49950.0,
                    "ask": 50050.0,
                    "timestamp": "2025-07-03T14:30:00"
                },
                "ETH/USDT": {
                    "price": 3000.0,
                    "volume": 500.0,
                    "bid": 2990.0,
                    "ask": 3010.0,
                    "timestamp": "2025-07-03T14:30:00"
                }
            },
            "coinbase": {
                "BTC/USDT": {
                    "price": 50200.0,
                    "volume": 80.0,
                    "bid": 50150.0,
                    "ask": 50250.0,
                    "timestamp": "2025-07-03T14:30:00"
                },
                "ETH/USDT": {
                    "price": 2980.0,
                    "volume": 450.0,
                    "bid": 2970.0,
                    "ask": 2990.0,
                    "timestamp": "2025-07-03T14:30:00"
                }
            }
        },
        "timestamp": "2025-07-03T14:30:00"
    }


@pytest.fixture
def sample_opportunity() -> Dict[str, Any]:
    """Fixture for sample arbitrage opportunity"""
    return {
        "pair": "BTC/USDT",
        "buy_exchange": "binance",
        "buy_price": 50000.0,
        "sell_exchange": "coinbase",
        "sell_price": 50200.0,
        "price_diff_pct": 0.4,
        "estimated_profit_pct": 0.2,
        "timestamp": "2025-07-03T14:30:00"
    }


@pytest.fixture
def sample_strategy() -> Dict[str, Any]:
    """Fixture for sample trading strategy"""
    return {
        "opportunity": {
            "pair": "BTC/USDT",
            "buy_exchange": "binance",
            "buy_price": 50000.0,
            "sell_exchange": "coinbase",
            "sell_price": 50200.0,
            "price_diff_pct": 0.4,
            "estimated_profit_pct": 0.2,
            "timestamp": "2025-07-03T14:30:00"
        },
        "position_size_pct": 2.0,
        "risk_score": 3,
        "execution_priority": 7,
        "expected_slippage": 0.1,
        "gas_settings": "medium",
        "circuit_breakers": {
            "max_slippage": 0.5,
            "timeout_seconds": 30
        },
        "timestamp": "2025-07-03T14:30:00"
    }


@pytest.fixture
def sample_pool_state() -> Dict[str, Any]:
    """Fixture for sample pool state"""
    return {
        "nav": 1.05,
        "total_value": 10000000.0,
        "participant_count": 50,
        "liquidity_reserve": 1000000.0,
        "withdrawal_forecast": {
            "expected": 200000.0,
            "worst_case": 500000.0
        },
        "participant_metrics": {
            "avg_holding_period": 45,
            "withdrawal_frequency": 0.05,
            "new_participants_rate": 0.02
        },
        "updated_at": "2025-07-03T14:30:00"
    }
