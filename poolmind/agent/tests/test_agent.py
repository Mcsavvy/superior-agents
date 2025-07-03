"""
Tests for the PoolMind Agent core functionality
"""
import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any
from unittest.mock import patch, MagicMock

from poolmind_agent.core.agent import PoolMindAgent


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
async def test_agent_observe(agent, sample_market_data):
    """Test agent observe method"""
    result = await agent.observe([sample_market_data])
    
    assert result is not None
    assert "success" in result
    assert result["success"] is True
    assert "opportunities_detected" in result
    assert "timestamp" in result


@pytest.mark.asyncio
async def test_agent_get_opportunities(agent, sample_market_data):
    """Test agent get opportunities method"""
    # First observe to detect opportunities
    await agent.observe([sample_market_data])
    
    # Then get opportunities
    opportunities = await agent.get_detected_opportunities(limit=5)
    
    assert opportunities is not None
    assert isinstance(opportunities, list)
    
    # If opportunities were detected, check their structure
    if opportunities:
        opportunity = opportunities[0]
        assert "pair" in opportunity
        assert "buy_exchange" in opportunity
        assert "sell_exchange" in opportunity
        assert "estimated_profit_pct" in opportunity


@pytest.mark.asyncio
async def test_agent_generate_strategy(agent, sample_opportunity):
    """Test agent generate strategy method"""
    strategy = await agent.generate_strategy(sample_opportunity)
    
    assert strategy is not None
    assert isinstance(strategy, dict)
    
    # Check if strategy has required fields
    if strategy:
        assert "opportunity" in strategy
        assert "position_size_pct" in strategy
        assert "risk_score" in strategy
        assert "execution_priority" in strategy


@pytest.mark.asyncio
async def test_agent_assess_risk(agent, sample_strategy):
    """Test agent assess risk method"""
    risk_assessment = await agent.assess_risk(sample_strategy)
    
    assert risk_assessment is not None
    assert isinstance(risk_assessment, dict)
    
    # Check if risk assessment has required fields
    if risk_assessment:
        assert "overall_risk" in risk_assessment
        assert "proceed" in risk_assessment


@pytest.mark.asyncio
async def test_agent_optimize_execution(agent, sample_strategy):
    """Test agent optimize execution method"""
    execution_plan = await agent.optimize_execution(sample_strategy)
    
    assert execution_plan is not None
    assert isinstance(execution_plan, dict)


@pytest.mark.asyncio
async def test_agent_execute(agent, sample_strategy):
    """Test agent execute method"""
    execution_result = await agent.execute(sample_strategy)
    
    assert execution_result is not None
    assert isinstance(execution_result, dict)


@pytest.mark.asyncio
async def test_agent_reflect(agent, sample_strategy):
    """Test agent reflect method"""
    # Create a mock execution result
    execution_result = {
        "strategy": sample_strategy,
        "success": True,
        "profit": 100.0,
        "execution_time": 5.2,
        "slippage": 0.05,
        "timestamp": datetime.now().isoformat()
    }
    
    reflection = await agent.reflect(execution_result)
    
    assert reflection is not None
    assert isinstance(reflection, dict)


@pytest.mark.asyncio
async def test_agent_run_full_cycle(agent, sample_market_data):
    """Test agent run full cycle method"""
    result = await agent.run_full_cycle([sample_market_data])
    
    assert result is not None
    assert isinstance(result, dict)
    assert "success" in result


@pytest.mark.asyncio
async def test_agent_update_config(agent):
    """Test agent update config method"""
    config_updates = {
        "primary_llm_temperature": 0.5,
        "min_profit_threshold": 0.3,
        "max_risk_threshold": 7.0
    }
    
    success = await agent.update_config(config_updates)
    
    assert success is True
    assert agent.config.primary_llm_temperature == 0.5
    assert agent.config.min_profit_threshold == 0.3
    assert agent.config.max_risk_threshold == 7.0
