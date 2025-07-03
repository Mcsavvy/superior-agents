"""
Risk Assessor - Evaluates risk of trading strategies
"""
from typing import Dict, List, Any, Optional
import logging
import asyncio
from datetime import datetime

from pydantic import BaseModel

from poolmind_agent.utils.config import AgentConfig
from poolmind_agent.services.llm_service import LLMService

logger = logging.getLogger(__name__)

class RiskAssessor:
    """
    Risk Assessment Module that evaluates trading strategies against
    multiple risk dimensions.
    """
    
    def __init__(self, config: AgentConfig):
        """
        Initialize the Risk Assessor
        
        Args:
            config: Agent configuration
        """
        self.config = config
        self.llm_service = LLMService(config)
        
        logger.info("Risk Assessor initialized")
        
    async def update_config(self, config_updates: Dict[str, Any]) -> bool:
        """
        Update the risk assessor configuration
        
        Args:
            config_updates: Dictionary or AgentConfig with configuration updates
            
        Returns:
            bool: True if update was successful
        """
        try:
            # Update local config reference
            self.config = config_updates
            
            # Update LLM service with new config
            await self.llm_service.update_config(self.config)
            
            logger.info("Risk Assessor configuration updated")
            return True
                
        except Exception as e:
            logger.error(f"Error updating Risk Assessor configuration: {str(e)}")
            return False
    
    async def assess_strategies(self, 
                              pool_state: Dict[str, Any], 
                              strategies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Assess risk for multiple trading strategies
        
        Args:
            pool_state: Current pool state
            strategies: List of trading strategies to assess
            
        Returns:
            List of risk assessments for each strategy
        """
        logger.debug(f"Assessing risk for {len(strategies)} strategies")
        
        if not strategies:
            logger.info("No strategies to assess")
            return []
        
        try:
            # Process strategies in parallel
            tasks = [
                self.assess_strategy(pool_state, strategy)
                for strategy in strategies
            ]
            
            assessments = await asyncio.gather(*tasks)
            
            logger.info(f"Completed risk assessment for {len(assessments)} strategies")
            return assessments
            
        except Exception as e:
            logger.error(f"Error assessing strategies: {str(e)}")
            # Return default assessments
            return [self._default_assessment(strategy) for strategy in strategies]
    
    async def assess_strategy(self, 
                            pool_state: Dict[str, Any], 
                            strategy: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess risk for a single trading strategy
        
        Args:
            pool_state: Current pool state
            strategy: Trading strategy to assess
            
        Returns:
            Risk assessment for the strategy
        """
        try:
            # Extract key metrics
            opportunity = strategy.get("opportunity", {})
            position_size_pct = strategy.get("position_size_pct", 1.0)
            
            # Calculate position size in absolute terms
            available_capital = max(0, pool_state.get("total_value", 0) - pool_state.get("liquidity_reserve", 0))
            position_size = available_capital * (position_size_pct / 100.0)
            
            # Calculate risk dimensions
            pool_impact_score = await self._calculate_pool_impact(pool_state, position_size)
            liquidity_strain_index = await self._calculate_liquidity_strain(pool_state, strategy)
            participant_risk = await self._calculate_participant_risk(pool_state)
            exchange_failure_prob = await self._calculate_exchange_failure_prob(strategy)
            
            # Calculate overall risk score
            overall_risk = self._calculate_overall_risk(
                pool_impact_score,
                liquidity_strain_index,
                participant_risk,
                exchange_failure_prob
            )
            
            # Determine if strategy should proceed
            proceed = overall_risk <= self.config.max_risk_threshold
            
            assessment = {
                "pool_impact_score": pool_impact_score,
                "liquidity_strain_index": liquidity_strain_index,
                "participant_risk": participant_risk,
                "exchange_failure_prob": exchange_failure_prob,
                "overall_risk": overall_risk,
                "proceed": proceed,
                "timestamp": datetime.now().isoformat()
            }
            
            # If using LLM for risk assessment, enhance with LLM insights
            if self.config.use_llm_for_risk:
                llm_assessment = await self._get_llm_risk_assessment(pool_state, strategy, assessment)
                if llm_assessment:
                    assessment.update(llm_assessment)
            
            return assessment
            
        except Exception as e:
            logger.error(f"Error assessing strategy: {str(e)}")
            return self._default_assessment(strategy)
    
    async def _calculate_pool_impact(self, 
                                   pool_state: Dict[str, Any], 
                                   position_size: float) -> float:
        """
        Calculate the impact of the position on the pool
        
        Args:
            pool_state: Current pool state
            position_size: Size of the position in absolute terms
            
        Returns:
            Pool impact score (1-10)
        """
        try:
            total_value = pool_state.get("total_value", 0)
            
            if total_value <= 0:
                return 10.0  # Maximum impact if pool is empty
            
            # Calculate position size as percentage of total pool
            position_pct = (position_size / total_value) * 100.0
            
            # Map percentage to score (1-10)
            # 0% -> 1, 10%+ -> 10
            impact_score = 1.0 + (position_pct / 10.0) * 9.0
            
            # Cap at 10
            impact_score = min(10.0, impact_score)
            
            return impact_score
            
        except Exception as e:
            logger.error(f"Error calculating pool impact: {str(e)}")
            return 5.0  # Default to medium impact
    
    async def _calculate_liquidity_strain(self, 
                                        pool_state: Dict[str, Any], 
                                        strategy: Dict[str, Any]) -> float:
        """
        Calculate the strain on liquidity reserves
        
        Args:
            pool_state: Current pool state
            strategy: Trading strategy
            
        Returns:
            Liquidity strain index (0-1)
        """
        try:
            liquidity_reserve = pool_state.get("liquidity_reserve", 0)
            withdrawal_forecast = pool_state.get("withdrawal_forecast", {})
            expected_withdrawals = withdrawal_forecast.get("expected", 0)
            
            # Calculate position size
            available_capital = max(0, pool_state.get("total_value", 0) - liquidity_reserve)
            position_size_pct = strategy.get("position_size_pct", 1.0)
            position_size = available_capital * (position_size_pct / 100.0)
            
            if liquidity_reserve <= 0:
                return 1.0  # Maximum strain if no reserves
            
            # Calculate strain as ratio of position size to reserves minus expected withdrawals
            effective_reserve = max(0, liquidity_reserve - expected_withdrawals)
            
            if effective_reserve <= 0:
                return 1.0  # Maximum strain if no effective reserves
            
            strain_index = position_size / effective_reserve
            
            # Cap at 1.0
            strain_index = min(1.0, strain_index)
            
            return strain_index
            
        except Exception as e:
            logger.error(f"Error calculating liquidity strain: {str(e)}")
            return 0.5  # Default to medium strain
    
    async def _calculate_participant_risk(self, pool_state: Dict[str, Any]) -> float:
        """
        Calculate risk based on participant behavior
        
        Args:
            pool_state: Current pool state
            
        Returns:
            Participant risk score (1-10)
        """
        try:
            participant_metrics = pool_state.get("participant_metrics", {})
            
            # Extract metrics
            avg_holding_period = participant_metrics.get("avg_holding_period_days", 30)
            withdrawal_frequency = participant_metrics.get("withdrawal_frequency", "low")
            new_participants_ratio = participant_metrics.get("new_participants_ratio", 0.1)
            
            # Calculate risk score components
            holding_risk = 10.0 - min(10.0, avg_holding_period / 10.0)
            
            withdrawal_risk = {
                "low": 2.0,
                "medium": 5.0,
                "high": 8.0
            }.get(withdrawal_frequency, 5.0)
            
            # New participants are riskier (more unpredictable)
            new_participant_risk = new_participants_ratio * 10.0
            
            # Combine components with weights
            risk_score = (
                holding_risk * 0.4 +
                withdrawal_risk * 0.4 +
                new_participant_risk * 0.2
            )
            
            return risk_score
            
        except Exception as e:
            logger.error(f"Error calculating participant risk: {str(e)}")
            return 5.0  # Default to medium risk
    
    async def _calculate_exchange_failure_prob(self, strategy: Dict[str, Any]) -> float:
        """
        Calculate probability of exchange failure
        
        Args:
            strategy: Trading strategy
            
        Returns:
            Exchange failure probability (0-1)
        """
        try:
            opportunity = strategy.get("opportunity", {})
            
            # Get exchanges
            buy_exchange = opportunity.get("buy_exchange", "")
            sell_exchange = opportunity.get("sell_exchange", "")
            
            # Get failure probabilities from config
            buy_failure_prob = self.config.exchange_failure_probs.get(buy_exchange, 0.01)
            sell_failure_prob = self.config.exchange_failure_probs.get(sell_exchange, 0.01)
            
            # Calculate combined probability (either exchange can fail)
            # P(A or B) = P(A) + P(B) - P(A and B)
            # Assuming independence: P(A and B) = P(A) * P(B)
            combined_prob = buy_failure_prob + sell_failure_prob - (buy_failure_prob * sell_failure_prob)
            
            return combined_prob
            
        except Exception as e:
            logger.error(f"Error calculating exchange failure probability: {str(e)}")
            return 0.05  # Default to 5% failure probability
    
    def _calculate_overall_risk(self,
                              pool_impact_score: float,
                              liquidity_strain_index: float,
                              participant_risk: float,
                              exchange_failure_prob: float) -> float:
        """
        Calculate overall risk score
        
        Args:
            pool_impact_score: Impact on the pool (1-10)
            liquidity_strain_index: Strain on liquidity (0-1)
            participant_risk: Risk from participant behavior (1-10)
            exchange_failure_prob: Probability of exchange failure (0-1)
            
        Returns:
            Overall risk score (1-10)
        """
        try:
            # Normalize exchange failure probability to 1-10 scale
            exchange_risk = exchange_failure_prob * 10.0
            
            # Normalize liquidity strain to 1-10 scale
            liquidity_risk = liquidity_strain_index * 10.0
            
            # Combine with weights
            overall_risk = (
                pool_impact_score * 0.3 +
                liquidity_risk * 0.3 +
                participant_risk * 0.2 +
                exchange_risk * 0.2
            )
            
            return overall_risk
            
        except Exception as e:
            logger.error(f"Error calculating overall risk: {str(e)}")
            return 5.0  # Default to medium risk
    
    async def _get_llm_risk_assessment(self,
                                     pool_state: Dict[str, Any],
                                     strategy: Dict[str, Any],
                                     base_assessment: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get risk assessment insights from LLM
        
        Args:
            pool_state: Current pool state
            strategy: Trading strategy
            base_assessment: Base risk assessment
            
        Returns:
            Additional risk assessment insights from LLM
        """
        try:
            # Prepare prompt for LLM
            prompt = self._prepare_risk_prompt(pool_state, strategy, base_assessment)
            
            # Call LLM service
            response = await self.llm_service.assess_risk(prompt)
            
            if not response:
                logger.warning("LLM returned empty response for risk assessment")
                return None
            
            # Parse LLM response
            llm_assessment = self._parse_risk_response(response)
            
            return llm_assessment
            
        except Exception as e:
            logger.error(f"Error getting LLM risk assessment: {str(e)}")
            return None
    
    def _prepare_risk_prompt(self,
                           pool_state: Dict[str, Any],
                           strategy: Dict[str, Any],
                           base_assessment: Dict[str, Any]) -> str:
        """
        Prepare prompt for LLM risk assessment
        
        Args:
            pool_state: Current pool state
            strategy: Trading strategy
            base_assessment: Base risk assessment
            
        Returns:
            Prompt string for LLM
        """
        # Extract key metrics
        opportunity = strategy.get("opportunity", {})
        position_size_pct = strategy.get("position_size_pct", 1.0)
        
        # Build prompt
        prompt = f"""
Assess the risk of the following arbitrage trading strategy:

Pool Information:
- Total Value: ${pool_state.get('total_value', 0):,.2f}
- Liquidity Reserve: ${pool_state.get('liquidity_reserve', 0):,.2f}
- Participant Count: {pool_state.get('participant_count', 0)}

Strategy:
- Trading Pair: {opportunity.get('pair', '')}
- Buy Exchange: {opportunity.get('buy_exchange', '')}
- Sell Exchange: {opportunity.get('sell_exchange', '')}
- Position Size: {position_size_pct:.2f}% of available capital
- Estimated Profit: {opportunity.get('estimated_profit_pct', 0):.2f}%

Base Risk Assessment:
- Pool Impact Score: {base_assessment.get('pool_impact_score', 0):.2f}/10
- Liquidity Strain Index: {base_assessment.get('liquidity_strain_index', 0):.2f}
- Participant Risk: {base_assessment.get('participant_risk', 0):.2f}/10
- Exchange Failure Probability: {base_assessment.get('exchange_failure_prob', 0):.2f}
- Overall Risk: {base_assessment.get('overall_risk', 0):.2f}/10

Please provide:
1. Additional risk factors not considered in the base assessment
2. Recommendations to mitigate identified risks
3. A final recommendation (proceed/reject) with justification
"""
        
        return prompt
    
    def _parse_risk_response(self, response: str) -> Dict[str, Any]:
        """
        Parse LLM response into structured risk insights
        
        Args:
            response: LLM response text
            
        Returns:
            Structured risk insights
        """
        # Default values
        llm_assessment = {
            "additional_risk_factors": [],
            "risk_mitigation": [],
            "llm_recommendation": "proceed",
            "llm_justification": "",
            "llm_response": response
        }
        
        try:
            # Extract additional risk factors
            if "risk factor" in response.lower() or "additional risk" in response.lower():
                factors = []
                in_factors_section = False
                
                for line in response.split("\n"):
                    if "risk factor" in line.lower() or "additional risk" in line.lower():
                        in_factors_section = True
                        continue
                    
                    if in_factors_section:
                        if line.strip() and (":" in line or "-" in line or "•" in line):
                            # Extract the factor text
                            factor_text = line.split(":", 1)[-1].strip() if ":" in line else line.strip()
                            factor_text = factor_text[1:].strip() if factor_text.startswith("-") or factor_text.startswith("•") else factor_text
                            
                            if factor_text:
                                factors.append(factor_text)
                        elif line.strip() == "" and factors:
                            # Empty line after factors, end of section
                            in_factors_section = False
                
                llm_assessment["additional_risk_factors"] = factors
            
            # Extract risk mitigation recommendations
            if "mitigation" in response.lower() or "recommend" in response.lower():
                mitigations = []
                in_mitigation_section = False
                
                for line in response.split("\n"):
                    if "mitigation" in line.lower() or "recommend" in line.lower():
                        in_mitigation_section = True
                        continue
                    
                    if in_mitigation_section:
                        if line.strip() and (":" in line or "-" in line or "•" in line):
                            # Extract the mitigation text
                            mitigation_text = line.split(":", 1)[-1].strip() if ":" in line else line.strip()
                            mitigation_text = mitigation_text[1:].strip() if mitigation_text.startswith("-") or mitigation_text.startswith("•") else mitigation_text
                            
                            if mitigation_text:
                                mitigations.append(mitigation_text)
                        elif line.strip() == "" and mitigations:
                            # Empty line after mitigations, end of section
                            in_mitigation_section = False
                
                llm_assessment["risk_mitigation"] = mitigations
            
            # Extract recommendation
            if "recommend" in response.lower() or "final" in response.lower():
                for line in response.split("\n"):
                    if "recommend" in line.lower() or "final" in line.lower():
                        if "reject" in line.lower() or "do not proceed" in line.lower() or "don't proceed" in line.lower():
                            llm_assessment["llm_recommendation"] = "reject"
                        elif "proceed" in line.lower() or "approve" in line.lower() or "accept" in line.lower():
                            llm_assessment["llm_recommendation"] = "proceed"
                        
                        # Extract justification
                        if ":" in line:
                            llm_assessment["llm_justification"] = line.split(":", 1)[1].strip()
            
            return llm_assessment
            
        except Exception as e:
            logger.error(f"Error parsing risk response: {str(e)}")
            return llm_assessment
    
    def _default_assessment(self, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a default risk assessment
        
        Args:
            strategy: Trading strategy
            
        Returns:
            Default risk assessment
        """
        return {
            "pool_impact_score": 5.0,
            "liquidity_strain_index": 0.5,
            "participant_risk": 5.0,
            "exchange_failure_prob": 0.05,
            "overall_risk": 5.0,
            "proceed": self.config.max_risk_threshold >= 5.0,
            "timestamp": datetime.now().isoformat()
        }
