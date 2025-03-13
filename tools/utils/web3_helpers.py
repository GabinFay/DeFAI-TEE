"""
Web3 helper utilities for Flare Bot.
"""

from web3 import Web3
from eth_account import Account
from web3.middleware import geth_poa_middleware
import os

from ..constants import DEFAULT_FLARE_RPC_URL

def get_web3(rpc_url=None):
    """
    Get a Web3 instance connected to the Flare network
    
    Args:
        rpc_url: Optional RPC URL to use. If not provided, uses the default.
        
    Returns:
        Web3: A Web3 instance connected to the Flare network
    """
    if not rpc_url:
        rpc_url = os.getenv("FLARE_RPC_URL", DEFAULT_FLARE_RPC_URL)
    
    web3 = Web3(Web3.HTTPProvider(rpc_url))
    web3.middleware_onion.inject(geth_poa_middleware, layer=0)
    
    return web3

def get_account_from_private_key(private_key=None):
    """
    Get an Account instance from a private key
    
    Args:
        private_key: Optional private key to use. If not provided, tries to get from environment.
        
    Returns:
        tuple: (Account instance, wallet address)
    """
    if not private_key:
        private_key = os.getenv("PRIVATE_KEY")
        if not private_key:
            raise ValueError("Private key not provided and not found in environment")
    
    account = Account.from_key(private_key)
    wallet_address = account.address
    
    return account, wallet_address 