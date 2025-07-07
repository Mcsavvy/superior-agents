"""
PoolMind Agent - Core Agent Module
"""
from typing import Dict, List, Optional, TypedDict, Any
import logging
import time
import asyncio
from datetime import datetime

from langgraph.graph import StateGraph
from pydantic import BaseModel

from poolmind_agent.core.pool_context import PoolContextEngine
from poolmind_agent.core.strategy_generator import StrategyGenerator
from poolmind_agent.core.risk_assessor import RiskAssessor
from poolmind_agent.core.execution_optimizer import ExecutionOptimizer
from poolmind_agent.core.reflection_engine import ReflectionEngine
from poolmind_agent.services.llm_service import LLMService
from poolmind_agent.services.rag_service import RAGService
from poolmind_agent.services.exchange_client import ExchangeClient
from poolmind_agent.services.blockchain_client import BlockchainClient
from poolmind_agent.services.orchestrator_client import OrchestratorClient
from poolmind_agent.utils.config import AgentConfig

logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    """State object for the agent workflow"""
    pool_state: Dict
    market_data: Dict
    opportunities: List[Dict]
    decisions: List[Dict]
    execution_results: List[Dict]
    errors: List[Dict]
    timestamp: str

class PoolMindAgent:
    """
    Main agent class that orchestrates the multi-agent system for 
    pooled cross-exchange arbitrage trading.
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """
        Initialize the PoolMind Agent with its components
        
        Args:
            config: Configuration for the agent
        """
        self.config = config or AgentConfig()
        logger.info("Initializing PoolMind Agent")
        
        # Initialize service clients
        self.llm_service = None
        self.rag_service = None
        self.exchange_client = None
        self.blockchain_client = None
        self.orchestrator_client = None
        
        # Initialize core components
        self.pool_context = None
        self.strategy_generator = None
        self.risk_assessor = None
        self.execution_optimizer = None
        self.reflection_engine = None
        
        # Initialize state graph
        self.graph = None
        
        # Track agent state
        self.start_time = time.time()
        self.last_activity_time = time.time()
        self.is_initialized = False
    
    async def initialize(self) -> None:
        """
        Initialize all components and services asynchronously
        """
        try:
            logger.info("Initializing PoolMind Agent services and components")
            
            # Initialize service clients first
            self.llm_service = LLMService(self.config)
            self.rag_service = RAGService(self.config)
            self.exchange_client = ExchangeClient(self.config)
            self.blockchain_client = BlockchainClient(self.config)
            self.orchestrator_client = OrchestratorClient(self.config)
            
            # Initialize core components
            self.pool_context = PoolContextEngine(self.config)
            self.strategy_generator = StrategyGenerator(self.config)
            self.risk_assessor = RiskAssessor(self.config)
            self.execution_optimizer = ExecutionOptimizer(self.config)
            self.reflection_engine = ReflectionEngine(self.config)
            
            # Initialize state graph
            self.graph = self._build_state_graph()
            
            # Update initialization state
            self.is_initialized = True
            self.start_time = time.time()  # Reset start time on each initialization
            self.last_activity_time = time.time()
            
            logger.info("PoolMind Agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing PoolMind Agent: {str(e)}")
            raise
    
    def _build_state_graph(self) -> StateGraph:
        """
        Build the state graph for the agent workflow
        
        Returns:
            StateGraph: The compiled state graph
        """
        builder = StateGraph(AgentState)
        
        # Add nodes
        builder.add_node("observe", self._observe_node)
        builder.add_node("detect_opportunities", self._detect_opportunities_node)
        builder.add_node("generate_strategy", self._generate_strategy_node)
        builder.add_node("assess_risk", self._assess_risk_node)
        builder.add_node("optimize_execution", self._optimize_execution_node)
        builder.add_node("execute", self._execute_node)
        builder.add_node("reflect", self._reflect_node)
        
        # Set entry point
        builder.set_entry_point("observe")
        
        # Add edges
        builder.add_edge("observe", "detect_opportunities")
        builder.add_edge("detect_opportunities", "generate_strategy")
        builder.add_edge("generate_strategy", "assess_risk")
        builder.add_edge("assess_risk", "optimize_execution")
        builder.add_edge("optimize_execution", "execute")
        builder.add_edge("execute", "reflect")
        builder.add_edge("reflect", "observe")  # Complete the loop
        
        # Add conditional edges for error handling
        builder.add_conditional_edges(
            "detect_opportunities",
            self._handle_empty_opportunities,
            {
                "continue": "generate_strategy",
                "skip": "observe"
            }
        )
        
        builder.add_conditional_edges(
            "assess_risk",
            self._handle_risk_assessment,
            {
                "proceed": "optimize_execution",
                "reject": "reflect"
            }
        )
        
        return builder.compile()
    
    async def _observe_node(self, state: AgentState) -> AgentState:
        """Observe the current market and pool state"""
        logger.debug("Observing market and pool state")
        
        try:
            # Get pool state from external API
            pool_state = await self.orchestrator_client.get_pool_status()
            
            # Get market data from exchanges
            market_data = await self._fetch_market_data()
            
            return {
                **state,
                "pool_state": pool_state,
                "market_data": market_data,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error("Error in observe node: %s", str(e))
            return {
                **state,
                "errors": state.get("errors", []) + [{"step": "observe", "error": str(e)}]
            }
    
    async def _fetch_market_data(self) -> Dict[str, Any]:
        """
        Fetch market data from all supported exchanges
        
        Returns:
            Dict containing market data from all exchanges
        """
        market_data = {}
        
        try:
            # Get data from each exchange
            for exchange in self.config.supported_exchanges:
                # Get all tickers for this exchange
                exchange_tickers = await self.exchange_client.get_all_tickers(exchange)
                
                # Store in market data
                market_data[exchange] = {
                    "tickers": exchange_tickers,
                    "timestamp": datetime.now().isoformat()
                }
                
                logger.debug(f"Fetched {len(exchange_tickers)} tickers from {exchange}")
            
            return market_data
        except Exception as e:
            logger.error(f"Error fetching market data: {str(e)}")
            return {}
    
    async def _detect_opportunities_node(self, state: AgentState) -> AgentState:
        """Detect arbitrage opportunities from market data"""
        logger.debug("Detecting arbitrage opportunities")
        
        try:
            opportunities = await self.strategy_generator.detect_opportunities(
                state["pool_state"], 
                state["market_data"]
            )
            
            # Report opportunities to external API
            if opportunities:
                for opportunity in opportunities:
                    await self.orchestrator_client.report_arbitrage_opportunity(opportunity)
            
            return {
                **state,
                "opportunities": opportunities
            }
        except Exception as e:
            logger.error("Error in detect_opportunities node: %s", str(e))
            return {
                **state,
                "errors": state.get("errors", []) + [{"step": "detect_opportunities", "error": str(e)}],
                "opportunities": []
            }
    
    def _handle_empty_opportunities(self, state: AgentState) -> str:
        """Decide whether to continue if no opportunities are found"""
        if not state.get("opportunities"):
            logger.info("No opportunities detected, skipping strategy generation")
            return "skip"
        return "continue"
    
    async def _generate_strategy_node(self, state: AgentState) -> AgentState:
        """Generate trading strategies for detected opportunities"""
        logger.debug("Generating trading strategies")
        
        try:
            decisions = await self.strategy_generator.generate_strategy(
                state["pool_state"],
                state["market_data"],
                state["opportunities"]
            )
            
            return {
                **state,
                "decisions": decisions
            }
        except Exception as e:
            logger.error("Error in generate_strategy node: %s", str(e))
            return {
                **state,
                "errors": state.get("errors", []) + [{"step": "generate_strategy", "error": str(e)}],
                "decisions": []
            }
    
    async def _assess_risk_node(self, state: AgentState) -> AgentState:
        """Assess risk for each trading strategy"""
        logger.debug("Assessing risk for trading strategies")
        
        try:
            risk_assessments = await self.risk_assessor.assess_strategies(
                state["pool_state"],
                state["decisions"]
            )
            
            return {
                **state,
                "decisions": [
                    {**decision, "risk_assessment": assessment}
                    for decision, assessment in zip(state["decisions"], risk_assessments)
                ]
            }
        except Exception as e:
            logger.error("Error in assess_risk node: %s", str(e))
            return {
                **state,
                "errors": state.get("errors", []) + [{"step": "assess_risk", "error": str(e)}]
            }
    
    def _handle_risk_assessment(self, state: AgentState) -> str:
        """Decide whether to proceed based on risk assessment"""
        if not state.get("decisions"):
            logger.info("No decisions to assess risk for")
            return "reject"
        
        # Check if any decision passes risk assessment
        for decision in state["decisions"]:
            if decision.get("risk_assessment", {}).get("proceed", False):
                return "proceed"
        
        logger.info("All decisions rejected by risk assessment")
        return "reject"
    
    async def _optimize_execution_node(self, state: AgentState) -> AgentState:
        """Optimize execution for approved strategies"""
        logger.debug("Optimizing execution for approved strategies")
        
        try:
            # Filter decisions that passed risk assessment
            approved_decisions = [
                d for d in state["decisions"]
                if d.get("risk_assessment", {}).get("proceed", False)
            ]
            
            if not approved_decisions:
                return {
                    **state,
                    "execution_plan": []
                }
            
            execution_plan = await self.execution_optimizer.optimize(
                state["pool_state"],
                approved_decisions
            )
            
            return {
                **state,
                "execution_plan": execution_plan
            }
        except Exception as e:
            logger.error("Error in optimize_execution node: %s", str(e))
            return {
                **state,
                "errors": state.get("errors", []) + [{"step": "optimize_execution", "error": str(e)}],
                "execution_plan": []
            }
    
    async def _execute_node(self, state: AgentState) -> AgentState:
        """Execute the optimized trading plan"""
        logger.debug("Executing trading plan")
        
        try:
            if not state.get("execution_plan"):
                logger.info("No execution plan to execute")
                return {
                    **state,
                    "execution_results": []
                }
            
            # Execute trades using real exchange API
            execution_results = []
            
            for plan in state["execution_plan"]:
                # Extract trade details
                buy_exchange = plan.get("buy_exchange")
                sell_exchange = plan.get("sell_exchange")
                symbol = plan.get("symbol")
                amount = plan.get("amount")
                
                # Execute buy order
                buy_result = await self.exchange_client.execute_order(
                    exchange=buy_exchange,
                    symbol=symbol,
                    side="buy",
                    amount=amount
                )
                
                # If buy successful, execute sell order
                if buy_result.get("success"):
                    sell_result = await self.exchange_client.execute_order(
                        exchange=sell_exchange,
                        symbol=symbol,
                        side="sell",
                        amount=amount
                    )
                    
                    # Calculate profit
                    buy_price = buy_result.get("executed_price", 0)
                    sell_price = sell_result.get("executed_price", 0)
                    profit = (sell_price - buy_price) * amount
                    profit_pct = ((sell_price - buy_price) / buy_price) * 100 if buy_price > 0 else 0
                    
                    # Create result
                    result = {
                        "strategy_id": plan.get("strategy_id"),
                        "buy_exchange": buy_exchange,
                        "sell_exchange": sell_exchange,
                        "symbol": symbol,
                        "amount": amount,
                        "buy_price": buy_price,
                        "sell_price": sell_price,
                        "profit": profit,
                        "profit_pct": profit_pct,
                        "buy_order_id": buy_result.get("order_id"),
                        "sell_order_id": sell_result.get("order_id"),
                        "timestamp": datetime.now().isoformat(),
                        "success": sell_result.get("success", False)
                    }
                    
                    execution_results.append(result)
                    
                    # Notify external API about trade execution
                    await self.orchestrator_client.notify_trade_execution(result)
                else:
                    # Buy order failed
                    result = {
                        "strategy_id": plan.get("strategy_id"),
                        "buy_exchange": buy_exchange,
                        "sell_exchange": sell_exchange,
                        "symbol": symbol,
                        "amount": amount,
                        "error": buy_result.get("error", "Unknown error"),
                        "timestamp": datetime.now().isoformat(),
                        "success": False
                    }
                    
                    execution_results.append(result)
                    
                    # Notify external API about failed trade
                    await self.orchestrator_client.notify_trade_execution(result)
            
            return {
                **state,
                "execution_results": execution_results
            }
        except Exception as e:
            logger.error("Error in execute node: %s", str(e))
            error_result = {
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "success": False
            }
            
            # Notify external API about error
            await self.orchestrator_client.notify_event("execution_error", error_result)
            
            return {
                **state,
                "errors": state.get("errors", []) + [{"step": "execute", "error": str(e)}],
                "execution_results": []
            }
    
    async def _reflect_node(self, state: AgentState) -> AgentState:
        """Reflect on execution results and update learning"""
        logger.debug("Reflecting on execution results")
        
        try:
            reflection = await self.reflection_engine.reflect(
                state["pool_state"],
                state["decisions"],
                state.get("execution_results", [])
            )
            
            # Report reflection to external API
            if reflection:
                await self.orchestrator_client.notify_event("reflection", {
                    "reflection": reflection,
                    "timestamp": datetime.now().isoformat()
                })
            
            return {
                **state,
                "reflection": reflection,
                # Clear transient state for next iteration
                "opportunities": [],
                "decisions": [],
                "execution_plan": [],
                "execution_results": []
            }
        except Exception as e:
            logger.error("Error in reflect node: %s", str(e))
            return {
                **state,
                "errors": state.get("errors", []) + [{"step": "reflect", "error": str(e)}],
                # Clear transient state for next iteration
                "opportunities": [],
                "decisions": [],
                "execution_plan": [],
                "execution_results": []
            }
    
    async def start(self) -> None:
        """Start the agent workflow"""
        logger.info("Starting PoolMind Agent workflow")
        
        if not self.is_initialized:
            await self.initialize()
        
        initial_state: AgentState = {
            "pool_state": {},
            "market_data": {},
            "opportunities": [],
            "decisions": [],
            "execution_results": [],
            "errors": [],
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Start the workflow
            await self.graph.arun(initial_state)
        except Exception as e:
            logger.error(f"Error in agent workflow: {str(e)}")
            raise
    
    async def stop(self) -> None:
        """Stop the agent workflow"""
        logger.info("Stopping PoolMind Agent workflow")
        
        # Cleanup logic
        try:
            # Close any open connections
            if self.rag_service:
                await self.rag_service.close()
            
            # Mark as not initialized
            self.is_initialized = False
        except Exception as e:
            logger.error(f"Error stopping agent: {str(e)}")
    
    async def run_continuous(self, interval_seconds: int = 60) -> None:
        """
        Run the agent continuously with a specified interval
        
        Args:
            interval_seconds: Interval between runs in seconds
        """
        logger.info(f"Starting continuous agent execution with {interval_seconds}s interval")
        
        if not self.is_initialized:
            await self.initialize()
        
        try:
            while True:
                start_time = time.time()
                
                try:
                    # Run one iteration of the workflow
                    await self.start()
                except Exception as e:
                    logger.error(f"Error in agent workflow iteration: {str(e)}")
                
                # Calculate time to sleep
                elapsed = time.time() - start_time
                sleep_time = max(0, interval_seconds - elapsed)
                
                if sleep_time > 0:
                    logger.info(f"Sleeping for {sleep_time:.2f}s until next iteration")
                    await asyncio.sleep(sleep_time)
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, stopping agent")
            await self.stop()
        except Exception as e:
            logger.error(f"Error in continuous execution: {str(e)}")
            await self.stop()
            raise
