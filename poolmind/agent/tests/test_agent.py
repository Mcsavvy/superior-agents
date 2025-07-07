"""
Tests for the PoolMind Agent core functionality
"""
import pytest
import asyncio
import os
from datetime import datetime
from typing import Dict, Any
from unittest.mock import patch, MagicMock

from poolmind_agent.core.agent import PoolMindAgent, AgentState


@pytest.mark.asyncio
async def test_agent_initialization(test_config):
    """Test agent initialization"""
    # Create an agent
    agent = PoolMindAgent(test_config)
    assert agent is not None
    assert agent.config is not None
    assert agent.is_initialized is False
    
    # Initialize the agent
    await agent.initialize()
    
    # Verify initialization
    assert agent.is_initialized is True
    assert agent.exchange_client is not None
    assert agent.blockchain_client is not None
    assert agent.orchestrator_client is not None
    assert agent.llm_service is not None
    assert agent.rag_service is not None
    assert agent.pool_context is not None
    assert agent.strategy_generator is not None
    assert agent.risk_assessor is not None
    assert agent.execution_optimizer is not None
    assert agent.reflection_engine is not None
    assert agent.graph is not None
    
    # Clean up
    await agent.stop()


@pytest.mark.asyncio
async def test_agent_lifecycle(test_config):
    """Test agent lifecycle (start/stop)"""
    # Create an agent
    agent = PoolMindAgent(test_config)
    
    # Initialize agent
    await agent.initialize()
    assert agent.is_initialized is True
    start_time = agent.start_time
    
    # Test stop
    await agent.stop()
    assert agent.is_initialized is False
    
    # Re-initialize agent
    await agent.initialize()
    assert agent.is_initialized is True
    assert agent.start_time > start_time
    
    # Test stop again
    await agent.stop()
    assert agent.is_initialized is False


@pytest.mark.asyncio
async def test_agent_observe_node(agent):
    """Test agent observe node"""
    # Create initial state
    state = AgentState(
        pool_state={},
        market_data={},
        opportunities=[],
        decisions=[],
        execution_results=[],
        errors=[],
        timestamp=datetime.now().isoformat()
    )
    
    # Mock the orchestrator_client.get_pool_status method
    agent.orchestrator_client.get_pool_status = MagicMock(
        return_value=asyncio.Future()
    )
    agent.orchestrator_client.get_pool_status.return_value.set_result({
        "pool_id": "test-pool",
        "total_value": 1000000,
        "liquidity_reserve": 150000,
        "status": "active"
    })
    
    # Mock the _fetch_market_data method
    agent._fetch_market_data = MagicMock(
        return_value=asyncio.Future()
    )
    agent._fetch_market_data.return_value.set_result({
        "binance": {
            "tickers": {
                "BTC/USDT": {"price": 50000, "volume": 100},
                "ETH/USDT": {"price": 3000, "volume": 200}
            }
        },
        "gate": {
            "tickers": {
                "BTC/USDT": {"price": 50100, "volume": 90},
                "ETH/USDT": {"price": 3010, "volume": 180}
            }
        }
    })
    
    # Call observe node
    result_state = await agent._observe_node(state)
    
    # Verify result
    assert result_state is not None
    assert "pool_state" in result_state
    assert "market_data" in result_state
    assert result_state["pool_state"]["pool_id"] == "test-pool"
    assert "binance" in result_state["market_data"]
    assert "gate" in result_state["market_data"]


@pytest.mark.asyncio
async def test_agent_detect_opportunities_node(agent):
    """Test agent detect opportunities node"""
    # Create initial state with market data
    state = AgentState(
        pool_state={"pool_id": "test-pool", "total_value": 1000000},
        market_data={
            "binance": {
                "tickers": {
                    "BTC/USDT": {"price": 50000, "volume": 100},
                    "ETH/USDT": {"price": 3000, "volume": 200}
                }
            },
            "gate": {
                "tickers": {
                    "BTC/USDT": {"price": 50100, "volume": 90},
                    "ETH/USDT": {"price": 3010, "volume": 180}
                }
            }
        },
        opportunities=[],
        decisions=[],
        execution_results=[],
        errors=[],
        timestamp=datetime.now().isoformat()
    )
    
    # Mock the strategy_generator.detect_opportunities method
    agent.strategy_generator.detect_opportunities = MagicMock(
        return_value=asyncio.Future()
    )
    agent.strategy_generator.detect_opportunities.return_value.set_result([
        {
            "pair": "BTC/USDT",
            "buy_exchange": "binance",
            "sell_exchange": "gate",
            "buy_price": 50000,
            "sell_price": 50100,
            "price_diff_pct": 0.2,
            "estimated_profit_pct": 0.1
        }
    ])
    
    # Mock the orchestrator_client.report_arbitrage_opportunity method
    agent.orchestrator_client.report_arbitrage_opportunity = MagicMock(
        return_value=asyncio.Future()
    )
    agent.orchestrator_client.report_arbitrage_opportunity.return_value.set_result({
        "success": True
    })
    
    # Call detect opportunities node
    result_state = await agent._detect_opportunities_node(state)
    
    # Verify result
    assert result_state is not None
    assert "opportunities" in result_state
    assert len(result_state["opportunities"]) == 1
    assert result_state["opportunities"][0]["pair"] == "BTC/USDT"
    assert result_state["opportunities"][0]["buy_exchange"] == "binance"
    assert result_state["opportunities"][0]["sell_exchange"] == "gate"


@pytest.mark.asyncio
async def test_agent_generate_strategy_node(agent):
    """Test agent generate strategy node"""
    # Create initial state with opportunities
    state = AgentState(
        pool_state={"pool_id": "test-pool", "total_value": 1000000},
        market_data={
            "binance": {"tickers": {"BTC/USDT": {"price": 50000}}},
            "gate": {"tickers": {"BTC/USDT": {"price": 50100}}}
        },
        opportunities=[
            {
                "pair": "BTC/USDT",
                "buy_exchange": "binance",
                "sell_exchange": "gate",
                "buy_price": 50000,
                "sell_price": 50100,
                "price_diff_pct": 0.2,
                "estimated_profit_pct": 0.1
            }
        ],
        decisions=[],
        execution_results=[],
        errors=[],
        timestamp=datetime.now().isoformat()
    )
    
    # Mock the strategy_generator.generate_strategy method
    agent.strategy_generator.generate_strategy = MagicMock(
        return_value=asyncio.Future()
    )
    agent.strategy_generator.generate_strategy.return_value.set_result([
        {
            "opportunity": state["opportunities"][0],
            "position_size_pct": 2.0,
            "risk_score": 3,
            "execution_priority": 7
        }
    ])
    
    # Call generate strategy node
    result_state = await agent._generate_strategy_node(state)
    
    # Verify result
    assert result_state is not None
    assert "decisions" in result_state
    assert len(result_state["decisions"]) == 1
    assert "opportunity" in result_state["decisions"][0]
    assert "position_size_pct" in result_state["decisions"][0]
    assert "risk_score" in result_state["decisions"][0]
    assert "execution_priority" in result_state["decisions"][0]


@pytest.mark.asyncio
async def test_agent_assess_risk_node(agent):
    """Test agent assess risk node"""
    # Create initial state with decisions
    state = AgentState(
        pool_state={"pool_id": "test-pool", "total_value": 1000000},
        market_data={},
        opportunities=[],
        decisions=[
            {
                "opportunity": {
                    "pair": "BTC/USDT",
                    "buy_exchange": "binance",
                    "sell_exchange": "gate",
                    "buy_price": 50000,
                    "sell_price": 50100,
                    "price_diff_pct": 0.2,
                    "estimated_profit_pct": 0.1
                },
                "position_size_pct": 2.0,
                "risk_score": 3,
                "execution_priority": 7
            }
        ],
        execution_results=[],
        errors=[],
        timestamp=datetime.now().isoformat()
    )
    
    # Mock the risk_assessor.assess_strategies method
    agent.risk_assessor.assess_strategies = MagicMock(
        return_value=asyncio.Future()
    )
    agent.risk_assessor.assess_strategies.return_value.set_result([
        {
            "overall_risk": 4,
            "proceed": True,
            "risk_factors": {
                "market_volatility": 3,
                "liquidity": 2,
                "exchange_reliability": 1
            }
        }
    ])
    
    # Call assess risk node
    result_state = await agent._assess_risk_node(state)
    
    # Verify result
    assert result_state is not None
    assert "decisions" in result_state
    assert len(result_state["decisions"]) == 1
    assert "risk_assessment" in result_state["decisions"][0]
    assert result_state["decisions"][0]["risk_assessment"]["proceed"] is True
    assert result_state["decisions"][0]["risk_assessment"]["overall_risk"] == 4


@pytest.mark.asyncio
async def test_agent_optimize_execution_node(agent):
    """Test agent optimize execution node"""
    # Create initial state with risk-assessed decisions
    state = AgentState(
        pool_state={"pool_id": "test-pool", "total_value": 1000000},
        market_data={},
        opportunities=[],
        decisions=[
            {
                "opportunity": {
                    "pair": "BTC/USDT",
                    "buy_exchange": "binance",
                    "sell_exchange": "gate",
                    "buy_price": 50000,
                    "sell_price": 50100
                },
                "position_size_pct": 2.0,
                "risk_score": 3,
                "execution_priority": 7,
                "risk_assessment": {
                    "overall_risk": 4,
                    "proceed": True
                }
            }
        ],
        execution_results=[],
        errors=[],
        timestamp=datetime.now().isoformat()
    )
    
    # Mock the execution_optimizer.optimize method
    agent.execution_optimizer.optimize = MagicMock(
        return_value=asyncio.Future()
    )
    agent.execution_optimizer.optimize.return_value.set_result([
        {
            "strategy_id": "test-strategy-1",
            "buy_exchange": "binance",
            "sell_exchange": "gate",
            "symbol": "BTC/USDT",
            "amount": 0.1,
            "max_buy_price": 50050,
            "min_sell_price": 50080
        }
    ])
    
    # Call optimize execution node
    result_state = await agent._optimize_execution_node(state)
    
    # Verify result
    assert result_state is not None
    assert "execution_plan" in result_state
    assert len(result_state["execution_plan"]) == 1
    assert "strategy_id" in result_state["execution_plan"][0]
    assert "buy_exchange" in result_state["execution_plan"][0]
    assert "sell_exchange" in result_state["execution_plan"][0]
    assert "symbol" in result_state["execution_plan"][0]
    assert "amount" in result_state["execution_plan"][0]


@pytest.mark.asyncio
async def test_agent_execute_node(agent):
    """Test agent execute node"""
    # Create initial state with execution plan
    state = AgentState(
        pool_state={},
        market_data={},
        opportunities=[],
        decisions=[],
        execution_plan=[
            {
                "strategy_id": "test-strategy-1",
                "buy_exchange": "binance",
                "sell_exchange": "gate",
                "symbol": "BTC/USDT",
                "amount": 0.1,
                "max_buy_price": 50050,
                "min_sell_price": 50080
            }
        ],
        execution_results=[],
        errors=[],
        timestamp=datetime.now().isoformat()
    )
    
    # Set up mock for buy order
    buy_result = {
        "success": True,
        "order_id": "buy-order-123",
        "executed_price": 50000,
        "timestamp": datetime.now().timestamp()
    }
    
    # Set up mock for sell order
    sell_result = {
        "success": True,
        "order_id": "sell-order-456",
        "executed_price": 50100,
        "timestamp": datetime.now().timestamp()
    }
    
    # Mock the exchange_client.execute_order method with side_effect
    buy_future = asyncio.Future()
    buy_future.set_result(buy_result)
    
    sell_future = asyncio.Future()
    sell_future.set_result(sell_result)
    
    agent.exchange_client.execute_order = MagicMock()
    agent.exchange_client.execute_order.side_effect = [buy_future, sell_future]
    
    # Mock the orchestrator_client.notify_trade_execution method
    agent.orchestrator_client.notify_trade_execution = MagicMock(
        return_value=asyncio.Future()
    )
    agent.orchestrator_client.notify_trade_execution.return_value.set_result({
        "success": True
    })
    
    # Call execute node
    result_state = await agent._execute_node(state)
    
    # Verify result
    assert result_state is not None
    assert "execution_results" in result_state
    assert len(result_state["execution_results"]) == 1
    assert result_state["execution_results"][0]["success"] is True
    assert "buy_order_id" in result_state["execution_results"][0]
    assert "sell_order_id" in result_state["execution_results"][0]
    assert "profit" in result_state["execution_results"][0]
    assert "profit_pct" in result_state["execution_results"][0]


@pytest.mark.asyncio
async def test_agent_reflect_node(agent):
    """Test agent reflect node"""
    # Create initial state with execution results
    state = AgentState(
        pool_state={"pool_id": "test-pool", "total_value": 1000000},
        market_data={},
        opportunities=[],
        decisions=[
            {
                "opportunity": {
                    "pair": "BTC/USDT",
                    "buy_exchange": "binance",
                    "sell_exchange": "gate"
                },
                "position_size_pct": 2.0,
                "risk_assessment": {"proceed": True}
            }
        ],
        execution_results=[
            {
                "strategy_id": "test-strategy-1",
                "buy_exchange": "binance",
                "sell_exchange": "gate",
                "symbol": "BTC/USDT",
                "amount": 0.1,
                "buy_price": 50000,
                "sell_price": 50100,
                "profit": 10,
                "profit_pct": 0.2,
                "success": True
            }
        ],
        errors=[],
        timestamp=datetime.now().isoformat()
    )
    
    # Mock the reflection_engine.reflect method
    agent.reflection_engine.reflect = MagicMock(
        return_value=asyncio.Future()
    )
    agent.reflection_engine.reflect.return_value.set_result({
        "insights": [
            "Arbitrage between Binance and Gate.io was successful",
            "Profit was within expected range",
            "Execution time was optimal"
        ],
        "adjustments": [
            "Increase position size for similar opportunities",
            "Continue monitoring BTC/USDT pair on these exchanges"
        ]
    })
    
    # Mock the orchestrator_client.notify_event method
    agent.orchestrator_client.notify_event = MagicMock(
        return_value=asyncio.Future()
    )
    agent.orchestrator_client.notify_event.return_value.set_result({
        "success": True
    })
    
    # Call reflect node
    result_state = await agent._reflect_node(state)
    
    # Verify result
    assert result_state is not None
    assert "reflection" in result_state
    assert "insights" in result_state["reflection"]
    assert "adjustments" in result_state["reflection"]
    assert "opportunities" in result_state
    assert len(result_state["opportunities"]) == 0
    assert "decisions" in result_state
    assert len(result_state["decisions"]) == 0
    assert "execution_results" in result_state
    assert len(result_state["execution_results"]) == 0


@pytest.mark.asyncio
async def test_agent_run_continuous(agent):
    """Test agent run_continuous method with early exit"""
    # Mock the start method to avoid actual execution
    agent.start = MagicMock(
        return_value=asyncio.Future()
    )
    agent.start.return_value.set_result(None)
    
    # Create a task to run the continuous method
    task = asyncio.create_task(agent.run_continuous(interval_seconds=1))
    
    # Wait a short time to let it start
    await asyncio.sleep(0.1)
    
    # Cancel the task to stop the continuous execution
    task.cancel()
    
    # Wait for task to be cancelled
    try:
        await task
    except asyncio.CancelledError:
        pass
    
    # Verify that start was called at least once
    assert agent.start.called


@pytest.mark.asyncio
async def test_fetch_market_data(agent):
    """Test _fetch_market_data method"""
    # Mock the exchange_client.get_all_tickers method
    binance_tickers = {
        "BTC/USDT": {"price": 50000, "volume": 100},
        "ETH/USDT": {"price": 3000, "volume": 200}
    }
    
    gate_tickers = {
        "BTC/USDT": {"price": 50100, "volume": 90},
        "ETH/USDT": {"price": 3010, "volume": 180}
    }
    
    # Create futures for the mock responses
    binance_future = asyncio.Future()
    binance_future.set_result(binance_tickers)
    
    gate_future = asyncio.Future()
    gate_future.set_result(gate_tickers)
    
    # Set up the mock
    agent.exchange_client.get_all_tickers = MagicMock()
    agent.exchange_client.get_all_tickers.side_effect = [binance_future, gate_future]
    
    # Set supported exchanges
    agent.config.supported_exchanges = ["binance", "gate"]
    
    # Call _fetch_market_data
    market_data = await agent._fetch_market_data()
    
    # Verify result
    assert market_data is not None
    assert "binance" in market_data
    assert "gate" in market_data
    assert "tickers" in market_data["binance"]
    assert "tickers" in market_data["gate"]
    assert "BTC/USDT" in market_data["binance"]["tickers"]
    assert "ETH/USDT" in market_data["binance"]["tickers"]
    assert "BTC/USDT" in market_data["gate"]["tickers"]
    assert "ETH/USDT" in market_data["gate"]["tickers"]
