import hmac
import hashlib
import json
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
import requests
from loguru import logger


@dataclass
class FundRequest:
    """
    Data class for fund request parameters.
    """
    amount_stx: float
    purpose: str
    expected_profit: float
    risk_assessment: str
    exchanges: list
    estimated_duration: str


@dataclass
class ProfitReport:
    """
    Data class for profit reporting parameters.
    """
    trade_id: str
    initial_amount: float
    final_amount: float
    profit: float
    fees_paid: float
    net_profit: float
    execution_time: str


class PoolMindClient:
    """
    Client for interacting with the PoolMind API.
    
    This client handles fund requests, profit reporting, and other
    agent-specific operations with HMAC authentication.
    """
    
    def __init__(
        self,
        base_url: str,
        agent_id: str,
        hmac_secret: str,
        timeout: int = 30
    ):
        """
        Initialize the PoolMind client.
        
        Args:
            base_url (str): Base URL for the PoolMind API
            agent_id (str): Unique identifier for the agent
            hmac_secret (str): Secret key for HMAC authentication
            timeout (int): Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.agent_id = agent_id
        self.hmac_secret = hmac_secret
        self.timeout = timeout
        self.session = requests.Session()
        
        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': f'PoolMind-Agent/{agent_id}'
        })
    
    def _generate_hmac_signature(self, method: str, path: str, body: str = "", timestamp: str = None) -> str:
        """
        Generate HMAC signature for request authentication.
        
        Args:
            method (str): HTTP method (GET, POST, etc.)
            path (str): API endpoint path
            body (str): Request body (for POST requests)
            timestamp (str): Request timestamp
            
        Returns:
            str: HMAC signature
        """
        if timestamp is None:
            timestamp = str(int(time.time()))
        
        # Create message to sign: method + path + timestamp + body
        message = f"{method.upper()}{path}{timestamp}{body}"
        
        # Generate HMAC signature
        signature = hmac.new(
            self.hmac_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def _make_authenticated_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None
    ) -> requests.Response:
        """
        Make an authenticated request to the PoolMind API.
        
        Args:
            method (str): HTTP method
            endpoint (str): API endpoint
            data (Optional[Dict[str, Any]]): Request data
            
        Returns:
            requests.Response: API response
            
        Raises:
            requests.HTTPError: If the request fails
        """
        url = f"{self.base_url}{endpoint}"
        timestamp = str(int(time.time()))
        
        # Prepare request body
        body = json.dumps(data) if data else ""
        
        # Generate HMAC signature
        signature = self._generate_hmac_signature(method, endpoint, body, timestamp)
        
        # Set authentication headers
        headers = {
            'x-agent-id': self.agent_id,
            'x-timestamp': timestamp,
            'x-hmac-signature': signature
        }
        
        # Make request
        response = self.session.request(
            method=method,
            url=url,
            headers=headers,
            data=body if body else None,
            timeout=self.timeout
        )
        
        response.raise_for_status()
        return response
    
    def request_funds(self, fund_request: FundRequest) -> Dict[str, Any]:
        """
        Request funds from PoolMind for arbitrage trading.
        
        Args:
            fund_request (FundRequest): Fund request parameters
            
        Returns:
            Dict[str, Any]: API response with approval status
            
        Raises:
            requests.HTTPError: If the request fails
        """
        try:
            data = {
                "amount_stx": fund_request.amount_stx,
                "purpose": fund_request.purpose,
                "expected_profit": fund_request.expected_profit,
                "risk_assessment": fund_request.risk_assessment,
                "exchanges": fund_request.exchanges,
                "estimated_duration": fund_request.estimated_duration
            }
            
            response = self._make_authenticated_request(
                method="POST",
                endpoint="/api/v1/agent/fund-request",
                data=data
            )
            
            result = response.json()
            logger.info(f"Fund request submitted: {result}")
            return result
            
        except requests.HTTPError as e:
            logger.error(f"Fund request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in fund request: {e}")
            raise
    
    def report_profit(self, profit_report: ProfitReport) -> Dict[str, Any]:
        """
        Report trading profit to PoolMind.
        
        Args:
            profit_report (ProfitReport): Profit report parameters
            
        Returns:
            Dict[str, Any]: API response
            
        Raises:
            requests.HTTPError: If the request fails
        """
        try:
            data = {
                "trade_id": profit_report.trade_id,
                "initial_amount": profit_report.initial_amount,
                "final_amount": profit_report.final_amount,
                "profit": profit_report.profit,
                "fees_paid": profit_report.fees_paid,
                "net_profit": profit_report.net_profit,
                "execution_time": profit_report.execution_time
            }
            
            response = self._make_authenticated_request(
                method="POST",
                endpoint="/api/v1/agent/profit-report",
                data=data
            )
            
            result = response.json()
            logger.info(f"Profit reported: {result}")
            return result
            
        except requests.HTTPError as e:
            logger.error(f"Profit report failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in profit report: {e}")
            raise
    
    def get_available_balance(self) -> Dict[str, Any]:
        """
        Get available balance for the agent.
        
        Returns:
            Dict[str, Any]: Available balance information
            
        Raises:
            requests.HTTPError: If the request fails
        """
        try:
            response = self._make_authenticated_request(
                method="GET",
                endpoint="/api/v1/agent/balance"
            )
            
            result = response.json()
            logger.info(f"Available balance: {result}")
            return result
            
        except requests.HTTPError as e:
            logger.error(f"Balance check failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in balance check: {e}")
            raise
    
    def get_pool_state(self) -> Dict[str, Any]:
        """
        Get current pool state from PoolMind.
        
        Returns:
            Dict[str, Any]: Pool state information
            
        Raises:
            requests.HTTPError: If the request fails
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/pool/state",
                timeout=self.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            logger.debug(f"Pool state: {result}")
            return result
            
        except requests.HTTPError as e:
            logger.error(f"Pool state request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in pool state request: {e}")
            raise
    
    def update_nav(self, new_nav: float, profit_amount: float) -> Dict[str, Any]:
        """
        Update pool NAV based on trading profits.
        
        Args:
            new_nav (float): New NAV value
            profit_amount (float): Profit amount to add
            
        Returns:
            Dict[str, Any]: API response
            
        Raises:
            requests.HTTPError: If the request fails
        """
        try:
            data = {
                "new_nav": new_nav,
                "profit_amount": profit_amount,
                "agent_id": self.agent_id
            }
            
            response = self._make_authenticated_request(
                method="POST",
                endpoint="/api/v1/agent/update-nav",
                data=data
            )
            
            result = response.json()
            logger.info(f"NAV updated: {result}")
            return result
            
        except requests.HTTPError as e:
            logger.error(f"NAV update failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in NAV update: {e}")
            raise
    
    def get_agent_performance(self) -> Dict[str, Any]:
        """
        Get agent performance metrics.
        
        Returns:
            Dict[str, Any]: Performance metrics
            
        Raises:
            requests.HTTPError: If the request fails
        """
        try:
            response = self._make_authenticated_request(
                method="GET",
                endpoint="/api/v1/agent/performance"
            )
            
            result = response.json()
            logger.debug(f"Agent performance: {result}")
            return result
            
        except requests.HTTPError as e:
            logger.error(f"Performance request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in performance request: {e}")
            raise
    
    def submit_trade_notification(self, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit trade notification for transparency.
        
        Args:
            trade_data (Dict[str, Any]): Trade execution data
            
        Returns:
            Dict[str, Any]: API response
            
        Raises:
            requests.HTTPError: If the request fails
        """
        try:
            response = self._make_authenticated_request(
                method="POST",
                endpoint="/api/v1/agent/trade-notification",
                data=trade_data
            )
            
            result = response.json()
            logger.info(f"Trade notification submitted: {result}")
            return result
            
        except requests.HTTPError as e:
            logger.error(f"Trade notification failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in trade notification: {e}")
            raise 