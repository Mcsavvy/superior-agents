"""
Execution Optimizer - Optimizes and executes trading strategies
"""
from typing import Dict, List, Any, Optional
import logging
import asyncio
from datetime import datetime

from pydantic import BaseModel

from poolmind_agent.utils.config import AgentConfig
from poolmind_agent.services.exchange_client import ExchangeClient

logger = logging.getLogger(__name__)

class ExecutionOptimizer:
    """
    Execution Optimizer that handles gas-aware routing, slippage prediction,
    exchange priority scoring, and batched transaction grouping.
    """
    
    def __init__(self, config: AgentConfig):
        """
        Initialize the Execution Optimizer
        
        Args:
            config: Agent configuration
        """
        self.config = config
        self.exchange_client = ExchangeClient(config)
        
        logger.info("Execution Optimizer initialized")
        
    async def update_config(self, config_updates: Dict[str, Any]) -> bool:
        """
        Update the execution optimizer configuration
        
        Args:
            config_updates: Dictionary or AgentConfig with configuration updates
            
        Returns:
            bool: True if update was successful
        """
        try:
            # Update local config reference
            self.config = config_updates
            
            # Update exchange client with new config
            # Note: ExchangeClient may need its own update_config method if it has stateful configuration
            
            logger.info("Execution Optimizer configuration updated")
            return True
                
        except Exception as e:
            logger.error(f"Error updating Execution Optimizer configuration: {str(e)}")
            return False
    
    async def optimize(self, 
                     pool_state: Dict[str, Any], 
                     strategies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Optimize execution for approved strategies
        
        Args:
            pool_state: Current pool state
            strategies: List of approved trading strategies
            
        Returns:
            List of optimized execution plans
        """
        logger.debug(f"Optimizing execution for {len(strategies)} strategies")
        
        if not strategies:
            logger.info("No strategies to optimize")
            return []
        
        try:
            # Sort strategies by execution priority (descending)
            sorted_strategies = sorted(
                strategies,
                key=lambda s: s.get("execution_priority", 0),
                reverse=True
            )
            
            # Calculate available capital
            available_capital = max(0, pool_state.get("total_value", 0) - pool_state.get("liquidity_reserve", 0))
            
            # Optimize each strategy
            execution_plans = []
            remaining_capital = available_capital
            
            for strategy in sorted_strategies:
                # Skip if no capital left
                if remaining_capital <= 0:
                    logger.info("No remaining capital for strategy execution")
                    break
                
                # Calculate position size
                position_size_pct = strategy.get("position_size_pct", 1.0)
                position_size = min(remaining_capital, available_capital * (position_size_pct / 100.0))
                
                if position_size <= 0:
                    continue
                
                # Create execution plan
                execution_plan = await self._create_execution_plan(strategy, position_size)
                
                if execution_plan:
                    execution_plans.append(execution_plan)
                    remaining_capital -= position_size
            
            # Group similar executions if possible
            optimized_plans = await self._group_similar_executions(execution_plans)
            
            logger.info(f"Created {len(optimized_plans)} optimized execution plans")
            return optimized_plans
            
        except Exception as e:
            logger.error(f"Error optimizing execution: {str(e)}")
            return []
    
    async def _create_execution_plan(self, 
                                   strategy: Dict[str, Any], 
                                   position_size: float) -> Optional[Dict[str, Any]]:
        """
        Create an execution plan for a strategy
        
        Args:
            strategy: Trading strategy
            position_size: Position size in absolute terms
            
        Returns:
            Execution plan or None if creation failed
        """
        try:
            opportunity = strategy.get("opportunity", {})
            
            # Extract key details
            pair = opportunity.get("pair", "")
            buy_exchange = opportunity.get("buy_exchange", "")
            sell_exchange = opportunity.get("sell_exchange", "")
            buy_price = opportunity.get("buy_price", 0)
            sell_price = opportunity.get("sell_price", 0)
            
            # Get current market conditions
            buy_market_data = await self.exchange_client.get_market_details(buy_exchange, pair)
            sell_market_data = await self.exchange_client.get_market_details(sell_exchange, pair)
            
            # Check if opportunity still exists
            current_buy_price = buy_market_data.get("price", buy_price)
            current_sell_price = sell_market_data.get("price", sell_price)
            
            price_diff_pct = ((current_sell_price - current_buy_price) / current_buy_price) * 100.0
            
            if price_diff_pct <= 0:
                logger.warning(f"Opportunity no longer exists for {pair}")
                return None
            
            # Calculate expected slippage
            buy_slippage = self._estimate_slippage(buy_market_data, position_size)
            sell_slippage = self._estimate_slippage(sell_market_data, position_size)
            
            # Adjust prices for slippage
            effective_buy_price = current_buy_price * (1 + buy_slippage)
            effective_sell_price = current_sell_price * (1 - sell_slippage)
            
            # Check if opportunity is still profitable after slippage
            if effective_sell_price <= effective_buy_price:
                logger.warning(f"Opportunity not profitable after slippage for {pair}")
                return None
            
            # Calculate gas costs
            buy_gas_cost = self._estimate_gas_cost(buy_exchange, strategy.get("gas_settings", "medium"))
            sell_gas_cost = self._estimate_gas_cost(sell_exchange, strategy.get("gas_settings", "medium"))
            total_gas_cost = buy_gas_cost + sell_gas_cost
            
            # Calculate expected profit
            buy_amount = position_size / effective_buy_price
            sell_amount = buy_amount
            
            # Apply exchange fees
            buy_fee = self.config.exchange_fees.get(buy_exchange, 0.1) / 100.0
            sell_fee = self.config.exchange_fees.get(sell_exchange, 0.1) / 100.0
            
            buy_fee_amount = position_size * buy_fee
            sell_amount_after_fees = sell_amount * (1 - sell_fee)
            
            expected_revenue = sell_amount_after_fees * effective_sell_price
            expected_profit = expected_revenue - position_size - total_gas_cost
            expected_profit_pct = (expected_profit / position_size) * 100.0
            
            # Create execution plan
            execution_plan = {
                "strategy_id": id(strategy),  # Use object id as unique identifier
                "pair": pair,
                "buy_exchange": buy_exchange,
                "sell_exchange": sell_exchange,
                "position_size": position_size,
                "buy_price": current_buy_price,
                "sell_price": current_sell_price,
                "effective_buy_price": effective_buy_price,
                "effective_sell_price": effective_sell_price,
                "buy_slippage": buy_slippage,
                "sell_slippage": sell_slippage,
                "buy_amount": buy_amount,
                "sell_amount": sell_amount_after_fees,
                "gas_cost": total_gas_cost,
                "expected_profit": expected_profit,
                "expected_profit_pct": expected_profit_pct,
                "gas_settings": strategy.get("gas_settings", "medium"),
                "circuit_breakers": strategy.get("circuit_breakers", {}),
                "timestamp": datetime.now().isoformat()
            }
            
            return execution_plan
            
        except Exception as e:
            logger.error(f"Error creating execution plan: {str(e)}")
            return None
    
    def _estimate_slippage(self, market_data: Dict[str, Any], position_size: float) -> float:
        """
        Estimate slippage based on market data and position size
        
        Args:
            market_data: Market data for the exchange and pair
            position_size: Position size in absolute terms
            
        Returns:
            Estimated slippage as a decimal (e.g., 0.001 = 0.1%)
        """
        try:
            # Extract order book data
            order_book = market_data.get("order_book", {})
            
            if not order_book:
                # Default slippage if no order book data
                return 0.001  # 0.1% default slippage
            
            # Get relevant side of the order book
            bids = order_book.get("bids", [])  # For selling
            asks = order_book.get("asks", [])  # For buying
            
            # Calculate slippage based on order book depth
            # This is a simplified model; in production, would use a more sophisticated model
            
            # For buying (using asks)
            if position_size > 0 and asks:
                return self._calculate_slippage_from_orders(asks, position_size)
            
            # For selling (using bids)
            if position_size > 0 and bids:
                return self._calculate_slippage_from_orders(bids, position_size)
            
            # Default if no order book data
            return 0.001  # 0.1% default slippage
            
        except Exception as e:
            logger.error(f"Error estimating slippage: {str(e)}")
            return 0.002  # 0.2% default slippage on error
    
    def _calculate_slippage_from_orders(self, orders: List[Dict[str, Any]], position_size: float) -> float:
        """
        Calculate slippage from order book data
        
        Args:
            orders: List of orders (price, amount)
            position_size: Position size in absolute terms
            
        Returns:
            Estimated slippage as a decimal
        """
        try:
            if not orders:
                return 0.001  # Default slippage
            
            # Sort orders by price (ascending for asks, descending for bids)
            sorted_orders = sorted(orders, key=lambda x: x.get("price", 0))
            
            # Get best price
            best_price = sorted_orders[0].get("price", 0)
            
            if best_price <= 0:
                return 0.001  # Default slippage
            
            # Calculate weighted average price to fill the position
            remaining_size = position_size
            total_cost = 0.0
            
            for order in sorted_orders:
                price = order.get("price", 0)
                amount = order.get("amount", 0)
                
                if price <= 0 or amount <= 0:
                    continue
                
                order_cost = price * amount
                
                if remaining_size <= order_cost:
                    # This order can fill the remaining position
                    total_cost += price * (remaining_size / price)
                    remaining_size = 0
                    break
                else:
                    # Use the entire order
                    total_cost += order_cost
                    remaining_size -= order_cost
            
            # If we couldn't fill the entire position, assume additional slippage
            if remaining_size > 0:
                # Add 0.5% additional slippage for the unfilled portion
                unfilled_ratio = remaining_size / position_size
                additional_slippage = unfilled_ratio * 0.005
                
                # Estimate cost of unfilled portion with additional slippage
                if sorted_orders:
                    last_price = sorted_orders[-1].get("price", best_price)
                    total_cost += remaining_size * last_price * (1 + additional_slippage)
            
            # Calculate weighted average price
            weighted_avg_price = total_cost / position_size if position_size > 0 else best_price
            
            # Calculate slippage
            slippage = abs(weighted_avg_price - best_price) / best_price
            
            return slippage
            
        except Exception as e:
            logger.error(f"Error calculating slippage from orders: {str(e)}")
            return 0.002  # 0.2% default slippage on error
    
    def _estimate_gas_cost(self, exchange: str, gas_setting: str) -> float:
        """
        Estimate gas cost for a transaction
        
        Args:
            exchange: Exchange name
            gas_setting: Gas setting (low, medium, high)
            
        Returns:
            Estimated gas cost in USD
        """
        try:
            # Get base gas cost for the exchange
            base_gas_cost = self.config.exchange_gas_costs.get(exchange, 5.0)  # Default $5
            
            # Adjust based on gas setting
            multiplier = {
                "low": 0.8,
                "medium": 1.0,
                "high": 1.5
            }.get(gas_setting, 1.0)
            
            return base_gas_cost * multiplier
            
        except Exception as e:
            logger.error(f"Error estimating gas cost: {str(e)}")
            return 5.0  # Default $5 gas cost
    
    async def _group_similar_executions(self, execution_plans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Group similar executions to optimize gas costs
        
        Args:
            execution_plans: List of execution plans
            
        Returns:
            List of optimized execution plans
        """
        try:
            if len(execution_plans) <= 1:
                return execution_plans
            
            # Group by exchange pairs
            exchange_groups = {}
            
            for plan in execution_plans:
                key = f"{plan.get('buy_exchange', '')}-{plan.get('sell_exchange', '')}"
                
                if key not in exchange_groups:
                    exchange_groups[key] = []
                
                exchange_groups[key].append(plan)
            
            # Optimize each group
            optimized_plans = []
            
            for key, plans in exchange_groups.items():
                if len(plans) <= 1:
                    optimized_plans.extend(plans)
                    continue
                
                # Group by trading pair
                pair_groups = {}
                
                for plan in plans:
                    pair = plan.get("pair", "")
                    
                    if pair not in pair_groups:
                        pair_groups[pair] = []
                    
                    pair_groups[pair].append(plan)
                
                # Combine plans for the same pair
                for pair, pair_plans in pair_groups.items():
                    if len(pair_plans) <= 1:
                        optimized_plans.extend(pair_plans)
                        continue
                    
                    # Create a combined plan
                    combined_plan = await self._combine_plans(pair_plans)
                    optimized_plans.append(combined_plan)
            
            return optimized_plans
            
        except Exception as e:
            logger.error(f"Error grouping similar executions: {str(e)}")
            return execution_plans
    
    async def _combine_plans(self, plans: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Combine multiple execution plans into one
        
        Args:
            plans: List of execution plans to combine
            
        Returns:
            Combined execution plan
        """
        try:
            if not plans:
                return {}
            
            if len(plans) == 1:
                return plans[0]
            
            # Use the first plan as a base
            base_plan = plans[0]
            
            # Sum up the position sizes and amounts
            total_position_size = sum(plan.get("position_size", 0) for plan in plans)
            total_buy_amount = sum(plan.get("buy_amount", 0) for plan in plans)
            total_sell_amount = sum(plan.get("sell_amount", 0) for plan in plans)
            total_expected_profit = sum(plan.get("expected_profit", 0) for plan in plans)
            
            # Use the highest gas cost (only pay once)
            max_gas_cost = max(plan.get("gas_cost", 0) for plan in plans)
            
            # Calculate weighted average prices
            weighted_buy_price = sum(
                plan.get("buy_price", 0) * plan.get("position_size", 0)
                for plan in plans
            ) / total_position_size if total_position_size > 0 else 0
            
            weighted_sell_price = sum(
                plan.get("sell_price", 0) * plan.get("position_size", 0)
                for plan in plans
            ) / total_position_size if total_position_size > 0 else 0
            
            # Calculate expected profit percentage
            expected_profit_pct = (total_expected_profit / total_position_size) * 100.0 if total_position_size > 0 else 0
            
            # Combine circuit breakers (use the most conservative values)
            max_slippage = min(
                plan.get("circuit_breakers", {}).get("max_slippage", 1.0)
                for plan in plans
            )
            
            timeout_seconds = min(
                plan.get("circuit_breakers", {}).get("timeout_seconds", 30)
                for plan in plans
            )
            
            # Create combined plan
            combined_plan = {
                "strategy_id": f"combined-{datetime.now().timestamp()}",
                "pair": base_plan.get("pair", ""),
                "buy_exchange": base_plan.get("buy_exchange", ""),
                "sell_exchange": base_plan.get("sell_exchange", ""),
                "position_size": total_position_size,
                "buy_price": weighted_buy_price,
                "sell_price": weighted_sell_price,
                "buy_amount": total_buy_amount,
                "sell_amount": total_sell_amount,
                "gas_cost": max_gas_cost,
                "expected_profit": total_expected_profit,
                "expected_profit_pct": expected_profit_pct,
                "gas_settings": base_plan.get("gas_settings", "medium"),
                "circuit_breakers": {
                    "max_slippage": max_slippage,
                    "timeout_seconds": timeout_seconds
                },
                "combined_plan": True,
                "combined_count": len(plans),
                "timestamp": datetime.now().isoformat()
            }
            
            return combined_plan
            
        except Exception as e:
            logger.error(f"Error combining plans: {str(e)}")
            return plans[0] if plans else {}
    
    async def execute(self, execution_plans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute the optimized trading plans
        
        Args:
            execution_plans: List of optimized execution plans
            
        Returns:
            List of execution results
        """
        logger.debug(f"Executing {len(execution_plans)} trading plans")
        
        if not execution_plans:
            logger.info("No execution plans to execute")
            return []
        
        try:
            # Execute plans in parallel
            tasks = [
                self._execute_plan(plan)
                for plan in execution_plans
            ]
            
            execution_results = await asyncio.gather(*tasks)
            
            # Filter out None results
            execution_results = [result for result in execution_results if result]
            
            logger.info(f"Executed {len(execution_results)} trading plans")
            return execution_results
            
        except Exception as e:
            logger.error(f"Error executing trading plans: {str(e)}")
            return []
    
    async def _execute_plan(self, plan: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Execute a single trading plan
        
        Args:
            plan: Execution plan
            
        Returns:
            Execution result or None if execution failed
        """
        try:
            # Extract key details
            pair = plan.get("pair", "")
            buy_exchange = plan.get("buy_exchange", "")
            sell_exchange = plan.get("sell_exchange", "")
            position_size = plan.get("position_size", 0)
            buy_amount = plan.get("buy_amount", 0)
            
            if position_size <= 0 or buy_amount <= 0:
                logger.warning(f"Invalid position size or buy amount for {pair}")
                return None
            
            # Get circuit breaker settings
            circuit_breakers = plan.get("circuit_breakers", {})
            max_slippage = circuit_breakers.get("max_slippage", 1.0) / 100.0  # Convert to decimal
            timeout_seconds = circuit_breakers.get("timeout_seconds", 30)
            
            # Execute buy order
            logger.info(f"Executing buy order for {buy_amount} {pair} on {buy_exchange}")
            
            buy_result = await self.exchange_client.execute_order(
                exchange=buy_exchange,
                pair=pair,
                side="buy",
                amount=position_size,
                price=plan.get("buy_price", 0),
                max_slippage=max_slippage,
                timeout_seconds=timeout_seconds
            )
            
            if not buy_result.get("success", False):
                logger.error(f"Buy order failed: {buy_result.get('error', 'Unknown error')}")
                return {
                    "plan": plan,
                    "success": False,
                    "stage": "buy",
                    "error": buy_result.get("error", "Buy order failed"),
                    "timestamp": datetime.now().isoformat()
                }
            
            # Get actual buy details
            actual_buy_price = buy_result.get("price", plan.get("buy_price", 0))
            actual_buy_amount = buy_result.get("filled_amount", 0)
            
            if actual_buy_amount <= 0:
                logger.error("Buy order filled with zero amount")
                return {
                    "plan": plan,
                    "success": False,
                    "stage": "buy",
                    "error": "Buy order filled with zero amount",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Execute sell order
            logger.info(f"Executing sell order for {actual_buy_amount} {pair} on {sell_exchange}")
            
            sell_result = await self.exchange_client.execute_order(
                exchange=sell_exchange,
                pair=pair,
                side="sell",
                amount=actual_buy_amount,
                price=plan.get("sell_price", 0),
                max_slippage=max_slippage,
                timeout_seconds=timeout_seconds
            )
            
            if not sell_result.get("success", False):
                logger.error(f"Sell order failed: {sell_result.get('error', 'Unknown error')}")
                return {
                    "plan": plan,
                    "success": False,
                    "stage": "sell",
                    "error": sell_result.get("error", "Sell order failed"),
                    "buy_result": buy_result,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Get actual sell details
            actual_sell_price = sell_result.get("price", plan.get("sell_price", 0))
            actual_sell_amount = sell_result.get("filled_amount", 0)
            
            # Calculate actual profit
            buy_cost = actual_buy_price * actual_buy_amount
            sell_revenue = actual_sell_price * actual_sell_amount
            
            # Apply fees
            buy_fee = self.config.exchange_fees.get(buy_exchange, 0.1) / 100.0
            sell_fee = self.config.exchange_fees.get(sell_exchange, 0.1) / 100.0
            
            buy_fee_amount = buy_cost * buy_fee
            sell_fee_amount = sell_revenue * sell_fee
            
            # Calculate gas costs
            gas_cost = plan.get("gas_cost", 0)
            
            # Calculate actual profit
            actual_profit = sell_revenue - buy_cost - buy_fee_amount - sell_fee_amount - gas_cost
            actual_profit_pct = (actual_profit / buy_cost) * 100.0 if buy_cost > 0 else 0
            
            # Create execution result
            execution_result = {
                "plan": plan,
                "success": True,
                "buy_result": {
                    "price": actual_buy_price,
                    "amount": actual_buy_amount,
                    "cost": buy_cost,
                    "fee": buy_fee_amount
                },
                "sell_result": {
                    "price": actual_sell_price,
                    "amount": actual_sell_amount,
                    "revenue": sell_revenue,
                    "fee": sell_fee_amount
                },
                "gas_cost": gas_cost,
                "actual_profit": actual_profit,
                "actual_profit_pct": actual_profit_pct,
                "expected_profit": plan.get("expected_profit", 0),
                "profit_difference": actual_profit - plan.get("expected_profit", 0),
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Successfully executed trade with {actual_profit_pct:.2f}% profit")
            return execution_result
            
        except Exception as e:
            logger.error(f"Error executing plan: {str(e)}")
            return {
                "plan": plan,
                "success": False,
                "stage": "unknown",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
