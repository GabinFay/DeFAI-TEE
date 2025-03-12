#!/usr/bin/env python3
"""
Uniswap V3 Pool Information Module for Flare Network

This module provides functions to retrieve detailed information about Uniswap V3 pools
on the Flare network, including liquidity, fees, price ranges, and more.
"""

import os
import sys
import time
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account
from uniswap import Uniswap
import json
import math

# Default fee tiers
FEE_TIER_LOW = 500      # 0.05%
FEE_TIER_MEDIUM = 3000  # 0.3%
FEE_TIER_HIGH = 10000   # 1%

# ERC20 Token ABI (only the necessary parts)
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function",
    },
]

def get_token_info(web3, token_address):
    """Get token information (symbol, name, decimals)"""
    token_contract = web3.eth.contract(address=token_address, abi=ERC20_ABI)
    
    try:
        symbol = token_contract.functions.symbol().call()
        name = token_contract.functions.name().call()
        decimals = token_contract.functions.decimals().call()
        
        return {
            "address": token_address,
            "symbol": symbol,
            "name": name,
            "decimals": decimals
        }
    except Exception as e:
        print(f"Error getting token info for {token_address}: {str(e)}")
        return {
            "address": token_address,
            "symbol": "Unknown",
            "name": "Unknown Token",
            "decimals": 18
        }

def tick_to_price(tick, token0_decimals, token1_decimals):
    """Convert a tick to a price"""
    # In Uniswap V3, the price is calculated as 1.0001^tick
    # This gives the price of token1 in terms of token0
    price = 1.0001 ** tick
    
    # Adjust for token decimals
    decimal_adjustment = 10 ** (token1_decimals - token0_decimals)
    adjusted_price = price * decimal_adjustment
    
    return adjusted_price

def get_pool_info(token0, token1, fee=3000, private_key=None, rpc_url=None):
    """
    Get information about a Uniswap V3 pool on Flare network
    
    Args:
        token0 (str): Address of token0 (must be lower address than token1)
        token1 (str): Address of token1 (must be higher address than token0)
        fee (int): Fee tier (3000 = 0.3%, 500 = 0.05%, 10000 = 1%)
        private_key (str): Private key for the wallet
        rpc_url (str): RPC URL for the Flare network
        
    Returns:
        dict: Pool information
    """
    print(f"Getting pool information for {token0}/{token1} with fee {fee}...")
    
    # Get environment variables if not provided
    if not rpc_url:
        rpc_url = os.getenv("FLARE_RPC_URL")
        if not rpc_url:
            raise ValueError("RPC URL is required. Set FLARE_RPC_URL environment variable or provide rpc_url parameter.")
    
    if not private_key:
        private_key = os.getenv("PRIVATE_KEY")
        if not private_key:
            raise ValueError("Private key is required. Set PRIVATE_KEY environment variable or provide private_key parameter.")
    
    # Derive wallet address from private key
    account = Account.from_key(private_key)
    wallet_address = account.address
    print(f"Using wallet address: {wallet_address}")
    
    # Initialize Web3
    web3 = Web3(Web3.HTTPProvider(rpc_url))
    web3.middleware_onion.inject(geth_poa_middleware, layer=0)
    
    if not web3.is_connected():
        raise ConnectionError(f"Failed to connect to Flare network at {rpc_url}")
    
    print(f"Connected to Flare network: {web3.is_connected()}")
    print(f"Chain ID: {web3.eth.chain_id}")
    
    # Initialize Uniswap SDK
    uniswap = Uniswap(
        address=wallet_address,
        private_key=private_key,
        web3=web3,
        version=3
    )
    
    # Convert addresses to checksum format
    token0_address = Web3.to_checksum_address(token0)
    token1_address = Web3.to_checksum_address(token1)
    
    # Ensure token0 address is less than token1 address (required by Uniswap V3)
    if int(token0_address, 16) > int(token1_address, 16):
        print("Swapping token0 and token1 to ensure token0 < token1")
        token0_address, token1_address = token1_address, token0_address
    
    try:
        # Get token information
        token0_contract = uniswap.get_token(token0_address)
        token1_contract = uniswap.get_token(token1_address)
        
        token0_symbol = token0_contract.symbol
        token1_symbol = token1_contract.symbol
        token0_decimals = token0_contract.decimals
        token1_decimals = token1_contract.decimals
        
        print(f"Token0: {token0_symbol} ({token0_address})")
        print(f"Token1: {token1_symbol} ({token1_address})")
        
        # Get pool instance
        pool = uniswap.get_pool_instance(token0_address, token1_address, fee)
        pool_address = pool.address
        print(f"Pool address: {pool_address}")
        
        # Get pool immutables
        pool_immutables = uniswap.get_pool_immutables(pool)
        print(f"Pool immutables: {json.dumps(pool_immutables, indent=2)}")
        
        # Get pool state
        pool_state = uniswap.get_pool_state(pool)
        print(f"Pool state: {json.dumps(pool_state, indent=2)}")
        
        # Try to get TVL in pool
        tvl_0 = 0
        tvl_1 = 0
        try:
            tvl_0, tvl_1 = uniswap.get_tvl_in_pool(pool)
            print(f"TVL in {token0_symbol}: {tvl_0 / (10**token0_decimals)} {token0_symbol}")
            print(f"TVL in {token1_symbol}: {tvl_1 / (10**token1_decimals)} {token1_symbol}")
        except Exception as tvl_error:
            print(f"Error getting TVL (this is expected on some pools): {tvl_error}")
        
        # Create pool info object
        pool_info = {
            "pool_address": pool_address,
            "token0": {
                "address": token0_address,
                "symbol": token0_symbol,
                "decimals": token0_decimals
            },
            "token1": {
                "address": token1_address,
                "symbol": token1_symbol,
                "decimals": token1_decimals
            },
            "fee": fee,
            "fee_percent": fee / 10000,
            "liquidity": pool_state.get("liquidity", 0),
            "sqrt_price_x96": pool_state.get("sqrtPriceX96", 0),
            "tick": pool_state.get("tick", 0),
            "tvl": {
                "token0": tvl_0 / (10**token0_decimals),
                "token1": tvl_1 / (10**token1_decimals)
            }
        }
        
        return pool_info
    except Exception as e:
        print(f"Error getting pool info: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # This allows the script to be run directly for testing
    import argparse
    
    parser = argparse.ArgumentParser(description='Get Uniswap V3 pool information on Flare network')
    parser.add_argument('--token0', type=str, required=True, help='Address of token0')
    parser.add_argument('--token1', type=str, required=True, help='Address of token1')
    parser.add_argument('--fee', type=int, default=3000, help='Fee tier (3000 = 0.3%, 500 = 0.05%, 10000 = 1%)')
    parser.add_argument('--rpc', type=str, help='RPC URL for the Flare network')
    
    args = parser.parse_args()
    
    pool_info = get_pool_info(args.token0, args.token1, args.fee, rpc_url=args.rpc)
    
    if pool_info:
        print(f"\nPool Information:")
        print(f"Address: {pool_info['pool_address']}")
        print(f"Pair: {pool_info['token0']['symbol']}/{pool_info['token1']['symbol']}")
        print(f"Fee: {pool_info['fee_percent']}%")
        print(f"Liquidity: {pool_info['liquidity']}")
        print(f"Current Tick: {pool_info['tick']}")
        print(f"TVL: {pool_info['tvl']['token0']} {pool_info['token0']['symbol']} and {pool_info['tvl']['token1']} {pool_info['token1']['symbol']}")
    else:
        print("Failed to get pool information or pool does not exist")