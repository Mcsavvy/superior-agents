"""
Tests for the PoolMind Agent API endpoints
"""
import pytest
import json
from fastapi.testclient import TestClient

from poolmind_agent.api.server import app
from poolmind_agent.core.agent import PoolMindAgent


@pytest.fixture
def client():
    """Test client fixture"""
    with TestClient(app) as client:
        yield client


def test_health_endpoint(client):
    """Test health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "uptime" in data


def test_metrics_endpoint(client):
    """Test metrics endpoint"""
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "agent_uptime" in data
    assert "last_activity" in data


def test_observe_market_endpoint(client):
    """Test observe market endpoint"""
    market_data = {
        "market_conditions": [
            {
                "exchange_data": {
                    "binance": {
                        "BTC/USDT": {
                            "price": 50000.0,
                            "volume": 100.0
                        }
                    },
                    "coinbase": {
                        "BTC/USDT": {
                            "price": 50200.0,
                            "volume": 80.0
                        }
                    }
                }
            }
        ]
    }
    
    response = client.post("/observe", json=market_data)
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    assert "opportunities_detected" in data


def test_get_opportunities_endpoint(client):
    """Test get opportunities endpoint"""
    response = client.get("/opportunities")
    assert response.status_code == 200
    data = response.json()
    assert "opportunities" in data
    assert isinstance(data["opportunities"], list)


def test_generate_strategy_endpoint(client):
    """Test generate strategy endpoint"""
    opportunity = {
        "opportunity": {
            "pair": "BTC/USDT",
            "buy_exchange": "binance",
            "buy_price": 50000.0,
            "sell_exchange": "coinbase",
            "sell_price": 50200.0,
            "price_diff_pct": 0.4,
            "estimated_profit_pct": 0.2
        }
    }
    
    response = client.post("/strategy/generate", json=opportunity)
    assert response.status_code == 200
    data = response.json()
    assert "strategy" in data


def test_assess_risk_endpoint(client):
    """Test assess risk endpoint"""
    strategy = {
        "strategy": {
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
    }
    
    response = client.post("/strategy/assess-risk", json=strategy)
    assert response.status_code == 200
    data = response.json()
    assert "risk_assessment" in data


def test_optimize_execution_endpoint(client):
    """Test optimize execution endpoint"""
    strategy = {
        "strategy": {
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
    }
    
    response = client.post("/strategy/optimize", json=strategy)
    assert response.status_code == 200
    data = response.json()
    assert "execution_plan" in data


def test_execute_strategy_endpoint(client):
    """Test execute strategy endpoint"""
    strategy = {
        "strategy": {
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
    }
    
    response = client.post("/strategy/execute", json=strategy)
    assert response.status_code == 202
    data = response.json()
    assert "task_id" in data


def test_get_execution_result_endpoint(client):
    """Test get execution result endpoint"""
    response = client.get("/strategy/execution-result/test-strategy-id")
    assert response.status_code == 200
    data = response.json()
    assert "result" in data


def test_reflect_endpoint(client):
    """Test reflect endpoint"""
    execution_result = {
        "execution_result": {
            "strategy": {
                "opportunity": {
                    "pair": "BTC/USDT",
                    "buy_exchange": "binance",
                    "sell_exchange": "coinbase"
                }
            },
            "success": True,
            "profit": 100.0,
            "execution_time": 5.2,
            "slippage": 0.05
        }
    }
    
    response = client.post("/reflect", json=execution_result)
    assert response.status_code == 200
    data = response.json()
    assert "insights" in data


def test_get_insights_endpoint(client):
    """Test get insights endpoint"""
    response = client.get("/insights")
    assert response.status_code == 200
    data = response.json()
    assert "insights" in data


def test_run_full_cycle_endpoint(client):
    """Test run full cycle endpoint"""
    market_data = {
        "market_conditions": [
            {
                "exchange_data": {
                    "binance": {
                        "BTC/USDT": {
                            "price": 50000.0,
                            "volume": 100.0
                        }
                    },
                    "coinbase": {
                        "BTC/USDT": {
                            "price": 50200.0,
                            "volume": 80.0
                        }
                    }
                }
            }
        ]
    }
    
    response = client.post("/run-cycle", json=market_data)
    assert response.status_code == 202
    data = response.json()
    assert "task_id" in data


def test_get_config_endpoint(client):
    """Test get config endpoint"""
    response = client.get("/config")
    assert response.status_code == 200
    data = response.json()
    assert "config" in data


def test_update_config_endpoint(client):
    """Test update config endpoint"""
    config_updates = {
        "updates": {
            "primary_llm_temperature": 0.5,
            "min_profit_threshold": 0.3,
            "max_risk_threshold": 7.0
        }
    }
    
    response = client.post("/config", json=config_updates)
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    assert data["success"] is True


def test_reset_agent_endpoint(client):
    """Test reset agent endpoint"""
    response = client.post("/reset")
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    assert data["success"] is True
