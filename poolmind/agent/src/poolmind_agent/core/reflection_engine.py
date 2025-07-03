"""
Reflection Engine - Analyzes trade outcomes and improves future strategies
"""
from typing import Dict, List, Any, Optional
import logging
import asyncio
from datetime import datetime

from pydantic import BaseModel

from poolmind_agent.utils.config import AgentConfig
from poolmind_agent.services.llm_service import LLMService
from poolmind_agent.services.rag_service import RAGService

logger = logging.getLogger(__name__)

class ReflectionEngine:
    """
    Reflection & Learning Loop that analyzes trade outcomes and
    adjusts strategies based on performance.
    """
    
    def __init__(self, config: AgentConfig):
        """
        Initialize the Reflection Engine
        
        Args:
            config: Agent configuration
        """
        self.config = config
        self.llm_service = LLMService(config)
        self.rag_service = RAGService(config)
        
        logger.info("Reflection Engine initialized")
        
    async def update_config(self, config_updates: Dict[str, Any]) -> bool:
        """
        Update the reflection engine configuration
        
        Args:
            config_updates: Dictionary or AgentConfig with configuration updates
            
        Returns:
            bool: True if update was successful
        """
        try:
            # Update local config reference
            self.config = config_updates
            
            # Update services with new config
            await self.llm_service.update_config(self.config)
            await self.rag_service.update_config(self.config)
            
            logger.info("Reflection Engine configuration updated")
            return True
                
        except Exception as e:
            logger.error(f"Error updating Reflection Engine configuration: {str(e)}")
            return False
    
    async def reflect(self, 
                    pool_state: Dict[str, Any], 
                    strategies: List[Dict[str, Any]],
                    execution_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Reflect on execution results and update learning
        
        Args:
            pool_state: Current pool state
            strategies: List of trading strategies
            execution_results: List of execution results
            
        Returns:
            Reflection results and insights
        """
        logger.debug("Reflecting on execution results")
        
        try:
            # If no executions, just return empty reflection
            if not execution_results:
                logger.info("No execution results to reflect on")
                return {
                    "insights": [],
                    "strategy_adjustments": [],
                    "performance_metrics": {},
                    "timestamp": datetime.now().isoformat()
                }
            
            # Analyze trade outcomes
            trade_analysis = await self._analyze_trades(execution_results)
            
            # Store outcomes in RAG for future reference
            await self._store_outcomes(pool_state, strategies, execution_results)
            
            # Generate insights using LLM
            insights = await self._generate_insights(pool_state, strategies, execution_results, trade_analysis)
            
            # Generate strategy adjustments
            strategy_adjustments = await self._generate_strategy_adjustments(insights, trade_analysis)
            
            # Calculate performance metrics
            performance_metrics = self._calculate_performance_metrics(execution_results)
            
            reflection = {
                "trade_analysis": trade_analysis,
                "insights": insights,
                "strategy_adjustments": strategy_adjustments,
                "performance_metrics": performance_metrics,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info("Reflection completed successfully")
            return reflection
            
        except Exception as e:
            logger.error(f"Error in reflection: {str(e)}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _analyze_trades(self, execution_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze trade outcomes
        
        Args:
            execution_results: List of execution results
            
        Returns:
            Trade analysis results
        """
        try:
            # Count successful and failed trades
            successful_trades = [r for r in execution_results if r.get("success", False)]
            failed_trades = [r for r in execution_results if not r.get("success", False)]
            
            # Calculate profit metrics
            total_profit = sum(r.get("actual_profit", 0) for r in successful_trades)
            total_expected_profit = sum(r.get("expected_profit", 0) for r in successful_trades)
            profit_difference = total_profit - total_expected_profit
            
            # Calculate average slippage
            buy_slippages = []
            sell_slippages = []
            
            for result in successful_trades:
                plan = result.get("plan", {})
                buy_result = result.get("buy_result", {})
                sell_result = result.get("sell_result", {})
                
                # Calculate buy slippage
                planned_buy_price = plan.get("buy_price", 0)
                actual_buy_price = buy_result.get("price", 0)
                
                if planned_buy_price > 0 and actual_buy_price > 0:
                    buy_slippage = abs(actual_buy_price - planned_buy_price) / planned_buy_price
                    buy_slippages.append(buy_slippage)
                
                # Calculate sell slippage
                planned_sell_price = plan.get("sell_price", 0)
                actual_sell_price = sell_result.get("price", 0)
                
                if planned_sell_price > 0 and actual_sell_price > 0:
                    sell_slippage = abs(actual_sell_price - planned_sell_price) / planned_sell_price
                    sell_slippages.append(sell_slippage)
            
            avg_buy_slippage = sum(buy_slippages) / len(buy_slippages) if buy_slippages else 0
            avg_sell_slippage = sum(sell_slippages) / len(sell_slippages) if sell_slippages else 0
            
            # Analyze failure reasons
            failure_reasons = {}
            
            for result in failed_trades:
                reason = result.get("error", "Unknown error")
                stage = result.get("stage", "unknown")
                
                key = f"{stage}: {reason}"
                failure_reasons[key] = failure_reasons.get(key, 0) + 1
            
            # Analyze execution times
            execution_times = []
            
            for result in successful_trades:
                plan_time = datetime.fromisoformat(result.get("plan", {}).get("timestamp", datetime.now().isoformat()))
                result_time = datetime.fromisoformat(result.get("timestamp", datetime.now().isoformat()))
                
                execution_time = (result_time - plan_time).total_seconds()
                execution_times.append(execution_time)
            
            avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
            
            # Create analysis result
            analysis = {
                "total_trades": len(execution_results),
                "successful_trades": len(successful_trades),
                "failed_trades": len(failed_trades),
                "success_rate": len(successful_trades) / len(execution_results) if execution_results else 0,
                "total_profit": total_profit,
                "total_expected_profit": total_expected_profit,
                "profit_difference": profit_difference,
                "profit_accuracy": total_profit / total_expected_profit if total_expected_profit > 0 else 0,
                "avg_buy_slippage": avg_buy_slippage,
                "avg_sell_slippage": avg_sell_slippage,
                "failure_reasons": failure_reasons,
                "avg_execution_time": avg_execution_time
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing trades: {str(e)}")
            return {}
    
    async def _store_outcomes(self, 
                            pool_state: Dict[str, Any],
                            strategies: List[Dict[str, Any]],
                            execution_results: List[Dict[str, Any]]) -> None:
        """
        Store trade outcomes in RAG for future reference
        
        Args:
            pool_state: Current pool state
            strategies: List of trading strategies
            execution_results: List of execution results
        """
        try:
            # Only store successful trades
            successful_trades = [r for r in execution_results if r.get("success", False)]
            
            for result in successful_trades:
                plan = result.get("plan", {})
                opportunity = plan.get("opportunity", {})
                
                # Create document for RAG
                document = {
                    "pool_size": pool_state.get("total_value", 0),
                    "participant_count": pool_state.get("participant_count", 0),
                    "liquidity_ratio": pool_state.get("liquidity_reserve", 0) / pool_state.get("total_value", 1),
                    "pair": plan.get("pair", ""),
                    "spread_size": opportunity.get("price_diff_pct", 0),
                    "volatility": 0,  # Would calculate from market data in production
                    "outcome": {
                        "profit": result.get("actual_profit", 0),
                        "execution_time": result.get("execution_time", 0),
                        "slippage": (result.get("buy_result", {}).get("slippage", 0) + 
                                    result.get("sell_result", {}).get("slippage", 0)) / 2
                    }
                }
                
                # Store in RAG
                await self.rag_service.store_trade_outcome(document)
            
            logger.info(f"Stored {len(successful_trades)} trade outcomes in RAG")
            
        except Exception as e:
            logger.error(f"Error storing outcomes: {str(e)}")
    
    async def _generate_insights(self,
                               pool_state: Dict[str, Any],
                               strategies: List[Dict[str, Any]],
                               execution_results: List[Dict[str, Any]],
                               trade_analysis: Dict[str, Any]) -> List[str]:
        """
        Generate insights using LLM
        
        Args:
            pool_state: Current pool state
            strategies: List of trading strategies
            execution_results: List of execution results
            trade_analysis: Trade analysis results
            
        Returns:
            List of insights
        """
        try:
            # Skip if no successful trades
            if not trade_analysis.get("successful_trades", 0):
                return ["No successful trades to generate insights from"]
            
            # Prepare prompt for LLM
            prompt = self._prepare_insights_prompt(pool_state, strategies, execution_results, trade_analysis)
            
            # Call LLM service
            response = await self.llm_service.generate_insights(prompt)
            
            if not response:
                logger.warning("LLM returned empty response for insights")
                return ["Failed to generate insights from LLM"]
            
            # Parse insights from response
            insights = self._parse_insights_response(response)
            
            logger.info(f"Generated {len(insights)} insights")
            return insights
            
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            return [f"Error generating insights: {str(e)}"]
    
    def _prepare_insights_prompt(self,
                               pool_state: Dict[str, Any],
                               strategies: List[Dict[str, Any]],
                               execution_results: List[Dict[str, Any]],
                               trade_analysis: Dict[str, Any]) -> str:
        """
        Prepare prompt for LLM insights generation
        
        Args:
            pool_state: Current pool state
            strategies: List of trading strategies
            execution_results: List of execution results
            trade_analysis: Trade analysis results
            
        Returns:
            Prompt string for LLM
        """
        # Format trade analysis
        analysis_str = f"""
Trade Analysis:
- Total Trades: {trade_analysis.get('total_trades', 0)}
- Successful Trades: {trade_analysis.get('successful_trades', 0)}
- Failed Trades: {trade_analysis.get('failed_trades', 0)}
- Success Rate: {trade_analysis.get('success_rate', 0) * 100:.2f}%
- Total Profit: ${trade_analysis.get('total_profit', 0):.2f}
- Expected Profit: ${trade_analysis.get('total_expected_profit', 0):.2f}
- Profit Difference: ${trade_analysis.get('profit_difference', 0):.2f}
- Profit Accuracy: {trade_analysis.get('profit_accuracy', 0) * 100:.2f}%
- Average Buy Slippage: {trade_analysis.get('avg_buy_slippage', 0) * 100:.2f}%
- Average Sell Slippage: {trade_analysis.get('avg_sell_slippage', 0) * 100:.2f}%
- Average Execution Time: {trade_analysis.get('avg_execution_time', 0):.2f}s
"""
        
        # Format failure reasons
        failure_reasons = trade_analysis.get('failure_reasons', {})
        failure_str = ""
        
        for reason, count in failure_reasons.items():
            failure_str += f"- {reason}: {count}\n"
        
        if failure_str:
            analysis_str += f"\nFailure Reasons:\n{failure_str}"
        
        # Format successful trades (limit to 3 for brevity)
        successful_trades = [r for r in execution_results if r.get("success", False)][:3]
        trades_str = ""
        
        for i, result in enumerate(successful_trades):
            plan = result.get("plan", {})
            buy_result = result.get("buy_result", {})
            sell_result = result.get("sell_result", {})
            
            trades_str += f"""
Trade {i+1}:
- Pair: {plan.get('pair', '')}
- Buy Exchange: {plan.get('buy_exchange', '')}
- Sell Exchange: {plan.get('sell_exchange', '')}
- Expected Profit: ${plan.get('expected_profit', 0):.2f} ({plan.get('expected_profit_pct', 0):.2f}%)
- Actual Profit: ${result.get('actual_profit', 0):.2f} ({result.get('actual_profit_pct', 0):.2f}%)
- Buy Price: Planned ${plan.get('buy_price', 0):.8f}, Actual ${buy_result.get('price', 0):.8f}
- Sell Price: Planned ${plan.get('sell_price', 0):.8f}, Actual ${sell_result.get('price', 0):.8f}
"""
        
        # Build prompt
        prompt = f"""
Analyze the following arbitrage trading results and generate insights:

Pool Information:
- Total Value: ${pool_state.get('total_value', 0):,.2f}
- Participant Count: {pool_state.get('participant_count', 0)}
- Liquidity Reserve: ${pool_state.get('liquidity_reserve', 0):,.2f}

{analysis_str}

Sample Trades:
{trades_str}

Please provide 3-5 specific insights about:
1. Slippage patterns and how to improve predictions
2. Exchange-specific performance differences
3. Profit prediction accuracy
4. Execution timing optimization
5. Risk assessment effectiveness

For each insight, include specific observations from the data and actionable recommendations.
"""
        
        return prompt
    
    def _parse_insights_response(self, response: str) -> List[str]:
        """
        Parse LLM response into a list of insights
        
        Args:
            response: LLM response text
            
        Returns:
            List of insights
        """
        try:
            insights = []
            current_insight = ""
            
            for line in response.split("\n"):
                line = line.strip()
                
                if not line:
                    if current_insight:
                        insights.append(current_insight)
                        current_insight = ""
                    continue
                
                # Check if this is a new insight
                if line.startswith("Insight") or line.startswith("1.") or line.startswith("2.") or line.startswith("3.") or line.startswith("4.") or line.startswith("5."):
                    if current_insight:
                        insights.append(current_insight)
                        current_insight = line
                    else:
                        current_insight = line
                else:
                    if current_insight:
                        current_insight += " " + line
                    else:
                        current_insight = line
            
            # Add the last insight if any
            if current_insight:
                insights.append(current_insight)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error parsing insights response: {str(e)}")
            return [response]  # Return the full response as a single insight
    
    async def _generate_strategy_adjustments(self,
                                          insights: List[str],
                                          trade_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate strategy adjustments based on insights
        
        Args:
            insights: List of insights
            trade_analysis: Trade analysis results
            
        Returns:
            List of strategy adjustments
        """
        try:
            adjustments = []
            
            # Slippage adjustment
            avg_buy_slippage = trade_analysis.get("avg_buy_slippage", 0)
            avg_sell_slippage = trade_analysis.get("avg_sell_slippage", 0)
            
            if avg_buy_slippage > 0 or avg_sell_slippage > 0:
                adjustments.append({
                    "parameter": "slippage_estimate",
                    "adjustment": "increase",
                    "value": max(avg_buy_slippage, avg_sell_slippage) * 1.2,  # Add 20% buffer
                    "reason": "Actual slippage higher than estimated"
                })
            
            # Profit prediction adjustment
            profit_accuracy = trade_analysis.get("profit_accuracy", 0)
            
            if profit_accuracy < 0.9:  # Less than 90% accurate
                adjustments.append({
                    "parameter": "profit_threshold",
                    "adjustment": "increase",
                    "value": self.config.min_profit_threshold * (2 - profit_accuracy),  # Adjust based on accuracy
                    "reason": "Profit predictions less accurate than expected"
                })
            
            # Execution time adjustment
            avg_execution_time = trade_analysis.get("avg_execution_time", 0)
            
            if avg_execution_time > 10:  # More than 10 seconds
                adjustments.append({
                    "parameter": "timeout_seconds",
                    "adjustment": "increase",
                    "value": avg_execution_time * 1.5,  # Add 50% buffer
                    "reason": "Execution taking longer than expected"
                })
            
            # Success rate adjustment
            success_rate = trade_analysis.get("success_rate", 0)
            
            if success_rate < 0.8:  # Less than 80% success
                adjustments.append({
                    "parameter": "risk_threshold",
                    "adjustment": "decrease",
                    "value": self.config.max_risk_threshold * 0.9,  # Reduce by 10%
                    "reason": "Low success rate indicates higher risk"
                })
            
            return adjustments
            
        except Exception as e:
            logger.error(f"Error generating strategy adjustments: {str(e)}")
            return []
    
    def _calculate_performance_metrics(self, execution_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate performance metrics
        
        Args:
            execution_results: List of execution results
            
        Returns:
            Performance metrics
        """
        try:
            # Count successful and failed trades
            successful_trades = [r for r in execution_results if r.get("success", False)]
            failed_trades = [r for r in execution_results if not r.get("success", False)]
            
            # Calculate profit metrics
            total_profit = sum(r.get("actual_profit", 0) for r in successful_trades)
            
            # Calculate total position size
            total_position_size = sum(r.get("plan", {}).get("position_size", 0) for r in execution_results)
            
            # Calculate ROI
            roi = (total_profit / total_position_size) * 100.0 if total_position_size > 0 else 0
            
            # Calculate opportunity metrics
            opportunity_count = len(execution_results)
            success_rate = len(successful_trades) / opportunity_count if opportunity_count > 0 else 0
            
            # Calculate average profit per trade
            avg_profit_per_trade = total_profit / len(successful_trades) if successful_trades else 0
            
            # Calculate average profit percentage
            avg_profit_pct = sum(r.get("actual_profit_pct", 0) for r in successful_trades) / len(successful_trades) if successful_trades else 0
            
            metrics = {
                "total_profit": total_profit,
                "roi": roi,
                "opportunity_count": opportunity_count,
                "success_rate": success_rate,
                "avg_profit_per_trade": avg_profit_per_trade,
                "avg_profit_pct": avg_profit_pct
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {str(e)}")
            return {}
