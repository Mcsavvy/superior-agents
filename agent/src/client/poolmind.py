import hmac
import hashlib
import json
import time
from typing import Dict, Any, Optional
import requests
from loguru import logger





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
            timestamp (str): Request timestamp (in milliseconds)
            
        Returns:
            str: HMAC signature
        """
        if timestamp is None:
            timestamp = str(int(time.time() * 1000))  # Use milliseconds
        
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
        timestamp = str(int(time.time() * 1000))  # Use milliseconds
        
        # Prepare request body
        body = json.dumps(data) if data else ""
        
        # Generate HMAC signature
        signature = self._generate_hmac_signature(method, endpoint, body, timestamp)
        
        # Set authentication headers - using the correct format from the API spec
        headers = {
            'x-signature': f'sha256={signature}',
            'x-timestamp': timestamp
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
    
    def request_funds(self, recipient_address: str, amount: float, memo: str = None) -> Dict[str, Any]:
        """
        Request funds from PoolMind for arbitrage trading.
        
        Args:
            recipient_address (str): STX address to receive the funds
            amount (float): Amount in STX to transfer
            memo (str, optional): Optional memo for the transfer
            
        Returns:
            Dict[str, Any]: API response with transfer details
            
        Raises:
            requests.HTTPError: If the request fails
        """
        try:
            data = {
                "recipientAddress": recipient_address,
                "amount": amount
            }
            
            if memo:
                data["memo"] = memo
            
            response = self._make_authenticated_request(
                method="POST",
                endpoint="/api/v1/fund-request",
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
    

    
    def get_admin_wallet_info(self) -> Dict[str, Any]:
        """
        Get admin wallet address for reference.
        
        Returns:
            Dict[str, Any]: Admin wallet information
            
        Raises:
            requests.HTTPError: If the request fails
        """
        try:
            response = self._make_authenticated_request(
                method="GET",
                endpoint="/api/v1/fund-request/admin/balance"
            )
            
            result = response.json()
            logger.info(f"Admin wallet info: {result}")
            return result
            
        except requests.HTTPError as e:
            logger.error(f"Admin wallet info request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in admin wallet info request: {e}")
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
            # Pool state endpoint doesn't require authentication per OpenAPI spec
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
    
    def get_pool_info(self) -> Dict[str, Any]:
        """
        Get pool token information including name, symbol, decimals, and total supply.
        
        Returns:
            Dict[str, Any]: Pool token information
            
        Raises:
            requests.HTTPError: If the request fails
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/pool/info",
                timeout=self.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            logger.debug(f"Pool info: {result}")
            return result
            
        except requests.HTTPError as e:
            logger.error(f"Pool info request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in pool info request: {e}")
            raise
    
    def get_current_nav(self) -> Dict[str, Any]:
        """
        Get current Net Asset Value (NAV) of the pool.
        
        Returns:
            Dict[str, Any]: Current NAV information
            
        Raises:
            requests.HTTPError: If the request fails
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/pool/nav",
                timeout=self.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            logger.debug(f"Current NAV: {result}")
            return result
            
        except requests.HTTPError as e:
            logger.error(f"NAV request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in NAV request: {e}")
            raise
    
 