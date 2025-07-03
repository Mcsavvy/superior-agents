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
            pool_state = await self.pool_context.get_current_state()
            market_data = await self.pool_context.get_market_data()
            
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
    
    async def _detect_opportunities_node(self, state: AgentState) -> AgentState:
        """Detect arbitrage opportunities from market data"""
        logger.debug("Detecting arbitrage opportunities")
        
        try:
            opportunities = await self.strategy_generator.detect_opportunities(
                state["pool_state"], 
                state["market_data"]
            )
            
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
            
            execution_results = await self.execution_optimizer.execute(
                state["execution_plan"]
            )
            
            return {
                **state,
                "execution_results": execution_results
            }
        except Exception as e:
            logger.error("Error in execute node: %s", str(e))
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
            
            logger.info("PoolMind Agent stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping PoolMind Agent: {str(e)}")
    
    async def reset(self) -> None:
        """Reset agent state"""
        logger.info("Resetting PoolMind Agent state")
        
        try:
            # Stop the agent
            await self.stop()
            
            # Re-initialize
            await self.initialize()
            
            logger.info("PoolMind Agent reset successfully")
        except Exception as e:
            logger.error(f"Error resetting PoolMind Agent: {str(e)}")
            raise
    
    def get_uptime(self) -> float:
        """Get agent uptime in seconds"""
        return time.time() - self.start_time
    
    async def observe(self, market_conditions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Observe market conditions
        
        Args:
            market_conditions: List of market conditions
            
        Returns:
            Observation result
        """
        self.last_activity_time = time.time()
        
        try:
            # Update pool context with market conditions
            await self.pool_context.update_market_data(market_conditions)
            
            # Detect opportunities
            opportunities = await self.strategy_generator.detect_opportunities(
                await self.pool_context.get_current_state(),
                await self.pool_context.get_market_data()
            )
            
            return {
                "success": True,
                "opportunities_detected": len(opportunities),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error in observe: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_detected_opportunities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get detected arbitrage opportunities
        
        Args:
            limit: Maximum number of opportunities to return
            
        Returns:
            List of opportunities
        """
        try:
            opportunities = await self.strategy_generator.get_recent_opportunities(limit)
            return opportunities
        except Exception as e:
            logger.error(f"Error getting opportunities: {str(e)}")
            return []
    
    async def generate_strategy(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a trading strategy for an opportunity
        
        Args:
            opportunity: Arbitrage opportunity
            
        Returns:
            Trading strategy
        """
        self.last_activity_time = time.time()
        
        try:
            # Get current state
            pool_state = await self.pool_context.get_current_state()
            market_data = await self.pool_context.get_market_data()
            
            # Generate strategy
            strategies = await self.strategy_generator.generate_strategy(
                pool_state,
                market_data,
                [opportunity]
            )
            
            if not strategies:
                return {}
            
            # Return first strategy
            return strategies[0]
        except Exception as e:
            logger.error(f"Error generating strategy: {str(e)}")
            return {}
    
    async def assess_risk(self, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess risk for a trading strategy
        
        Args:
            strategy: Trading strategy
            
        Returns:
            Risk assessment
        """
        self.last_activity_time = time.time()
        
        try:
            # Get current state
            pool_state = await self.pool_context.get_current_state()
            
            # Assess risk
            risk_assessments = await self.risk_assessor.assess_strategies(
                pool_state,
                [strategy]
            )
            
            if not risk_assessments:
                return {}
            
            # Return first risk assessment
            return risk_assessments[0]
        except Exception as e:
            logger.error(f"Error assessing risk: {str(e)}")
            return {}
    
    async def optimize_execution(self, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize execution for a trading strategy
        
        Args:
            strategy: Trading strategy
            
        Returns:
            Optimized execution plan
        """
        self.last_activity_time = time.time()
        
        try:
            # Get current state
            pool_state = await self.pool_context.get_current_state()
            
            # Optimize execution
            execution_plan = await self.execution_optimizer.optimize(
                pool_state,
                [strategy]
            )
            
            if not execution_plan:
                return {}
            
            # Return first execution plan
            return execution_plan[0]
        except Exception as e:
            logger.error(f"Error optimizing execution: {str(e)}")
            return {}
    
    async def execute(self, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a trading strategy
        
        Args:
            strategy: Trading strategy
            
        Returns:
            Execution result
        """
        self.last_activity_time = time.time()
        
        try:
            # Execute strategy
            execution_results = await self.execution_optimizer.execute([strategy])
            
            if not execution_results:
                return {}
            
            # Return first execution result
            return execution_results[0]
        except Exception as e:
            logger.error(f"Error executing strategy: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_execution_result(self, strategy_id: str) -> Dict[str, Any]:
        """
        Get execution result for a strategy
        
        Args:
            strategy_id: Strategy ID
            
        Returns:
            Execution result
        """
        try:
            # Get execution result from orchestrator
            result = await self.orchestrator_client.get_execution_result(strategy_id)
            return result
        except Exception as e:
            logger.error(f"Error getting execution result: {str(e)}")
            return {}
    
    async def reflect(self, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reflect on execution result
        
        Args:
            execution_result: Execution result
            
        Returns:
            Reflection insight
        """
        self.last_activity_time = time.time()
        
        try:
            # Get current state
            pool_state = await self.pool_context.get_current_state()
            
            # Reflect on execution
            reflection = await self.reflection_engine.reflect(
                pool_state,
                [execution_result.get("strategy", {})],
                [execution_result]
            )
            
            return reflection
        except Exception as e:
            logger.error(f"Error reflecting on execution: {str(e)}")
            return {}
    
    async def run_full_cycle(self, market_conditions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run full agent cycle
        
        Args:
            market_conditions: List of market conditions
            
        Returns:
            Cycle result
        """
        self.last_activity_time = time.time()
        
        try:
            # Observe
            observe_result = await self.observe(market_conditions)
            
            if not observe_result.get("success", False):
                return {"success": False, "error": observe_result.get("error", "Observation failed")}
            
            # Get opportunities
            opportunities = await self.get_detected_opportunities(limit=1)
            
            if not opportunities:
                return {"success": True, "message": "No opportunities detected"}
            
            # Generate strategy
            strategy = await self.generate_strategy(opportunities[0])
            
            if not strategy:
                return {"success": True, "message": "No viable strategy generated"}
            
            # Assess risk
            risk_assessment = await self.assess_risk(strategy)
            
            if not risk_assessment.get("proceed", False):
                return {"success": True, "message": "Strategy rejected by risk assessment"}
            
            # Optimize execution
            optimized_strategy = await self.optimize_execution(strategy)
            
            if not optimized_strategy:
                return {"success": True, "message": "Failed to optimize execution"}
            
            # Execute
            execution_result = await self.execute(optimized_strategy)
            
            if not execution_result.get("success", False):
                return {"success": True, "message": "Execution failed", "error": execution_result.get("error")}
            
            # Reflect
            reflection = await self.reflect(execution_result)
            
            return {
                "success": True,
                "strategy": strategy,
                "risk_assessment": risk_assessment,
                "execution_result": execution_result,
                "reflection": reflection
            }
        except Exception as e:
            logger.error(f"Error running full cycle: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def update_config(self, config_updates: Dict[str, Any]) -> bool:
        """
        Update agent configuration
        
        Args:
            config_updates: Configuration updates
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update config
            success = self.config.update(config_updates)
            
            if success:
                # Propagate config updates to components
                if self.pool_context:
                    await self.pool_context.update_config(self.config)
                if self.strategy_generator:
                    await self.strategy_generator.update_config(self.config)
                if self.risk_assessor:
                    await self.risk_assessor.update_config(self.config)
                if self.execution_optimizer:
                    await self.execution_optimizer.update_config(self.config)
                if self.reflection_engine:
                    await self.reflection_engine.update_config(self.config)
                if self.llm_service:
                    await self.llm_service.update_config(self.config)
                if self.rag_service:
                    await self.rag_service.update_config(self.config)
                
                logger.info("Agent configuration successfully updated")
            
            return success
        except Exception as e:
            logger.error(f"Error updating config: {str(e)}")
            return False
