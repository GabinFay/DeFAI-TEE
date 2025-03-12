#!/usr/bin/env python3
"""
Module for getting Uniswap V3 positions on Flare network
"""

import os
import sys
from web3 import Web3
from web3.middleware import geth_poa_middleware
from uniswap import Uniswap
from eth_account import Account

def get_positions(private_key=None, rpc_url=None, wallet_address=None):
    """
    Get all Uniswap V3 positions owned by a wallet on Flare network
    
    Args:
        private_key (str): Private key for the wallet (optional if wallet_address is provided)
        rpc_url (str): RPC URL for the Flare network
        wallet_address (str): Wallet address to get positions for (optional if private_key is provided)
        
    Returns:
        list: List of position details
    """
    print("Getting Uniswap V3 positions...")
    
    # Get environment variables if not provided
    if not rpc_url:
        rpc_url = os.getenv("FLARE_RPC_URL")
        if not rpc_url:
            raise ValueError("RPC URL is required. Set FLARE_RPC_URL environment variable or provide rpc_url parameter.")
    
    # Get wallet address from private key if not provided
    if not wallet_address:
        if not private_key:
            private_key = os.getenv("PRIVATE_KEY")
            if not private_key:
                raise ValueError("Either wallet_address or private_key is required.")
        
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
    
    try:
        # Get the position manager contract
        position_manager = uniswap.nonFungiblePositionManager
        
        # Get the number of positions owned by the wallet
        balance = position_manager.functions.balanceOf(wallet_address).call()
        print(f"Number of positions owned: {balance}")
        
        if balance == 0:
            print("No positions found")
            return []
        
        # Get all position IDs and details
        positions = []
        for i in range(balance):
            try:
                token_id = position_manager.functions.tokenOfOwnerByIndex(wallet_address, i).call()
                print(f"Found position with ID: {token_id}")
                
                # Get position information
                try:
                    position_data = position_manager.functions.positions(token_id).call()
                    
                    # Extract position data
                    if len(position_data) >= 8:
                        nonce = position_data[0]
                        operator = position_data[1]
                        token0 = position_data[2]
                        token1 = position_data[3]
                        fee = position_data[4]
                        tick_lower = position_data[5]
                        tick_upper = position_data[6]
                        liquidity = position_data[7]
                        
                        # Get token symbols if possible
                        token0_symbol = "Unknown"
                        token1_symbol = "Unknown"
                        
                        try:
                            if token0 and token0 != "0x0" and token0 != 0:
                                token0_contract = uniswap.get_token(token0)
                                token0_symbol = token0_contract.symbol
                        except Exception as token0_error:
                            print(f"Error getting token0 info: {token0_error}")
                            
                        try:
                            if token1 and token1 != "0x0" and token1 != 0:
                                token1_contract = uniswap.get_token(token1)
                                token1_symbol = token1_contract.symbol
                        except Exception as token1_error:
                            print(f"Error getting token1 info: {token1_error}")
                        
                        # Get pool information if possible
                        pool_address = None
                        try:
                            pool = uniswap.get_pool_instance(token0, token1, fee)
                            pool_address = pool.address
                        except Exception as pool_error:
                            print(f"Error getting pool info: {pool_error}")
                        
                        # Create position object
                        position = {
                            "position_id": token_id,
                            "token0": {
                                "address": token0,
                                "symbol": token0_symbol
                            },
                            "token1": {
                                "address": token1,
                                "symbol": token1_symbol
                            },
                            "fee": fee,
                            "fee_percent": fee / 10000,
                            "tick_lower": tick_lower,
                            "tick_upper": tick_upper,
                            "liquidity": liquidity,
                            "pool_address": pool_address
                        }
                        
                        positions.append(position)
                        
                        print(f"Position {token_id}:")
                        print(f"  Token0: {token0_symbol} ({token0})")
                        print(f"  Token1: {token1_symbol} ({token1})")
                        print(f"  Fee: {fee} ({fee/10000}%)")
                        print(f"  Liquidity: {liquidity}")
                    else:
                        print(f"Position {token_id} has unexpected data format")
                except Exception as position_error:
                    print(f"Error getting position {token_id} details: {position_error}")
            except Exception as token_error:
                print(f"Error getting token ID at index {i}: {token_error}")
        
        return positions
    except Exception as e:
        print(f"Error getting positions: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    # This allows the script to be run directly for testing
    import argparse
    
    parser = argparse.ArgumentParser(description='Get Uniswap V3 positions on Flare network')
    parser.add_argument('--address', type=str, help='Wallet address to get positions for')
    parser.add_argument('--rpc', type=str, help='RPC URL for the Flare network')
    
    args = parser.parse_args()
    
    positions = get_positions(wallet_address=args.address, rpc_url=args.rpc)
    
    if positions:
        print(f"\nFound {len(positions)} positions:")
        for pos in positions:
            print(f"Position ID: {pos['position_id']}")
            print(f"  Pair: {pos['token0']['symbol']}/{pos['token1']['symbol']}")
            print(f"  Fee: {pos['fee_percent']}%")
            print(f"  Liquidity: {pos['liquidity']}")
            print("")
    else:
        print("No positions found or error occurred") 