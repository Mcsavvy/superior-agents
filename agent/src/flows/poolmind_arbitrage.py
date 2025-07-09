import json
from datetime import timedelta
from textwrap import dedent
from typing import Callable, List, Dict, Any

from loguru import logger
from result import UnwrapError
from src.agent.poolmind_arbitrage import PoolMindArbitrageAgent
from src.client.poolmind import PoolMindClient
from src.datatypes import (
    StrategyData,
    StrategyDataParameters,
    StrategyInsertData,
)
from src.types import ChatHistory
import uuid


def poolmind_arbitrage_flow(
    agent: PoolMindArbitrageAgent,
    session_id: str,
    role: str,
    supported_exchanges: List[str],
    min_profit_threshold: float,
    max_trade_size_percent: float,
    prev_strat: StrategyData | None,
    notif_str: str,
    poolmind_client: PoolMindClient,
    summarizer: Callable[[List[str]], str],
):
    """
    Execute a PoolMind arbitrage trading workflow.
    
    This function orchestrates the complete arbitrage trading workflow, including
    market analysis, opportunity identification, fund requests, risk assessment,
    and trade execution with profit reporting to PoolMind.
    
    Args:
        agent (PoolMindArbitrageAgent): The arbitrage agent to use
        session_id (str): Identifier for the current session
        role (str): Role of the agent (e.g., "arbitrage_trader")
        supported_exchanges (List[str]): List of supported exchanges
        min_profit_threshold (float): Minimum profit threshold for trades
        max_trade_size_percent (float): Maximum trade size as % of available funds
        prev_strat (StrategyData | None): Previous strategy, if any
        notif_str (str): Notification string to process
        poolmind_client (PoolMindClient): Client for PoolMind API interactions
        summarizer (Callable[[List[str]], str]): Function to summarize text
    
    Returns:
        None: This function doesn't return a value but logs its progress
    """
    agent.reset()
    
    for_training_chat_history = ChatHistory()
    
    logger.info("Reset agent")
    logger.info("Starting PoolMind arbitrage flow")
    
    # Get initial pool state
    pool_state = agent.sensor.get_pool_state()
    logger.info(f"Initial pool state: {pool_state}")
    
    # Initialize system prompt
    new_ch = agent.prepare_system(
        role=role,
        pool_state=pool_state
    )
    agent.chat_history += new_ch
    for_training_chat_history += new_ch
    
    logger.info("Initialized system prompt")
    
    # Get relevant strategies from RAG
    if notif_str:
        logger.info(f"Getting relevant RAG strategies with query: {notif_str[:100]}...")
        related_strategies = agent.rag.relevant_strategy_raw_v4(notif_str)
    else:
        logger.info("No notification string provided, getting general strategies")
        related_strategies = agent.rag.relevant_strategy_raw_v4("STX arbitrage opportunities")
    
    rag_result = {
        "summary": "No relevant RAG strategies found",
        "previous_opportunities": "No previous opportunities available",
        "risk_insights": "No risk insights available"
    }
    
    if len(related_strategies) > 0:
        most_related_strat, distance = related_strategies[0]
        
        if distance <= 0.5:
            logger.info(f"Using RAG strategy with distance: {distance}")
            try:
                rag_result["summary"] = most_related_strat.summarized_desc
                
                if isinstance(most_related_strat.parameters, str):
                    params: StrategyDataParameters = json.loads(most_related_strat.parameters)
                else:
                    params = most_related_strat.parameters
                
                rag_result["previous_opportunities"] = params.get("code_output", "")
                rag_result["risk_insights"] = params.get("summarized_state_change", "")
                
            except Exception as e:
                logger.error(f"Error processing RAG strategy: {e}")
        else:
            logger.info(f"RAG strategy distance too high: {distance} > 0.5")
    
    # Step 1: Market Analysis
    logger.info("Step 1: Performing market analysis...")
    market_analysis_success = False
    market_analysis_output = ""
    
    for attempt in range(3):
        try:
            market_analysis_result = agent.analyze_market()
            if market_analysis_result.is_ok():
                market_analysis_output, new_ch = market_analysis_result.ok()
                agent.chat_history += new_ch
                for_training_chat_history += new_ch
                market_analysis_success = True
                logger.info("Market analysis completed successfully")
                break
            else:
                logger.error(f"Market analysis failed (attempt {attempt + 1}): {market_analysis_result.err()}")
        except Exception as e:
            logger.error(f"Market analysis exception (attempt {attempt + 1}): {e}")
    
    if not market_analysis_success:
        logger.error("Market analysis failed after 3 attempts, aborting cycle")
        return
    
    logger.info(f"Market analysis results: {market_analysis_output[:500]}...")
    
    # Step 2: Generate Arbitrage Strategy
    logger.info("Step 2: Generating arbitrage strategy...")
    strategy_success = False
    strategy_output = ""
    
    for attempt in range(3):
        try:
            strategy_result = agent.generate_arbitrage_strategy(market_analysis_output)
            if strategy_result.is_ok():
                strategy_output, new_ch = strategy_result.ok()
                agent.chat_history += new_ch
                for_training_chat_history += new_ch
                strategy_success = True
                logger.info("Arbitrage strategy generated successfully")
                break
            else:
                logger.error(f"Strategy generation failed (attempt {attempt + 1}): {strategy_result.err()}")
        except Exception as e:
            logger.error(f"Strategy generation exception (attempt {attempt + 1}): {e}")
    
    if not strategy_success:
        logger.error("Strategy generation failed after 3 attempts, aborting cycle")
        return
    
    logger.info(f"Strategy generated: {strategy_output[:500]}...")
    
    # Step 3: Parse strategy and identify opportunities
    logger.info("Step 3: Identifying arbitrage opportunities...")
    opportunities = agent.sensor.identify_arbitrage_opportunities()
    
    if not opportunities:
        logger.info("No arbitrage opportunities found, ending cycle")
        return
    
    # Select best opportunity
    best_opportunity = opportunities[0]  # Already sorted by profit percentage
    logger.info(f"Best opportunity: {best_opportunity.profit_percentage:.2f}% profit "
                f"between {best_opportunity.buy_exchange} and {best_opportunity.sell_exchange}")
    
    # Check if opportunity meets minimum threshold
    if best_opportunity.profit_percentage < min_profit_threshold:
        logger.info(f"Best opportunity ({best_opportunity.profit_percentage:.2f}%) "
                   f"below minimum threshold ({min_profit_threshold}%), skipping")
        return
    
    # Step 4: Risk Assessment
    logger.info("Step 4: Performing risk assessment...")
    risk_assessment_success = False
    risk_data = {}
    
    opportunity_data = {
        "profit_percentage": best_opportunity.profit_percentage,
        "required_amount": best_opportunity.required_amount,
        "exchanges": [best_opportunity.buy_exchange, best_opportunity.sell_exchange],
        "buy_price": best_opportunity.buy_price,
        "sell_price": best_opportunity.sell_price,
        "risk_score": best_opportunity.risk_score
    }
    
    for attempt in range(3):
        try:
            risk_result = agent.assess_risk(opportunity_data)
            if risk_result.is_ok():
                risk_data, new_ch = risk_result.ok()
                agent.chat_history += new_ch
                for_training_chat_history += new_ch
                risk_assessment_success = True
                logger.info("Risk assessment completed successfully")
                break
            else:
                logger.error(f"Risk assessment failed (attempt {attempt + 1}): {risk_result.err()}")
        except Exception as e:
            logger.error(f"Risk assessment exception (attempt {attempt + 1}): {e}")
    
    if not risk_assessment_success:
        logger.warning("Risk assessment failed, using default risk evaluation")
        risk_data = {
            "risk_score": best_opportunity.risk_score,
            "recommendation": "proceed" if best_opportunity.risk_score <= 6 else "abort"
        }
    
    # Check risk recommendation
    if risk_data.get("recommendation") == "abort":
        logger.info(f"Risk assessment recommends aborting (risk score: {risk_data.get('risk_score')})")
        return
    
    # Step 5: Fund Request
    logger.info("Step 5: Requesting funds from PoolMind...")
    
    # Calculate required amount with safety margin
    required_amount = best_opportunity.required_amount * 1.1  # 10% safety margin
    
    # Check if amount exceeds maximum trade size
    max_allowed = pool_state["available_stx"] * max_trade_size_percent / 100
    if required_amount > max_allowed:
        required_amount = max_allowed
        logger.info(f"Reducing trade size to maximum allowed: {required_amount}")
    
    # Get deposit address from the buy exchange
    buy_exchange_deposit_address = agent.get_exchange_deposit_address(best_opportunity.buy_exchange)
    
    memo = f"Arbitrage trade: {best_opportunity.buy_exchange} -> {best_opportunity.sell_exchange}, Expected profit: {best_opportunity.expected_profit:.2f} STX"
    
    fund_request_success = False
    approved_amount = 0
    
    try:
        fund_response = poolmind_client.request_funds(
            recipient_address=buy_exchange_deposit_address,
            amount=required_amount,
            memo=memo
        )
        
        if fund_response.get("success"):
            # Extract amount from the response data
            response_data = fund_response.get("data", {})
            approved_amount = response_data.get("amount", required_amount)
            fund_request_success = True
            logger.info(f"Fund request approved: {approved_amount} STX to {buy_exchange_deposit_address}")
            logger.info(f"Transaction ID: {response_data.get('txId', 'N/A')}")
        else:
            logger.info(f"Fund request rejected: {fund_response.get('message', 'Unknown reason')}")
    except Exception as e:
        logger.error(f"Fund request failed: {e}")
    
    if not fund_request_success or approved_amount <= 0:
        logger.info("Fund request failed or rejected, ending cycle")
        return
    
    # Step 6: Execute Arbitrage Trade
    logger.info("Step 6: Executing arbitrage trade...")
    
    strategy_details = {
        "buy_exchange": best_opportunity.buy_exchange,
        "sell_exchange": best_opportunity.sell_exchange,
        "buy_price": best_opportunity.buy_price,
        "sell_price": best_opportunity.sell_price,
        "expected_profit": best_opportunity.expected_profit,
        "risk_score": risk_data.get("risk_score", 5)
    }
    
    trade_execution_success = False
    trade_output = ""
    
    for attempt in range(3):
        try:
            execution_result = agent.execute_arbitrage_trade(strategy_details, approved_amount)
            if execution_result.is_ok():
                trade_output, new_ch = execution_result.ok()
                agent.chat_history += new_ch
                for_training_chat_history += new_ch
                trade_execution_success = True
                logger.info("Arbitrage trade executed successfully")
                break
            else:
                logger.error(f"Trade execution failed (attempt {attempt + 1}): {execution_result.err()}")
        except Exception as e:
            logger.error(f"Trade execution exception (attempt {attempt + 1}): {e}")
    
    if not trade_execution_success:
        logger.error("Trade execution failed after 3 attempts")
        # In a real implementation, we would need to return the funds to PoolMind
        return
    
    logger.info(f"Trade execution results: {trade_output[:500]}...")
    
    # Step 7: Calculate trade results
    logger.info("Step 7: Calculating trade results...")
    
    try:
        # Parse trade results (this would be more sophisticated in real implementation)
        trade_id = str(uuid.uuid4())
        
        # Mock profit calculation - in real implementation this would be parsed from trade_output
        final_amount = approved_amount * (1 + best_opportunity.profit_percentage / 100)
        actual_profit = final_amount - approved_amount
        fees_paid = approved_amount * 0.002  # Assume 0.2% total fees
        net_profit = actual_profit - fees_paid
        
        logger.info(f"Trade results calculated:")
        logger.info(f"  Initial amount: {approved_amount} STX")
        logger.info(f"  Final amount: {final_amount} STX")
        logger.info(f"  Gross profit: {actual_profit} STX")
        logger.info(f"  Fees paid: {fees_paid} STX")
        logger.info(f"  Net profit: {net_profit} STX")
        
        # Note: Profit reporting and NAV updates would be handled by the PoolMind platform
        # based on the actual trade execution results from the exchanges
        
    except Exception as e:
        logger.error(f"Trade result calculation failed: {e}")
        # Set default values for logging
        net_profit = 0
        actual_profit = 0
    
    # Step 8: Save strategy and results
    logger.info("Step 8: Saving strategy and results...")
    
    # Save chat history
    agent.db.insert_chat_history(session_id, for_training_chat_history)
    
    # Get final pool state
    final_pool_state = agent.sensor.get_pool_state()
    
    # Summarize state change
    summarized_state_change = dedent(f"""
        Initial Pool State:
        - Available STX: {pool_state['available_stx']}
        - NAV: {pool_state['current_nav']}
        - Pool Size: {pool_state['pool_size']}
        
        Final Pool State:
        - Available STX: {final_pool_state['available_stx']}
        - NAV: {final_pool_state['current_nav']}
        - Pool Size: {final_pool_state['pool_size']}
        
        Trade Results:
        - Opportunity: {best_opportunity.profit_percentage:.2f}% profit
        - Amount Traded: {approved_amount} STX
        - Net Profit: {net_profit:.2f} STX
        - Exchanges: {best_opportunity.buy_exchange} -> {best_opportunity.sell_exchange}
    """)
    
    # Summarize code
    summarized_code = summarizer([
        trade_output,
        "Summarize the arbitrage trading code execution above in key points"
    ])
    
    logger.info("Summarizing code...")
    logger.info(f"Summarized code: {summarized_code}")
    
    # Save strategy
    try:
        agent.db.insert_strategy_and_result(
            agent_id=agent.agent_id,
            strategy_result=StrategyInsertData(
                summarized_desc=summarizer([strategy_output]),
                full_desc=strategy_output,
                parameters={
                    "exchanges": [best_opportunity.buy_exchange, best_opportunity.sell_exchange],
                    "trading_instruments": ["spot"],
                    "metric_name": "pool_state",
                    "start_metric_state": json.dumps(pool_state),
                    "end_metric_state": json.dumps(final_pool_state),
                    "summarized_state_change": summarized_state_change,
                    "summarized_code": summarized_code,
                    "code_output": trade_output,
                    "prev_strat": prev_strat.summarized_desc if prev_strat else "",
                    "notif_str": notif_str,
                    "profit_percentage": best_opportunity.profit_percentage,
                    "net_profit": net_profit,
                    "risk_score": risk_data.get("risk_score", 5)
                },
                strategy_result="success" if trade_execution_success else "failed",
            ),
        )
        logger.info("Strategy saved successfully")
    except Exception as e:
        logger.error(f"Failed to save strategy: {e}")
    
    logger.info("PoolMind arbitrage cycle completed successfully")


def poolmind_monitoring_flow(
    agent: PoolMindArbitrageAgent,
    session_id: str,
    poolmind_client: PoolMindClient,
    monitoring_interval: int = 60,
):
    """
    Continuous monitoring flow for PoolMind arbitrage opportunities.
    
    This flow runs continuously to monitor for arbitrage opportunities
    and executes trades when profitable opportunities are identified.
    
    Args:
        agent (PoolMindArbitrageAgent): The arbitrage agent
        session_id (str): Session identifier
        poolmind_client (PoolMindClient): PoolMind API client
        monitoring_interval (int): Monitoring interval in seconds
    """
    logger.info("Starting PoolMind continuous monitoring flow")
    
    while True:
        try:
            # Check for arbitrage opportunities
            opportunities = agent.sensor.identify_arbitrage_opportunities()
            
            if opportunities:
                best_opportunity = opportunities[0]
                
                if best_opportunity.profit_percentage >= agent.min_profit_threshold:
                    logger.info(f"Profitable opportunity found: {best_opportunity.profit_percentage:.2f}%")
                    
                    # Execute the full arbitrage flow
                    poolmind_arbitrage_flow(
                        agent=agent,
                        session_id=session_id,
                        role="continuous_arbitrage_trader",
                        supported_exchanges=agent.supported_exchanges,
                        min_profit_threshold=agent.min_profit_threshold,
                        max_trade_size_percent=agent.max_trade_size_percent,
                        prev_strat=None,
                        notif_str=f"Arbitrage opportunity: {best_opportunity.profit_percentage:.2f}% profit",
                        poolmind_client=poolmind_client,
                        summarizer=lambda x: " ".join(x) if isinstance(x, list) else str(x)
                    )
                else:
                    logger.debug(f"Opportunity below threshold: {best_opportunity.profit_percentage:.2f}%")
            else:
                logger.debug("No arbitrage opportunities found")
            
            # Wait before next check
            import time
            time.sleep(monitoring_interval)
            
        except KeyboardInterrupt:
            logger.info("Monitoring flow interrupted by user")
            break
        except Exception as e:
            logger.error(f"Error in monitoring flow: {e}")
            # Continue monitoring despite errors
            import time
            time.sleep(monitoring_interval) 