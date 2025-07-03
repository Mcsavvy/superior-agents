"""
Strategy Generator - Detects arbitrage opportunities and generates trading strategies
"""
from typing import Dict, List, Any, Optional
import logging
import asyncio
from datetime import datetime

from pydantic import BaseModel
import httpx

from poolmind_agent.utils.config import AgentConfig
from poolmind_agent.services.llm_service import LLMService
from poolmind_agent.services.rag_service import RAGService

logger = logging.getLogger(__name__)

class StrategyGenerator:
    """
    Multi-LLM Strategy Generator that detects arbitrage opportunities and
    generates pool-aware trading strategies.
    """
    
    def __init__(self, config: AgentConfig):
        """
        Initialize the Strategy Generator
        
        Args:
            config: Agent configuration
        """
        self.config = config
        self.llm_service = LLMService(config)
        self.rag_service = RAGService(config)
        
        # Initialize fallback system
        self._fallback_active = False
        self._fallback_until = datetime.now()
        
        logger.info("Strategy Generator initialized")
        
    async def update_config(self, config_updates: Dict[str, Any]) -> bool:
        """
        Update the strategy generator configuration
        
        Args:
            config_updates: Dictionary of configuration updates
            
        Returns:
            bool: True if update was successful
        """
        try:
            if isinstance(config_updates, dict):
                # Update local config reference
                self.config = config_updates
                
                # Update services with new config
                await self.llm_service.update_config(self.config)
                await self.rag_service.update_config(self.config)
                
                logger.info("Strategy Generator configuration updated")
                return True
            else:
                logger.warning("Invalid configuration update format")
                return False
                
        except Exception as e:
            logger.error(f"Error updating Strategy Generator configuration: {str(e)}")
            return False
    
    async def detect_opportunities(self, 
                                  pool_state: Dict[str, Any], 
                                  market_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect arbitrage opportunities from market data
        
        Args:
            pool_state: Current pool state
            market_data: Current market data
            
        Returns:
            List of detected opportunities
        """
        logger.debug("Detecting arbitrage opportunities")
        
        try:
            # Extract exchange data
            exchange_data = market_data.get("exchange_data", {})
            
            if not exchange_data:
                logger.warning("No exchange data available")
                return []
            
            # Detect price differences across exchanges
            opportunities = await self._detect_price_differences(exchange_data)
            
            # Filter opportunities based on minimum profit threshold
            min_profit_threshold = self.config.min_profit_threshold
            filtered_opportunities = [
                opp for opp in opportunities
                if opp.get("estimated_profit_pct", 0) >= min_profit_threshold
            ]
            
            logger.info(f"Detected {len(filtered_opportunities)} opportunities above threshold")
            return filtered_opportunities
            
        except Exception as e:
            logger.error(f"Error detecting opportunities: {str(e)}")
            return []
    
    async def _detect_price_differences(self, exchange_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect price differences across exchanges
        
        Args:
            exchange_data: Data from various exchanges
            
        Returns:
            List of opportunities with price differences
        """
        opportunities = []
        
        # Get all trading pairs
        all_pairs = set()
        for exchange, data in exchange_data.items():
            all_pairs.update(data.keys())
        
        # For each pair, check prices across exchanges
        for pair in all_pairs:
            # Get exchanges that have this pair
            exchanges_with_pair = [
                exchange for exchange, data in exchange_data.items()
                if pair in data
            ]
            
            if len(exchanges_with_pair) < 2:
                continue  # Need at least 2 exchanges for arbitrage
            
            # Get prices for this pair across exchanges
            prices = {
                exchange: exchange_data[exchange][pair].get("price", 0)
                for exchange in exchanges_with_pair
            }
            
            # Find min and max prices
            min_price_exchange = min(prices.items(), key=lambda x: x[1])
            max_price_exchange = max(prices.items(), key=lambda x: x[1])
            
            min_price = min_price_exchange[1]
            max_price = max_price_exchange[1]
            
            if min_price <= 0:
                continue  # Skip invalid prices
            
            # Calculate price difference percentage
            price_diff_pct = ((max_price - min_price) / min_price) * 100
            
            # Calculate estimated profit after fees
            buy_fee = self.config.exchange_fees.get(min_price_exchange[0], 0.1)
            sell_fee = self.config.exchange_fees.get(max_price_exchange[0], 0.1)
            
            estimated_profit_pct = price_diff_pct - (buy_fee + sell_fee)
            
            if estimated_profit_pct > 0:
                opportunities.append({
                    "pair": pair,
                    "buy_exchange": min_price_exchange[0],
                    "buy_price": min_price,
                    "sell_exchange": max_price_exchange[0],
                    "sell_price": max_price,
                    "price_diff_pct": price_diff_pct,
                    "estimated_profit_pct": estimated_profit_pct,
                    "timestamp": datetime.now().isoformat()
                })
        
        # Sort by estimated profit (descending)
        opportunities.sort(key=lambda x: x.get("estimated_profit_pct", 0), reverse=True)
        
        return opportunities
    
    async def generate_strategy(self, 
                               pool_state: Dict[str, Any], 
                               market_data: Dict[str, Any],
                               opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate trading strategies for detected opportunities
        
        Args:
            pool_state: Current pool state
            market_data: Current market data
            opportunities: Detected arbitrage opportunities
            
        Returns:
            List of trading strategies
        """
        logger.debug("Generating trading strategies")
        
        if not opportunities:
            logger.info("No opportunities to generate strategies for")
            return []
        
        try:
            # Check if we should use fallback system
            if self._should_use_fallback():
                logger.info("Using fallback strategy generation")
                return await self._generate_fallback_strategies(pool_state, opportunities)
            
            # Use LLM for strategy generation
            strategies = []
            
            for opportunity in opportunities:
                # Get similar historical contexts from RAG
                similar_contexts = await self.rag_service.retrieve_similar_contexts(
                    pool_state=pool_state,
                    opportunity=opportunity
                )
                
                # Generate strategy using LLM
                strategy = await self._generate_llm_strategy(
                    pool_state=pool_state,
                    opportunity=opportunity,
                    similar_contexts=similar_contexts
                )
                
                if strategy:
                    strategies.append(strategy)
            
            logger.info(f"Generated {len(strategies)} strategies")
            return strategies
            
        except Exception as e:
            logger.error(f"Error generating strategies: {str(e)}")
            self._activate_fallback()
            return await self._generate_fallback_strategies(pool_state, opportunities)
    
    async def _generate_llm_strategy(self,
                                    pool_state: Dict[str, Any],
                                    opportunity: Dict[str, Any],
                                    similar_contexts: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Generate a trading strategy using LLM
        
        Args:
            pool_state: Current pool state
            opportunity: Arbitrage opportunity
            similar_contexts: Similar historical contexts
            
        Returns:
            Trading strategy or None if generation failed
        """
        try:
            # Prepare prompt for LLM
            prompt = self._prepare_strategy_prompt(pool_state, opportunity, similar_contexts)
            
            # Call LLM service
            response = await self.llm_service.generate_strategy(prompt)
            
            if not response:
                logger.warning("LLM returned empty response")
                return None
            
            # Parse LLM response
            strategy = self._parse_strategy_response(response, opportunity)
            
            return strategy
            
        except Exception as e:
            logger.error(f"Error generating LLM strategy: {str(e)}")
            return None
    
    def _prepare_strategy_prompt(self,
                               pool_state: Dict[str, Any],
                               opportunity: Dict[str, Any],
                               similar_contexts: List[Dict[str, Any]]) -> str:
        """
        Prepare prompt for LLM strategy generation
        
        Args:
            pool_state: Current pool state
            opportunity: Arbitrage opportunity
            similar_contexts: Similar historical contexts
            
        Returns:
            Prompt string for LLM
        """
        # Extract key metrics
        total_value = pool_state.get("total_value", 0)
        liquidity_reserve = pool_state.get("liquidity_reserve", 0)
        available_capital = max(0, total_value - liquidity_reserve)
        
        # Format similar contexts
        context_str = ""
        for i, context in enumerate(similar_contexts[:3]):  # Use top 3 contexts
            outcome = context.get("outcome", {})
            context_str += f"""
Context {i+1}:
- Pool Size: ${context.get('pool_size', 0):,.2f}
- Spread Size: {context.get('spread_size', 0):.2f}%
- Profit: ${outcome.get('profit', 0):,.2f}
- Execution Time: {outcome.get('execution_time', 0):.2f}s
- Slippage: {outcome.get('slippage', 0):.2f}%
"""
        
        # Build prompt
        prompt = f"""
Generate a trading strategy for a pooled arbitrage opportunity with the following details:

Pool Information:
- Total Value: ${total_value:,.2f}
- Available Capital: ${available_capital:,.2f}
- Liquidity Reserve: ${liquidity_reserve:,.2f}
- Participant Count: {pool_state.get('participant_count', 0)}

Opportunity:
- Trading Pair: {opportunity.get('pair', '')}
- Buy Exchange: {opportunity.get('buy_exchange', '')}
- Buy Price: {opportunity.get('buy_price', 0):.8f}
- Sell Exchange: {opportunity.get('sell_exchange', '')}
- Sell Price: {opportunity.get('sell_price', 0):.8f}
- Price Difference: {opportunity.get('price_diff_pct', 0):.2f}%
- Estimated Profit: {opportunity.get('estimated_profit_pct', 0):.2f}%

Similar Historical Contexts:
{context_str}

Please provide a trading strategy that includes:
1. Position size (as percentage of available capital)
2. Risk assessment (1-10 scale)
3. Execution priority (1-10 scale)
4. Expected slippage
5. Recommended gas/fee settings
6. Circuit breaker conditions
"""
        
        return prompt
    
    def _parse_strategy_response(self, 
                               response: str, 
                               opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse LLM response into a structured strategy
        
        Args:
            response: LLM response text
            opportunity: Original opportunity
            
        Returns:
            Structured strategy dict
        """
        # Default values
        strategy = {
            "opportunity": opportunity,
            "position_size_pct": 1.0,  # Default to 1% of available capital
            "risk_score": 5,
            "execution_priority": 5,
            "expected_slippage": 0.1,
            "gas_settings": "medium",
            "circuit_breakers": {
                "max_slippage": 1.0,
                "timeout_seconds": 30
            },
            "llm_response": response,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Extract position size
            if "position size" in response.lower():
                for line in response.split("\n"):
                    if "position size" in line.lower():
                        # Try to extract percentage
                        import re
                        match = re.search(r"(\d+\.?\d*)%", line)
                        if match:
                            strategy["position_size_pct"] = float(match.group(1))
            
            # Extract risk assessment
            if "risk assessment" in response.lower():
                for line in response.split("\n"):
                    if "risk assessment" in line.lower():
                        # Try to extract score
                        import re
                        match = re.search(r"(\d+)(?:/10)?", line)
                        if match:
                            strategy["risk_score"] = int(match.group(1))
            
            # Extract execution priority
            if "execution priority" in response.lower():
                for line in response.split("\n"):
                    if "execution priority" in line.lower():
                        # Try to extract priority
                        import re
                        match = re.search(r"(\d+)(?:/10)?", line)
                        if match:
                            strategy["execution_priority"] = int(match.group(1))
            
            # Extract expected slippage
            if "expected slippage" in response.lower():
                for line in response.split("\n"):
                    if "expected slippage" in line.lower():
                        # Try to extract percentage
                        import re
                        match = re.search(r"(\d+\.?\d*)%", line)
                        if match:
                            strategy["expected_slippage"] = float(match.group(1))
            
            # Extract gas settings
            if "gas" in response.lower() or "fee" in response.lower():
                for line in response.split("\n"):
                    if "gas" in line.lower() or "fee" in line.lower():
                        if "high" in line.lower():
                            strategy["gas_settings"] = "high"
                        elif "low" in line.lower():
                            strategy["gas_settings"] = "low"
            
            # Extract circuit breaker conditions
            if "circuit breaker" in response.lower():
                for line in response.split("\n"):
                    if "slippage" in line.lower() and "circuit" in line.lower():
                        # Try to extract percentage
                        import re
                        match = re.search(r"(\d+\.?\d*)%", line)
                        if match:
                            strategy["circuit_breakers"]["max_slippage"] = float(match.group(1))
                    
                    if "timeout" in line.lower() and "circuit" in line.lower():
                        # Try to extract seconds
                        import re
                        match = re.search(r"(\d+)(?:\s*s|\s*sec|\s*seconds)?", line)
                        if match:
                            strategy["circuit_breakers"]["timeout_seconds"] = int(match.group(1))
            
            return strategy
            
        except Exception as e:
            logger.error(f"Error parsing strategy response: {str(e)}")
            return strategy
    
    def _should_use_fallback(self) -> bool:
        """Check if we should use the fallback system"""
        if self._fallback_active and datetime.now() < self._fallback_until:
            return True
        
        self._fallback_active = False
        return False
    
    def _activate_fallback(self) -> None:
        """Activate the fallback system for a period of time"""
        self._fallback_active = True
        self._fallback_until = datetime.now() + self.config.fallback_duration
        logger.warning(f"Fallback system activated until {self._fallback_until}")
    
    async def _generate_fallback_strategies(self,
                                          pool_state: Dict[str, Any],
                                          opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate strategies using fallback system
        
        Args:
            pool_state: Current pool state
            opportunities: Detected arbitrage opportunities
            
        Returns:
            List of trading strategies
        """
        logger.info("Generating fallback strategies")
        
        strategies = []
        pool_size = pool_state.get("total_value", 0)
        
        for opportunity in opportunities:
            # Simple rule-based strategy based on pool size
            if pool_size < 10000:
                strategy = {
                    "opportunity": opportunity,
                    "position_size_pct": 0.5,  # Conservative
                    "risk_score": 3,
                    "execution_priority": 3,
                    "expected_slippage": 0.2,
                    "gas_settings": "medium",
                    "circuit_breakers": {
                        "max_slippage": 0.5,
                        "timeout_seconds": 15
                    },
                    "fallback": True,
                    "timestamp": datetime.now().isoformat()
                }
            elif pool_size < 100000:
                strategy = {
                    "opportunity": opportunity,
                    "position_size_pct": 1.0,  # Moderate
                    "risk_score": 5,
                    "execution_priority": 5,
                    "expected_slippage": 0.15,
                    "gas_settings": "medium",
                    "circuit_breakers": {
                        "max_slippage": 0.75,
                        "timeout_seconds": 20
                    },
                    "fallback": True,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                strategy = {
                    "opportunity": opportunity,
                    "position_size_pct": 2.0,  # Aggressive
                    "risk_score": 7,
                    "execution_priority": 7,
                    "expected_slippage": 0.1,
                    "gas_settings": "high",
                    "circuit_breakers": {
                        "max_slippage": 1.0,
                        "timeout_seconds": 30
                    },
                    "fallback": True,
                    "timestamp": datetime.now().isoformat()
                }
            
            strategies.append(strategy)
        
        return strategies
