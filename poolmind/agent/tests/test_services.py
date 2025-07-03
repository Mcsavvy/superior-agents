"""
Tests for the PoolMind Agent service clients
"""
import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any

from poolmind_agent.services.exchange_client import ExchangeClient
from poolmind_agent.services.blockchain_client import BlockchainClient
from poolmind_agent.services.orchestrator_client import OrchestratorClient
from poolmind_agent.services.llm_service import LLMService
from poolmind_agent.services.rag_service import RAGService


@pytest.mark.asyncio
async def test_exchange_client_initialization(test_config):
    """Test exchange client initialization"""
    client = ExchangeClient(test_config)
    assert client is not None
    assert client.config is not None
    assert client.use_mock is True


@pytest.mark.asyncio
async def test_exchange_client_get_ticker(exchange_client):
    """Test exchange client get ticker method"""
    ticker = await exchange_client.get_ticker("binance", "BTC/USDT")
    
    assert ticker is not None
    assert "price" in ticker
    assert "volume" in ticker
    assert "timestamp" in ticker


@pytest.mark.asyncio
async def test_exchange_client_get_order_book(exchange_client):
    """Test exchange client get order book method"""
    order_book = await exchange_client.get_order_book("binance", "BTC/USDT")
    
    assert order_book is not None
    assert "bids" in order_book
    assert "asks" in order_book
    assert isinstance(order_book["bids"], list)
    assert isinstance(order_book["asks"], list)


@pytest.mark.asyncio
async def test_exchange_client_get_all_tickers(exchange_client):
    """Test exchange client get all tickers method"""
    tickers = await exchange_client.get_all_tickers("binance")
    
    assert tickers is not None
    assert isinstance(tickers, dict)
    assert len(tickers) > 0


@pytest.mark.asyncio
async def test_exchange_client_execute_order(exchange_client):
    """Test exchange client execute order method"""
    order_result = await exchange_client.execute_order(
        exchange="binance",
        symbol="BTC/USDT",
        order_type="market",
        side="buy",
        amount=0.1,
        price=None
    )
    
    assert order_result is not None
    assert "order_id" in order_result
    assert "executed_price" in order_result
    assert "timestamp" in order_result


@pytest.mark.asyncio
async def test_blockchain_client_initialization(test_config):
    """Test blockchain client initialization"""
    client = BlockchainClient(test_config)
    assert client is not None
    assert client.config is not None
    assert client.use_mock is True


@pytest.mark.asyncio
async def test_blockchain_client_get_pool_state(blockchain_client):
    """Test blockchain client get pool state method"""
    pool_state = await blockchain_client.get_pool_state()
    
    assert pool_state is not None
    assert "total_value" in pool_state
    assert "participant_count" in pool_state


@pytest.mark.asyncio
async def test_blockchain_client_get_participant_metrics(blockchain_client):
    """Test blockchain client get participant metrics method"""
    metrics = await blockchain_client.get_participant_metrics()
    
    assert metrics is not None
    assert "avg_holding_period" in metrics
    assert "withdrawal_frequency" in metrics


@pytest.mark.asyncio
async def test_blockchain_client_get_gas_price(blockchain_client):
    """Test blockchain client get gas price method"""
    gas_price = await blockchain_client.get_gas_price()
    
    assert gas_price is not None
    assert "fast" in gas_price
    assert "standard" in gas_price
    assert "slow" in gas_price


@pytest.mark.asyncio
async def test_orchestrator_client_initialization(test_config):
    """Test orchestrator client initialization"""
    client = OrchestratorClient(test_config)
    assert client is not None
    assert client.config is not None
    assert client.use_mock is True


@pytest.mark.asyncio
async def test_orchestrator_client_get_pool_status(orchestrator_client):
    """Test orchestrator client get pool status method"""
    status = await orchestrator_client.get_pool_status()
    
    assert status is not None
    assert "pool_id" in status
    assert "status" in status
    assert "total_value" in status


@pytest.mark.asyncio
async def test_orchestrator_client_get_trading_history(orchestrator_client):
    """Test orchestrator client get trading history method"""
    history = await orchestrator_client.get_trading_history(limit=5)
    
    assert history is not None
    assert isinstance(history, list)
    assert len(history) <= 5
    
    if history:
        assert "strategy_id" in history[0]
        assert "timestamp" in history[0]


@pytest.mark.asyncio
async def test_orchestrator_client_submit_strategy(orchestrator_client, sample_strategy):
    """Test orchestrator client submit strategy method"""
    result = await orchestrator_client.submit_strategy(sample_strategy)
    
    assert result is not None
    assert "strategy_id" in result
    assert "status" in result


@pytest.mark.asyncio
async def test_llm_service_initialization(test_config):
    """Test LLM service initialization"""
    service = LLMService(test_config)
    assert service is not None
    assert service.config is not None
    assert service.primary_model is not None


@pytest.mark.asyncio
async def test_llm_service_generate_strategy(llm_service):
    """Test LLM service generate strategy method"""
    prompt = """
    Generate a trading strategy for BTC/USDT with the following parameters:
    - Buy on Binance at $50,000
    - Sell on Coinbase at $50,200
    - Price difference: 0.4%
    - Estimated profit: 0.2%
    """
    
    response = await llm_service.generate_strategy(prompt)
    
    # This might be None in test environment without actual LLM access
    if response is not None:
        assert isinstance(response, str)
        assert len(response) > 0


@pytest.mark.asyncio
async def test_rag_service_initialization(test_config):
    """Test RAG service initialization"""
    service = RAGService(test_config)
    assert service is not None
    assert service.config is not None
    assert service.client is not None


@pytest.mark.asyncio
async def test_rag_service_store_and_retrieve(rag_service):
    """Test RAG service store and retrieve methods"""
    # Store a strategy
    strategy = {
        "opportunity": {
            "pair": "BTC/USDT",
            "buy_exchange": "binance",
            "buy_price": 50000.0,
            "sell_exchange": "coinbase",
            "sell_price": 50200.0,
            "price_diff_pct": 0.4,
            "estimated_profit_pct": 0.2
        },
        "position_size_pct": 2.0,
        "risk_score": 3,
        "execution_priority": 7
    }
    
    success = await rag_service.store_strategy(strategy)
    assert success is True
    
    # Store a market condition
    condition = {
        "exchanges": ["binance", "coinbase"],
        "pairs": ["BTC/USDT", "ETH/USDT"],
        "market_conditions": {
            "volatility": "medium",
            "trend": "bullish"
        }
    }
    
    success = await rag_service.store_market_condition(condition)
    assert success is True
    
    # Retrieve similar market conditions
    similar = await rag_service.retrieve_similar_market_conditions(condition)
    assert similar is not None
    assert isinstance(similar, list)
