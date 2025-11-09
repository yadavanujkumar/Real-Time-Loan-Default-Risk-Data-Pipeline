"""
API client for ingesting data from fintech APIs (RazorpayX, Plaid)
"""
import os
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import time

from ..utils.config_loader import config
from ..utils.logger import setup_logger


logger = setup_logger(__name__)


class FintechAPIClient:
    """Client for interacting with fintech APIs"""
    
    def __init__(self):
        """Initialize API client with credentials"""
        self.api_config = config.api_config
        
        # RazorpayX credentials
        self.razorpay_key = os.getenv('RAZORPAY_KEY_ID')
        self.razorpay_secret = os.getenv('RAZORPAY_KEY_SECRET')
        
        # Plaid credentials
        self.plaid_client_id = os.getenv('PLAID_CLIENT_ID')
        self.plaid_secret = os.getenv('PLAID_SECRET')
        self.plaid_env = os.getenv('PLAID_ENV', 'sandbox')
        
        logger.info("Fintech API client initialized")
    
    def get_razorpay_transactions(
        self,
        start_date: datetime = None,
        end_date: datetime = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Fetch transactions from RazorpayX
        
        Args:
            start_date: Start date for transactions
            end_date: End date for transactions
            limit: Maximum number of transactions
            
        Returns:
            List of transaction records
        """
        if not self.razorpay_key or not self.razorpay_secret:
            logger.warning("RazorpayX credentials not configured")
            return self._generate_mock_transactions(limit)
        
        try:
            base_url = self.api_config.get('razorpayx', {}).get('base_url')
            timeout = self.api_config.get('razorpayx', {}).get('timeout', 30)
            
            params = {'count': limit}
            if start_date:
                params['from'] = int(start_date.timestamp())
            if end_date:
                params['to'] = int(end_date.timestamp())
            
            response = requests.get(
                f"{base_url}/transactions",
                auth=(self.razorpay_key, self.razorpay_secret),
                params=params,
                timeout=timeout
            )
            
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Fetched {len(data.get('items', []))} transactions from RazorpayX")
            return data.get('items', [])
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching RazorpayX transactions: {str(e)}")
            return []
    
    def get_plaid_transactions(
        self,
        access_token: str,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch transactions from Plaid
        
        Args:
            access_token: Plaid access token
            start_date: Start date for transactions
            end_date: End date for transactions
            
        Returns:
            List of transaction records
        """
        if not self.plaid_client_id or not self.plaid_secret:
            logger.warning("Plaid credentials not configured")
            return self._generate_mock_transactions(100)
        
        try:
            base_url = self.api_config.get('plaid', {}).get('base_url')
            timeout = self.api_config.get('plaid', {}).get('timeout', 30)
            
            if not start_date:
                start_date = datetime.now() - timedelta(days=30)
            if not end_date:
                end_date = datetime.now()
            
            payload = {
                'client_id': self.plaid_client_id,
                'secret': self.plaid_secret,
                'access_token': access_token,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d')
            }
            
            response = requests.post(
                f"{base_url}/transactions/get",
                json=payload,
                timeout=timeout
            )
            
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Fetched {len(data.get('transactions', []))} transactions from Plaid")
            return data.get('transactions', [])
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Plaid transactions: {str(e)}")
            return []
    
    def get_plaid_balance(self, access_token: str) -> Dict[str, Any]:
        """
        Get account balance from Plaid
        
        Args:
            access_token: Plaid access token
            
        Returns:
            Account balance information
        """
        if not self.plaid_client_id or not self.plaid_secret:
            logger.warning("Plaid credentials not configured")
            return {}
        
        try:
            base_url = self.api_config.get('plaid', {}).get('base_url')
            timeout = self.api_config.get('plaid', {}).get('timeout', 30)
            
            payload = {
                'client_id': self.plaid_client_id,
                'secret': self.plaid_secret,
                'access_token': access_token
            }
            
            response = requests.post(
                f"{base_url}/accounts/balance/get",
                json=payload,
                timeout=timeout
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Plaid balance: {str(e)}")
            return {}
    
    def _generate_mock_transactions(self, count: int) -> List[Dict[str, Any]]:
        """
        Generate mock transaction data for testing
        
        Args:
            count: Number of transactions to generate
            
        Returns:
            List of mock transactions
        """
        import random
        
        transactions = []
        for i in range(count):
            transactions.append({
                'transaction_id': f'txn_{int(time.time())}_{i}',
                'amount': round(random.uniform(100, 50000), 2),
                'type': random.choice(['credit', 'debit']),
                'category': random.choice(['salary', 'purchase', 'transfer', 'loan_repayment']),
                'timestamp': datetime.now().isoformat(),
                'description': f'Mock transaction {i}',
                'status': 'completed'
            })
        
        logger.info(f"Generated {count} mock transactions")
        return transactions
