import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from pathlib import Path

# Add the parent directory to the path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent.poolmind_arbitrage import PoolMindArbitrageAgent, PoolMindArbitragePromptGenerator
from src.sensor.poolmind import PoolMindSensor, PoolState, ExchangePrice, ArbitrageOpportunity
from src.client.poolmind import PoolMindClient, FundRequest, ProfitReport
from src.datatypes.poolmind import PoolMindArbitrageState, PoolMetrics, ArbitrageOpportunityData


class TestPoolMindArbitragePromptGenerator:
    """Test cases for PoolMindArbitragePromptGenerator."""
    
    def test_init_with_default_prompts(self):
        """Test initialization with default prompts."""
        generator = PoolMindArbitragePromptGenerator()
        assert generator.prompts is not None
        assert "system_prompt" in generator.prompts
        assert "market_analysis_prompt" in generator.prompts
        assert "arbitrage_strategy_prompt" in generator.prompts
    
    def test_init_with_custom_prompts(self):
        """Test initialization with custom prompts."""
        custom_prompts = {
            "system_prompt": "Custom system prompt",
            "market_analysis_prompt": "Custom market analysis prompt",
            "arbitrage_strategy_prompt": "Custom arbitrage strategy prompt",
            "fund_request_prompt": "Custom fund request prompt",
            "execution_code_prompt": "Custom execution code prompt",
            "risk_assessment_prompt": "Custom risk assessment prompt"
        }
        generator = PoolMindArbitragePromptGenerator(custom_prompts)
        assert generator.prompts["system_prompt"] == "Custom system prompt"
    
    def test_validate_prompts_missing_required(self):
        """Test validation fails when required prompts are missing."""
        incomplete_prompts = {
            "system_prompt": "Test prompt"
            # Missing other required prompts
        }
        with pytest.raises(ValueError, match="Required prompt.*is missing"):
            PoolMindArbitragePromptGenerator(incomplete_prompts)
    
    def test_get_system_prompt_with_variables(self):
        """Test system prompt generation with variable substitution."""
        generator = PoolMindArbitragePromptGenerator()
        prompt = generator.get_system_prompt(
            exchanges="binance,okx",
            min_profit_threshold=0.5,
            available_stx=1000,
            current_nav=1.05
        )
        assert "binance,okx" in prompt
        assert "0.5" in prompt
        assert "1000" in prompt
        assert "1.05" in prompt


class TestPoolMindSensor:
    """Test cases for PoolMindSensor."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.sensor = PoolMindSensor(
            poolmind_api_url="http://localhost:3000",
            supported_exchanges=["binance", "okx", "gate"],
            exchange_configs={
                "binance": {"api_endpoint": "https://api.binance.com"},
                "okx": {"api_endpoint": "https://www.okx.com"},
                "gate": {"api_endpoint": "https://api.gateio.ws"}
            }
        )
    
    def test_init(self):
        """Test sensor initialization."""
        assert self.sensor.poolmind_api_url == "http://localhost:3000"
        assert len(self.sensor.supported_exchanges) == 3
        assert "binance" in self.sensor.supported_exchanges
    
    def test_get_pool_state_mock_data(self):
        """Test getting pool state returns mock data when API fails."""
        pool_state = self.sensor.get_pool_state()
        assert "current_nav" in pool_state
        assert "available_stx" in pool_state
        assert "total_shares" in pool_state
        assert pool_state["current_nav"] > 0
    
    @patch('requests.get')
    def test_get_pool_state_api_success(self, mock_get):
        """Test getting pool state from API when successful."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "nav": 1.1,
            "available_stx": 2000,
            "total_shares": 1818,
            "pool_size": 2200
        }
        mock_get.return_value = mock_response
        
        pool_state = self.sensor.get_pool_state()
        assert pool_state["current_nav"] == 1.1
        assert pool_state["available_stx"] == 2000
    
    def test_get_exchange_prices(self):
        """Test getting exchange prices."""
        prices = self.sensor.get_exchange_prices()
        assert len(prices) == 3
        assert "binance" in prices
        assert "okx" in prices
        assert "gate" in prices
        
        for exchange, price in prices.items():
            assert isinstance(price, ExchangePrice)
            assert price.exchange == exchange
            assert price.bid > 0
            assert price.ask > 0
    
    def test_identify_arbitrage_opportunities(self):
        """Test identifying arbitrage opportunities."""
        opportunities = self.sensor.identify_arbitrage_opportunities()
        assert isinstance(opportunities, list)
        
        # Check if opportunities are sorted by profit percentage
        if len(opportunities) > 1:
            assert opportunities[0].profit_percentage >= opportunities[1].profit_percentage
    
    def test_calculate_risk_score(self):
        """Test risk score calculation."""
        buy_price = ExchangePrice("binance", 2.45, 2.46, 1000000, 50000, int(datetime.now().timestamp()))
        sell_price = ExchangePrice("okx", 2.47, 2.48, 800000, 30000, int(datetime.now().timestamp()))
        
        risk_score = self.sensor._calculate_risk_score(buy_price, sell_price)
        assert isinstance(risk_score, int)
        assert 1 <= risk_score <= 10
    
    def test_get_metric_fn(self):
        """Test getting metric functions."""
        pool_state_fn = self.sensor.get_metric_fn("pool_state")
        assert callable(pool_state_fn)
        
        result = pool_state_fn()
        assert isinstance(result, dict)
        assert "current_nav" in result
        
        # Test invalid metric name
        with pytest.raises(ValueError, match="Unsupported metric"):
            self.sensor.get_metric_fn("invalid_metric")


class TestPoolMindClient:
    """Test cases for PoolMindClient."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = PoolMindClient(
            base_url="http://localhost:3000",
            agent_id="test-agent",
            hmac_secret="test-secret"
        )
    
    def test_init(self):
        """Test client initialization."""
        assert self.client.base_url == "http://localhost:3000"
        assert self.client.agent_id == "test-agent"
        assert self.client.hmac_secret == "test-secret"
    
    def test_generate_hmac_signature(self):
        """Test HMAC signature generation."""
        signature = self.client._generate_hmac_signature(
            method="POST",
            path="/api/v1/test",
            body='{"test": "data"}',
            timestamp="1234567890"
        )
        assert isinstance(signature, str)
        assert len(signature) == 64  # SHA256 hex digest length
    
    def test_fund_request_data_structure(self):
        """Test fund request data structure."""
        fund_request = FundRequest(
            amount_stx=1000.0,
            purpose="arbitrage_opportunity",
            expected_profit=50.0,
            risk_assessment="low",
            exchanges=["binance", "okx"],
            estimated_duration="5_minutes"
        )
        
        assert fund_request.amount_stx == 1000.0
        assert fund_request.purpose == "arbitrage_opportunity"
        assert fund_request.expected_profit == 50.0
        assert "binance" in fund_request.exchanges
    
    def test_profit_report_data_structure(self):
        """Test profit report data structure."""
        profit_report = ProfitReport(
            trade_id="test-trade-123",
            initial_amount=1000.0,
            final_amount=1050.0,
            profit=50.0,
            fees_paid=5.0,
            net_profit=45.0,
            execution_time="300 seconds"
        )
        
        assert profit_report.trade_id == "test-trade-123"
        assert profit_report.initial_amount == 1000.0
        assert profit_report.net_profit == 45.0


class TestPoolMindArbitrageAgent:
    """Test cases for PoolMindArbitrageAgent."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create mock components
        self.mock_rag = Mock()
        self.mock_db = Mock()
        self.mock_sensor = Mock()
        self.mock_genner = Mock()
        self.mock_container_manager = Mock()
        self.mock_prompt_generator = Mock()
        
        # Configure mock sensor
        self.mock_sensor.get_pool_state.return_value = {
            "current_nav": 1.05,
            "available_stx": 50000,
            "total_shares": 47619,
            "pool_size": 52500
        }
        
        # Create agent
        self.agent = PoolMindArbitrageAgent(
            agent_id="test-agent",
            rag=self.mock_rag,
            db=self.mock_db,
            sensor=self.mock_sensor,
            genner=self.mock_genner,
            container_manager=self.mock_container_manager,
            prompt_generator=self.mock_prompt_generator,
            poolmind_api_url="http://localhost:3000",
            hmac_secret="test-secret",
            supported_exchanges=["binance", "okx"],
            min_profit_threshold=0.5,
            max_trade_size_percent=10.0,
            stop_loss_threshold=5.0
        )
    
    def test_init(self):
        """Test agent initialization."""
        assert self.agent.agent_id == "test-agent"
        assert self.agent.min_profit_threshold == 0.5
        assert self.agent.max_trade_size_percent == 10.0
        assert len(self.agent.supported_exchanges) == 2
    
    def test_reset(self):
        """Test agent reset functionality."""
        # Add some messages to chat history
        from src.types import Message, ChatHistory
        self.agent.chat_history = ChatHistory([Message("user", "test message")])
        
        # Reset should clear chat history
        self.agent.reset()
        assert len(self.agent.chat_history) == 0
    
    def test_prepare_system(self):
        """Test system preparation."""
        chat_history = self.agent.prepare_system()
        
        # Should return ChatHistory with system message
        assert len(chat_history) == 1
        assert chat_history.messages[0].role == "system"
        
        # Mock prompt generator should have been called
        self.mock_prompt_generator.get_system_prompt.assert_called_once()


class TestPoolMindDataTypes:
    """Test cases for PoolMind data types."""
    
    def test_pool_mind_arbitrage_state_enum(self):
        """Test PoolMindArbitrageState enum."""
        assert PoolMindArbitrageState.SUCCESS.value == "success"
        assert PoolMindArbitrageState.FAILED_MARKET_ANALYSIS.value == "failed_market_analysis"
        assert PoolMindArbitrageState.HIGH_RISK_ABORT.value == "high_risk_abort"
    
    def test_pool_metrics_dataclass(self):
        """Test PoolMetrics dataclass."""
        metrics = PoolMetrics(
            current_nav=1.05,
            available_stx=50000,
            total_shares=47619,
            pool_size=52500,
            daily_return=0.02,
            weekly_return=0.08,
            monthly_return=0.15,
            total_profit=2500,
            sharpe_ratio=1.2,
            max_drawdown=0.03,
            timestamp=datetime.now()
        )
        
        assert metrics.current_nav == 1.05
        assert metrics.available_stx == 50000
        assert metrics.total_profit == 2500
    
    def test_arbitrage_opportunity_data(self):
        """Test ArbitrageOpportunityData dataclass."""
        opportunity = ArbitrageOpportunityData(
            opportunity_id="test-opp-123",
            buy_exchange="binance",
            sell_exchange="okx",
            buy_price=2.45,
            sell_price=2.47,
            profit_percentage=0.8,
            profit_amount=20,
            required_capital=1000,
            risk_score=3,
            execution_time_estimate=300,
            liquidity_score=0.8,
            market_conditions={},
            timestamp=datetime.now()
        )
        
        assert opportunity.opportunity_id == "test-opp-123"
        assert opportunity.buy_exchange == "binance"
        assert opportunity.sell_exchange == "okx"
        assert opportunity.profit_percentage == 0.8


if __name__ == "__main__":
    pytest.main([__file__]) 