from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum


class PoolMindArbitrageState(Enum):
    """
    Enumeration of possible states for a PoolMind arbitrage agent.
    """
    SUCCESS = "success"
    FAILED_MARKET_ANALYSIS = "failed_market_analysis"
    FAILED_STRATEGY_GENERATION = "failed_strategy_generation"
    FAILED_FUND_REQUEST = "failed_fund_request"
    FAILED_RISK_ASSESSMENT = "failed_risk_assessment"
    FAILED_TRADE_EXECUTION = "failed_trade_execution"
    INSUFFICIENT_OPPORTUNITY = "insufficient_opportunity"
    HIGH_RISK_ABORT = "high_risk_abort"


@dataclass
class PoolMetrics:
    """
    Data class representing PoolMind pool metrics.
    """
    current_nav: float
    available_stx: float
    total_shares: float
    pool_size: float
    daily_return: float
    weekly_return: float
    monthly_return: float
    total_profit: float
    sharpe_ratio: float
    max_drawdown: float
    timestamp: datetime


@dataclass
class ArbitrageMetrics:
    """
    Data class representing arbitrage-specific metrics.
    """
    total_opportunities_identified: int
    total_trades_executed: int
    total_profit_generated: float
    average_profit_per_trade: float
    success_rate: float
    average_execution_time: float
    risk_adjusted_returns: float
    exchange_performance: Dict[str, Dict[str, Any]]
    timestamp: datetime


@dataclass
class ExchangeData:
    """
    Data class representing exchange-specific data.
    """
    exchange_name: str
    stx_bid: float
    stx_ask: float
    volume_24h: float
    liquidity_depth: float
    spread_percentage: float
    reliability_score: float
    last_updated: datetime


@dataclass
class ArbitrageOpportunityData:
    """
    Data class representing a specific arbitrage opportunity.
    """
    opportunity_id: str
    buy_exchange: str
    sell_exchange: str
    buy_price: float
    sell_price: float
    profit_percentage: float
    profit_amount: float
    required_capital: float
    risk_score: int
    execution_time_estimate: int
    liquidity_score: float
    market_conditions: Dict[str, Any]
    timestamp: datetime


@dataclass
class TradeExecutionData:
    """
    Data class representing trade execution details.
    """
    trade_id: str
    opportunity_id: str
    agent_id: str
    session_id: str
    initial_amount: float
    final_amount: float
    gross_profit: float
    fees_paid: float
    net_profit: float
    execution_time_seconds: int
    buy_exchange: str
    sell_exchange: str
    buy_price: float
    sell_price: float
    slippage_percentage: float
    status: str
    error_message: Optional[str]
    timestamp: datetime


@dataclass
class RiskAssessmentData:
    """
    Data class representing risk assessment results.
    """
    assessment_id: str
    opportunity_id: str
    overall_risk_score: int
    market_volatility_risk: float
    liquidity_risk: float
    execution_risk: float
    counterparty_risk: float
    technical_risk: float
    recommendation: str  # "proceed", "caution", "abort"
    max_position_size: float
    risk_mitigation_strategies: List[str]
    timestamp: datetime


@dataclass
class PoolMindStrategyParameters:
    """
    Parameters specific to PoolMind arbitrage strategies.
    """
    supported_exchanges: List[str]
    min_profit_threshold: float
    max_trade_size_percent: float
    stop_loss_threshold: float
    risk_tolerance: str
    execution_timeout: int
    slippage_tolerance: float
    pool_state: Dict[str, Any]
    market_conditions: Dict[str, Any]
    arbitrage_opportunities: List[ArbitrageOpportunityData]
    risk_assessment: Optional[RiskAssessmentData]
    fund_request_details: Optional[Dict[str, Any]]
    trade_execution_details: Optional[TradeExecutionData]


@dataclass
class PoolMindNotificationData:
    """
    Data class for PoolMind-specific notifications.
    """
    notification_id: str
    notification_type: str  # "opportunity", "trade_executed", "profit_reported", "risk_alert"
    agent_id: str
    session_id: str
    title: str
    message: str
    data: Dict[str, Any]
    priority: str  # "low", "medium", "high", "critical"
    timestamp: datetime
    acknowledged: bool = False


@dataclass
class PoolMindPerformanceMetrics:
    """
    Comprehensive performance metrics for PoolMind arbitrage agent.
    """
    agent_id: str
    session_id: str
    total_cycles: int
    successful_cycles: int
    failed_cycles: int
    success_rate: float
    total_opportunities_identified: int
    total_trades_executed: int
    total_stx_traded: float
    total_profit_generated: float
    total_fees_paid: float
    net_profit: float
    average_profit_per_trade: float
    best_trade_profit: float
    worst_trade_loss: float
    average_execution_time: float
    risk_adjusted_returns: float
    sharpe_ratio: float
    maximum_drawdown: float
    pool_nav_improvement: float
    exchange_performance: Dict[str, Dict[str, Any]]
    risk_metrics: Dict[str, float]
    uptime_percentage: float
    error_rate: float
    last_updated: datetime 