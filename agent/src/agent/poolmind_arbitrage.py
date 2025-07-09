import re
from textwrap import dedent
from typing import Dict, List, Set, Tuple
from datetime import datetime
from src.db import DBInterface

from result import Err, Ok, Result

from src.container import ContainerManager
from src.genner.Base import Genner
from src.client.rag import RAGClient
from src.sensor.poolmind import PoolMindSensor
from src.types import ChatHistory, Message


class PoolMindArbitragePromptGenerator:
    """
    Generator for creating prompts used in PoolMind arbitrage agent workflows.
    
    This class is responsible for generating various prompts used by the PoolMind arbitrage agent,
    including system prompts, market analysis prompts, arbitrage strategy prompts, and execution code prompts.
    """
    
    def __init__(self, prompts: Dict[str, str] = None):
        """
        Initialize with custom prompts for each function.
        
        Args:
            prompts (Dict[str, str]): Dictionary containing custom prompts for each function
        """
        self.prompts = prompts or self.get_default_prompts()
        self._validate_prompts(self.prompts)
    
    def _validate_prompts(self, prompts: Dict[str, str]):
        """
        Validate that all required prompts are present.
        
        Args:
            prompts (Dict[str, str]): Dictionary of prompts to validate
        
        Raises:
            ValueError: If any required prompt is missing
        """
        required_prompts = [
            "system_prompt",
            "market_analysis_prompt", 
            "arbitrage_strategy_prompt",
            "fund_request_prompt",
            "execution_code_prompt",
            "risk_assessment_prompt"
        ]
        
        for prompt_name in required_prompts:
            if prompt_name not in prompts:
                raise ValueError(f"Required prompt '{prompt_name}' is missing")
    
    def get_default_prompts(self) -> Dict[str, str]:
        """
        Get the default prompts for PoolMind arbitrage agent.
        
        Returns:
            Dict[str, str]: Dictionary containing default prompts
        """
        return {
            "system_prompt": dedent("""
                You are a sophisticated STX arbitrage trading agent for the PoolMind platform.
                Your role is to identify and execute profitable arbitrage opportunities across multiple exchanges
                while managing risk and maintaining integration with the PoolMind smart contract system.
                
                Core Responsibilities:
                - Monitor STX price differences across exchanges: {exchanges}
                - Execute profitable arbitrage trades with minimum {min_profit_threshold}% profit
                - Request funds from PoolMind when opportunities arise
                - Update pool NAV based on trading profits
                - Maintain strict risk management parameters
                
                Current Pool State:
                - Available STX: {available_stx}
                - Current NAV: {current_nav}
                - Pool Size: {pool_size}
                - Your Risk Limit: {risk_limit}
                
                Trading Parameters:
                - Base Currency: STX
                - Supported Exchanges: {exchanges}
                - Max Trade Size: {max_trade_size}% of available funds
                - Stop Loss: {stop_loss_threshold}%
                
                Always prioritize capital preservation and transparent reporting to pool participants.
            """),
            
            "market_analysis_prompt": dedent("""
                Analyze the current STX market conditions across all supported exchanges.
                
                Your analysis should include:
                1. Current STX prices on each exchange: {exchanges}
                2. Order book depth and liquidity analysis
                3. 24-hour volume and volatility metrics
                4. Market sentiment indicators
                5. Identification of arbitrage opportunities
                
                Available Tools:
                - Exchange APIs for real-time price data
                - Order book analysis tools
                - Volume and liquidity metrics
                - Market sentiment analysis
                
                Write only the code to collect and analyze this market data.
                Focus on identifying price discrepancies that could be profitable after accounting for:
                - Trading fees on both exchanges
                - Slippage estimates
                - Network transaction costs
                - Execution time risks
                
                Format the code as follows:
                ```python
                from dotenv import load_dotenv
                import ...

                load_dotenv()

                def main():
                    ....

                main()
                ```
            """),
            
            "arbitrage_strategy_prompt": dedent("""
                Based on the market analysis, formulate a specific arbitrage strategy.
                
                Market Analysis Results:
                {market_analysis_results}
                
                Strategy Requirements:
                1. Identify the most profitable arbitrage opportunity
                2. Calculate required capital and expected profit
                3. Assess execution risks and timeframes
                4. Determine optimal trade sizes for both legs
                5. Plan for fund requests from PoolMind if needed
                
                Risk Assessment Criteria:
                - Market volatility during execution window
                - Liquidity risk on both exchanges
                - Counterparty risk assessment
                - Technical execution risks
                
                Your strategy should specify:
                - Target exchanges (buy low, sell high)
                - Trade amounts for each leg
                - Expected profit margins
                - Risk mitigation measures
                - Execution timeline
                - Fund requirements from PoolMind
                
                Only proceed with opportunities that meet minimum profit threshold of {min_profit_threshold}%.
            """),
            
            "fund_request_prompt": dedent("""
                Generate a fund request to PoolMind for the arbitrage opportunity.
                
                Opportunity Details:
                {opportunity_details}
                
                Required Information:
                - Amount of STX needed: {required_amount}
                - Expected profit: {expected_profit}
                - Risk assessment: {risk_level}
                - Execution timeframe: {execution_time}
                - Exchanges involved: {exchanges}
                
                Write only the code to:
                1. Prepare the fund request payload
                2. Calculate HMAC signature for authentication
                3. Submit request to PoolMind API
                4. Handle approval/rejection responses
                5. Proceed with trade execution upon approval
                
                Format the code as follows:
                ```python
                from dotenv import load_dotenv
                import ...

                load_dotenv()

                def main():
                    ....

                main()
                ```
            """),
            
            "execution_code_prompt": dedent("""
                Generate code to execute the approved arbitrage trade.
                
                Strategy Details:
                {strategy_details}
                
                Fund Allocation:
                - Approved Amount: {approved_amount}
                - Buy Exchange: {buy_exchange}
                - Sell Exchange: {sell_exchange}
                - Expected Profit: {expected_profit}
                
                Write only the code for:
                1. Simultaneous order placement on both exchanges
                2. Real-time monitoring of execution status
                3. Risk management with stop-loss triggers
                4. Profit calculation and reporting
                5. Return of funds + profits to PoolMind
                
                Include:
                - Exchange API integrations
                - Order placement and monitoring
                - Error handling and rollback procedures
                - Profit/loss calculation
                - PoolMind profit reporting
                - NAV update triggers
                
                Format the code as follows:
                ```python
                from dotenv import load_dotenv
                import ...

                load_dotenv()

                def main():
                    ....

                main()
                ```
            """),
            
            "risk_assessment_prompt": dedent("""
                Perform comprehensive risk assessment for the arbitrage opportunity.
                
                Opportunity Data:
                {opportunity_data}
                
                Risk Factors to Analyze:
                1. Market Volatility Risk
                   - STX price volatility during execution window
                   - Market depth and liquidity changes
                   - Potential slippage on large orders
                
                2. Execution Risk
                   - Time delay between buy and sell orders
                   - Exchange connectivity and reliability
                   - Order partial fills or rejections
                
                3. Counterparty Risk
                   - Exchange reputation and reliability
                   - Withdrawal/deposit processing times
                   - Exchange-specific risks
                
                4. Technical Risk
                   - API failures or rate limiting
                   - Network connectivity issues
                   - Smart contract interaction risks
                
                Write only the code to generate a risk score (1-10) and recommendation:
                - 1-3: Low risk - Proceed with full position
                - 4-6: Medium risk - Reduce position size
                - 7-10: High risk - Abort opportunity
                
                Format the code as follows:
                ```python
                from dotenv import load_dotenv
                import ...

                load_dotenv()

                def main():
                    ....

                main()
                ```
            """)
        }
    
    def get_system_prompt(self, **kwargs) -> str:
        """
        Get the system prompt with variable substitution.
        
        Args:
            **kwargs: Variables to substitute in the prompt
            
        Returns:
            str: The formatted system prompt
        """
        return self.prompts["system_prompt"].format(**kwargs)
    
    def get_market_analysis_prompt(self, **kwargs) -> str:
        """
        Get the market analysis prompt with variable substitution.
        
        Args:
            **kwargs: Variables to substitute in the prompt
            
        Returns:
            str: The formatted market analysis prompt
        """
        return self.prompts["market_analysis_prompt"].format(**kwargs)
    
    def get_arbitrage_strategy_prompt(self, **kwargs) -> str:
        """
        Get the arbitrage strategy prompt with variable substitution.
        
        Args:
            **kwargs: Variables to substitute in the prompt
            
        Returns:
            str: The formatted arbitrage strategy prompt
        """
        return self.prompts["arbitrage_strategy_prompt"].format(**kwargs)
    
    def get_fund_request_prompt(self, **kwargs) -> str:
        """
        Get the fund request prompt with variable substitution.
        
        Args:
            **kwargs: Variables to substitute in the prompt
            
        Returns:
            str: The formatted fund request prompt
        """
        return self.prompts["fund_request_prompt"].format(**kwargs)
    
    def get_execution_code_prompt(self, **kwargs) -> str:
        """
        Get the execution code prompt with variable substitution.
        
        Args:
            **kwargs: Variables to substitute in the prompt
            
        Returns:
            str: The formatted execution code prompt
        """
        return self.prompts["execution_code_prompt"].format(**kwargs)
    
    def get_risk_assessment_prompt(self, **kwargs) -> str:
        """
        Get the risk assessment prompt with variable substitution.
        
        Args:
            **kwargs: Variables to substitute in the prompt
            
        Returns:
            str: The formatted risk assessment prompt
        """
        return self.prompts["risk_assessment_prompt"].format(**kwargs)


class PoolMindArbitrageAgent:
    """
    Agent responsible for executing STX arbitrage strategies for PoolMind.
    
    This class orchestrates the complete arbitrage workflow, including market analysis,
    strategy formulation, fund requests, and trade execution while maintaining
    integration with the PoolMind smart contract system.
    """
    
    def __init__(
        self,
        agent_id: str,
        rag: RAGClient,
        db: DBInterface,
        sensor: PoolMindSensor,
        genner: Genner,
        container_manager: ContainerManager,
        prompt_generator: PoolMindArbitragePromptGenerator,
        poolmind_api_url: str,
        hmac_secret: str,
        supported_exchanges: List[str],
        min_profit_threshold: float = 0.5,
        max_trade_size_percent: float = 10.0,
        stop_loss_threshold: float = 5.0,
    ):
        """
        Initialize the PoolMind arbitrage agent with all required components.
        
        Args:
            agent_id (str): Unique identifier for this agent
            rag (RAGClient): Client for retrieval-augmented generation
            db (DBInterface): Database client for storing and retrieving data
            sensor (PoolMindSensor): Sensor for monitoring PoolMind and market data
            genner (Genner): Generator for creating code and strategies
            container_manager (ContainerManager): Manager for code execution in containers
            prompt_generator (PoolMindArbitragePromptGenerator): Generator for creating prompts
            poolmind_api_url (str): URL for PoolMind API
            hmac_secret (str): Secret for HMAC authentication
            supported_exchanges (List[str]): List of supported exchanges
            min_profit_threshold (float): Minimum profit threshold (%)
            max_trade_size_percent (float): Maximum trade size as % of available funds
            stop_loss_threshold (float): Stop loss threshold (%)
        """
        self.agent_id = agent_id
        self.db = db
        self.rag = rag
        self.sensor = sensor
        self.genner = genner
        self.container_manager = container_manager
        self.prompt_generator = prompt_generator
        self.poolmind_api_url = poolmind_api_url
        self.hmac_secret = hmac_secret
        self.supported_exchanges = supported_exchanges
        self.min_profit_threshold = min_profit_threshold
        self.max_trade_size_percent = max_trade_size_percent
        self.stop_loss_threshold = stop_loss_threshold
        
        self.chat_history = ChatHistory()
    
    def reset(self) -> None:
        """
        Reset the agent's chat history.
        
        This method clears any existing conversation history to start fresh.
        """
        self.chat_history = ChatHistory()
    
    def prepare_system(self, **kwargs) -> ChatHistory:
        """
        Prepare the system prompt with current pool state and configuration.
        
        Args:
            **kwargs: Additional variables for prompt formatting
            
        Returns:
            ChatHistory: Chat history with system prompt
        """
        pool_state = self.sensor.get_pool_state()
        
        system_prompt = self.prompt_generator.get_system_prompt(
            exchanges=", ".join(self.supported_exchanges),
            min_profit_threshold=self.min_profit_threshold,
            available_stx=pool_state.get("available_stx", 0),
            current_nav=pool_state.get("current_nav", 1.0),
            pool_size=pool_state.get("pool_size", 0),
            risk_limit=pool_state.get("available_stx", 0) * self.max_trade_size_percent / 100,
            max_trade_size=self.max_trade_size_percent,
            stop_loss_threshold=self.stop_loss_threshold,
            **kwargs
        )
        
        return ChatHistory([Message("system", system_prompt)])
    
    def analyze_market(self) -> Result[Tuple[str, ChatHistory], str]:
        """
        Generate and execute market analysis code.
        
        Returns:
            Result[Tuple[str, ChatHistory], str]: Market analysis results and chat history
        """
        try:
            market_analysis_prompt = self.prompt_generator.get_market_analysis_prompt(
                exchanges=", ".join(self.supported_exchanges)
            )
            
            prompt_message = Message("user", market_analysis_prompt)
            analysis_history = self.chat_history.append(prompt_message)
            
            # Generate market analysis code
            code_result = self.genner.generate_code(analysis_history)
            if isinstance(code_result, Err):
                return Err(f"Failed to generate market analysis code: {code_result.err()}")
            
            code_blocks, response = code_result.ok()
            if not code_blocks:
                return Err("No code blocks generated for market analysis")
            
            # Execute the market analysis code
            execution_result = self.container_manager.run_code_in_con(
                code_blocks[0], "poolmind_market_analysis"
            )
            
            if isinstance(execution_result, Err):
                return Err(f"Failed to execute market analysis: {execution_result.err()}")
            
            analysis_output, _ = execution_result.ok()
            
            # Update chat history with response
            response_message = Message("assistant", response)
            updated_history = analysis_history.append(response_message)
            
            return Ok((analysis_output, updated_history))
            
        except Exception as e:
            return Err(f"Market analysis failed: {str(e)}")
    
    def generate_arbitrage_strategy(self, market_analysis_results: str) -> Result[Tuple[str, ChatHistory], str]:
        """
        Generate arbitrage strategy based on market analysis.
        
        Args:
            market_analysis_results (str): Results from market analysis
            
        Returns:
            Result[Tuple[str, ChatHistory], str]: Strategy and updated chat history
        """
        try:
            strategy_prompt = self.prompt_generator.get_arbitrage_strategy_prompt(
                market_analysis_results=market_analysis_results,
                min_profit_threshold=self.min_profit_threshold
            )
            
            prompt_message = Message("user", strategy_prompt)
            strategy_history = self.chat_history.append(prompt_message)
            
            # Generate strategy
            strategy_result = self.genner.ch_completion(strategy_history)
            if isinstance(strategy_result, Err):
                return Err(f"Failed to generate arbitrage strategy: {strategy_result.err()}")
            
            strategy_output = strategy_result.ok()
            
            # Update chat history
            response_message = Message("assistant", strategy_output)
            updated_history = strategy_history.append(response_message)
            
            return Ok((strategy_output, updated_history))
            
        except Exception as e:
            return Err(f"Strategy generation failed: {str(e)}")
    
    def request_funds(self, opportunity_details: Dict) -> Result[Tuple[str, ChatHistory], str]:
        """
        Generate and execute fund request code.
        
        Args:
            opportunity_details (Dict): Details about the arbitrage opportunity
            
        Returns:
            Result[Tuple[str, ChatHistory], str]: Fund request results and chat history
        """
        try:
            fund_request_prompt = self.prompt_generator.get_fund_request_prompt(
                opportunity_details=str(opportunity_details),
                required_amount=opportunity_details.get("required_amount", 0),
                expected_profit=opportunity_details.get("expected_profit", 0),
                risk_level=opportunity_details.get("risk_level", "medium"),
                execution_time=opportunity_details.get("execution_time", "5 minutes"),
                exchanges=", ".join(opportunity_details.get("exchanges", []))
            )
            
            prompt_message = Message("user", fund_request_prompt)
            request_history = self.chat_history.append(prompt_message)
            
            # Generate fund request code
            code_result = self.genner.generate_code(request_history)
            if isinstance(code_result, Err):
                return Err(f"Failed to generate fund request code: {code_result.err()}")
            
            code_blocks, response = code_result.ok()
            if not code_blocks:
                return Err("No code blocks generated for fund request")
            
            # Execute the fund request code
            execution_result = self.container_manager.run_code_in_con(
                code_blocks[0], "poolmind_fund_request"
            )
            
            if isinstance(execution_result, Err):
                return Err(f"Failed to execute fund request: {execution_result.err()}")
            
            request_output, _ = execution_result.ok()
            
            # Update chat history
            response_message = Message("assistant", response)
            updated_history = request_history.append(response_message)
            
            return Ok((request_output, updated_history))
            
        except Exception as e:
            return Err(f"Fund request failed: {str(e)}")
    
    def execute_arbitrage_trade(self, strategy_details: Dict, approved_amount: float) -> Result[Tuple[str, ChatHistory], str]:
        """
        Generate and execute arbitrage trade code.
        
        Args:
            strategy_details (Dict): Details about the arbitrage strategy
            approved_amount (float): Amount approved for trading
            
        Returns:
            Result[Tuple[str, ChatHistory], str]: Trade execution results and chat history
        """
        try:
            execution_prompt = self.prompt_generator.get_execution_code_prompt(
                strategy_details=str(strategy_details),
                approved_amount=approved_amount,
                buy_exchange=strategy_details.get("buy_exchange", ""),
                sell_exchange=strategy_details.get("sell_exchange", ""),
                expected_profit=strategy_details.get("expected_profit", 0)
            )
            
            prompt_message = Message("user", execution_prompt)
            execution_history = self.chat_history.append(prompt_message)
            
            # Generate execution code
            code_result = self.genner.generate_code(execution_history)
            if isinstance(code_result, Err):
                return Err(f"Failed to generate execution code: {code_result.err()}")
            
            code_blocks, response = code_result.ok()
            if not code_blocks:
                return Err("No code blocks generated for trade execution")
            
            # Execute the arbitrage trade
            execution_result = self.container_manager.run_code_in_con(
                code_blocks[0], "poolmind_arbitrage_execution"
            )
            
            if isinstance(execution_result, Err):
                return Err(f"Failed to execute arbitrage trade: {execution_result.err()}")
            
            trade_output, _ = execution_result.ok()
            
            # Update chat history
            response_message = Message("assistant", response)
            updated_history = execution_history.append(response_message)
            
            return Ok((trade_output, updated_history))
            
        except Exception as e:
            return Err(f"Trade execution failed: {str(e)}")
    
    def assess_risk(self, opportunity_data: Dict) -> Result[Tuple[Dict, ChatHistory], str]:
        """
        Perform risk assessment for the arbitrage opportunity.
        
        Args:
            opportunity_data (Dict): Data about the arbitrage opportunity
            
        Returns:
            Result[Tuple[Dict, ChatHistory], str]: Risk assessment results and chat history
        """
        try:
            risk_prompt = self.prompt_generator.get_risk_assessment_prompt(
                opportunity_data=str(opportunity_data)
            )
            
            prompt_message = Message("user", risk_prompt)
            risk_history = self.chat_history.append(prompt_message)
            
            # Generate risk assessment code
            code_result = self.genner.generate_code(risk_history)
            if isinstance(code_result, Err):
                return Err(f"Failed to generate risk assessment code: {code_result.err()}")
            
            code_blocks, response = code_result.ok()
            if not code_blocks:
                return Err("No code blocks generated for risk assessment")
            
            # Execute risk assessment
            execution_result = self.container_manager.run_code_in_con(
                code_blocks[0], "poolmind_risk_assessment"
            )
            
            if isinstance(execution_result, Err):
                return Err(f"Failed to execute risk assessment: {execution_result.err()}")
            
            risk_output, _ = execution_result.ok()
            
            # Parse risk assessment results
            try:
                # Assuming the risk assessment returns JSON-formatted results
                import json
                risk_data = json.loads(risk_output)
            except:
                # Fallback to basic parsing if JSON parsing fails
                risk_data = {
                    "risk_score": 5,
                    "recommendation": "proceed",
                    "raw_output": risk_output
                }
            
            # Update chat history
            response_message = Message("assistant", response)
            updated_history = risk_history.append(response_message)
            
            return Ok((risk_data, updated_history))
            
        except Exception as e:
            return Err(f"Risk assessment failed: {str(e)}")
    
    def get_exchange_deposit_address(self, exchange: str, asset: str = "STX") -> str:
        """
        Get deposit address for a specific exchange and asset.
        
        In a real implementation, this would call the exchange's API to get
        a fresh deposit address for the trading account.
        
        Args:
            exchange (str): Exchange name (e.g., "binance", "okx")
            asset (str): Asset symbol (default: "STX")
            
        Returns:
            str: Deposit address for the exchange
        """
        # Mock implementation - in reality this would call exchange APIs
        mock_addresses = {
            "binance": "SP1BINANCEDEPOSIT123456789ABCDEFGHIJK",
            "okx": "SP1OKXDEPOSIT123456789ABCDEFGHIJKLMN",
            "gate": "SP1GATEDEPOSIT123456789ABCDEFGHIJKLM",
            "hotcoin": "SP1HOTCOINDEPOSIT123456789ABCDEFGHIJ",
            "bybit": "SP1BYBITDEPOSIT123456789ABCDEFGHIJKL",
            "coinw": "SP1COINWDEPOSIT123456789ABCDEFGHIJKL",
            "orangex": "SP1ORANGEXDEPOSIT123456789ABCDEFGHIJ"
        }
        
        # Return mock address or generate one if exchange not in list
        if exchange.lower() in mock_addresses:
            return mock_addresses[exchange.lower()]
        else:
            # Generate a mock address for unknown exchanges
            return f"SP1{exchange.upper()[:8]}DEPOSIT123456789ABCDEF" 