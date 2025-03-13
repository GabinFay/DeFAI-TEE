#!/usr/bin/env python3
"""
Script to check if the Flare network addresses are correctly set in the uniswap-python SDK
"""

import os
from dotenv import load_dotenv
from web3 import Web3
from web3.middleware import geth_poa_middleware
from uniswap import Uniswap
from eth_account import Account

def check_flare_addresses():
    """
    Check if the Flare network addresses are correctly set in the uniswap-python SDK
    """
    # Load environment variables
    load_dotenv()
    
    # Get environment variables
    FLARE_RPC_URL = os.getenv("FLARE_RPC_URL")
    PRIVATE_KEY = os.getenv("PRIVATE_KEY")
    
    # Derive wallet address from private key
    account = Account.from_key(PRIVATE_KEY)
    wallet_address = account.address
    print(f"Using wallet address: {wallet_address}")
    
    # Initialize Web3
    web3 = Web3(Web3.HTTPProvider(FLARE_RPC_URL))
    web3.middleware_onion.inject(geth_poa_middleware, layer=0)
    
    print(f"Connected to Flare network: {web3.is_connected()}")
    print(f"Chain ID: {web3.eth.chain_id}")
    
    # Initialize Uniswap SDK with version 3 for V3 swaps
    uniswap = Uniswap(
        address=wallet_address,
        private_key=PRIVATE_KEY,
        web3=web3,
        version=3
    )
    
    # Check if the router address is correctly set
    print("\nChecking Uniswap V3 contract addresses on Flare network:")
    print(f"Router address: {uniswap.router.address}")
    print(f"Quoter address: {uniswap.quoter.address}")
    
    # Expected addresses
    expected_router = "0x8a1E35F5c98C4E85B36B7B253222eE17773b2781"
    expected_quoter = "0x5B5513c55fd06e2658010c121c37b07fC8e8B705"
    
    # Check if the addresses match
    print("\nVerifying addresses:")
    print(f"Router address matches: {uniswap.router.address.lower() == expected_router.lower()}")
    print(f"Quoter address matches: {uniswap.quoter.address.lower() == expected_quoter.lower()}")
    
    # Print the correct addresses
    print("\nCorrect addresses for Flare network:")
    print(f"Router address should be: {expected_router}")
    print(f"Quoter address should be: {expected_quoter}")
    
    # Check if the SDK is using the correct network
    print(f"\nSDK is using network with chain ID: {web3.eth.chain_id}")
    print("Flare network chain ID should be: 14")

if __name__ == "__main__":
    check_flare_addresses() 