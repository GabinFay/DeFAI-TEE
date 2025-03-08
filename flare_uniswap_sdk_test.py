#!/usr/bin/env python3
"""
Comprehensive test script for Uniswap V3 on Flare network
Tests various functionalities including:
- Swapping tokens
- Providing liquidity
- Removing liquidity
- Fetching pool information
"""

import os
import time
import traceback
import argparse
from dotenv import load_dotenv
from web3 import Web3
from web3.middleware import geth_poa_middleware
from uniswap import Uniswap
from eth_account import Account
import json

# Load environment variables
load_dotenv()

# Get environment variables
FLARE_RPC_URL = os.getenv("FLARE_RPC_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

# Token addresses on Flare
WFLR_ADDRESS = "0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d"
USDC_ADDRESS = "0xFbDa5F676cB37624f28265A144A48B0d6e87d3b6"

# Fee tiers
FEE_TIER_LOW = 500      # 0.05%
FEE_TIER_MEDIUM = 3000  # 0.3%
FEE_TIER_HIGH = 10000   # 1%

def initialize_uniswap():
    """Initialize Uniswap SDK with Flare network"""
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
        version=3,
        default_slippage=0.01  # 1% slippage
    )
    
    # Print the contract addresses being used to verify they're correct
    print(f"Using Uniswap V3 Router address: {uniswap.router.address}")
    print(f"Using Uniswap V3 Factory address: {uniswap.factory_contract.address}")
    print(f"Using Uniswap V3 Quoter address: {uniswap.quoter.address}")
    print(f"Using Uniswap V3 Position Manager address: {uniswap.positionManager_addr}")
    print(f"Using wrapped native token address: {uniswap.wrapped_native_token_addr}")
    
    return uniswap, web3, wallet_address

def test_token_balances(uniswap, web3, token_addresses):
    """Test getting token balances"""
    print("\n=== Testing Token Balances ===")
    
    for token_address in token_addresses:
        token_contract = uniswap.get_token(token_address)
        token_symbol = token_contract.symbol
        token_decimals = token_contract.decimals
        
        balance = uniswap.get_token_balance(token_address)
        print(f"{token_symbol} Balance: {balance / (10**token_decimals)} {token_symbol}")

def test_swap(uniswap, token_in, token_out, amount_in_eth, fee=3000):
    """Test swapping tokens"""
    print(f"\n=== Testing Swap: {amount_in_eth} tokens ===")
    
    try:
        from flare_uniswap_sdk_swap import swap_tokens
        result = swap_tokens(token_in, token_out, amount_in_eth, fee)
        
        if result:
            print("Swap test successful!")
        else:
            print("Swap test failed!")
        
        return result
    except ImportError:
        print("flare_uniswap_sdk_swap module not found. Skipping swap test.")
        return None

def test_get_pool_info(uniswap, token0, token1, fee=3000):
    """Test getting pool information"""
    print(f"\n=== Testing Get Pool Info: {fee} fee tier ===")
    
    # Convert addresses to checksum format
    token0_address = Web3.to_checksum_address(token0)
    token1_address = Web3.to_checksum_address(token1)
    
    # Ensure token0 address is less than token1 address (required by Uniswap V3)
    if int(token0_address, 16) > int(token1_address, 16):
        print("Swapping token0 and token1 to ensure token0 < token1")
        token0_address, token1_address = token1_address, token0_address
    
    try:
        # Get pool instance
        pool = uniswap.get_pool_instance(token0_address, token1_address, fee)
        print(f"Pool address: {pool.address}")
        
        # Get pool immutables
        pool_immutables = uniswap.get_pool_immutables(pool)
        print(f"Pool immutables: {json.dumps(pool_immutables, indent=2)}")
        
        # Get pool state
        pool_state = uniswap.get_pool_state(pool)
        print(f"Pool state: {json.dumps(pool_state, indent=2)}")
        
        # Try to get TVL in pool, but handle errors gracefully
        try:
            tvl_0, tvl_1 = uniswap.get_tvl_in_pool(pool)
            token0_contract = uniswap.get_token(token0_address)
            token1_contract = uniswap.get_token(token1_address)
            
            print(f"TVL in {token0_contract.symbol}: {tvl_0}")
            print(f"TVL in {token1_contract.symbol}: {tvl_1}")
        except Exception as tvl_error:
            print(f"Error getting TVL (this is expected on some pools): {tvl_error}")
        
        return pool
    except Exception as e:
        print(f"Error getting pool info: {e}")
        traceback.print_exc()
        return None

def approve_token(uniswap, web3, wallet_address, token_address):
    """Approve token for spending by the router and position manager"""
    token_contract = uniswap.get_token(token_address)
    token_symbol = token_contract.symbol
    
    print(f"Approving {token_symbol} for spending...")
    
    # Create ERC20 contract instance
    erc20_abi = '''[{"constant":true,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_from","type":"address"},{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transferFrom","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"}]'''
    token_contract = web3.eth.contract(address=token_address, abi=erc20_abi)
    
    # Check allowance for router
    router_allowance = token_contract.functions.allowance(wallet_address, uniswap.router.address).call()
    print(f"Current allowance for router: {router_allowance}")
    
    # Check allowance for position manager
    position_manager_address = uniswap.positionManager_addr
    print(f"Position manager address: {position_manager_address}")
    
    position_manager_allowance = token_contract.functions.allowance(wallet_address, position_manager_address).call()
    print(f"Current allowance for position manager: {position_manager_allowance}")
    
    # Approve for router if needed
    if router_allowance == 0:
        print(f"Approving {token_symbol} for router...")
        approve_tx = token_contract.functions.approve(
            uniswap.router.address,
            2**256 - 1  # Max approval
        ).build_transaction({
            'from': wallet_address,
            'gas': 200000,
            'gasPrice': web3.eth.gas_price,
            'nonce': web3.eth.get_transaction_count(wallet_address),
        })
        
        # Sign transaction
        signed_txn = web3.eth.account.sign_transaction(approve_tx, private_key=PRIVATE_KEY)
        
        # Send transaction
        print(f"Sending approval transaction for router...")
        approve_tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        print(f"Approval transaction sent with hash: {approve_tx_hash.hex()}")
        
        # Wait for transaction receipt
        print("Waiting for approval confirmation...")
        approve_receipt = web3.eth.wait_for_transaction_receipt(approve_tx_hash)
        
        if approve_receipt.status != 1:
            print("Approval for router failed!")
            return False
        
        print("Approval for router successful!")
    else:
        print(f"Token {token_symbol} already approved for router")
    
    # Approve for position manager if needed
    if position_manager_allowance == 0:
        print(f"Approving {token_symbol} for position manager...")
        approve_tx = token_contract.functions.approve(
            position_manager_address,
            2**256 - 1  # Max approval
        ).build_transaction({
            'from': wallet_address,
            'gas': 200000,
            'gasPrice': web3.eth.gas_price,
            'nonce': web3.eth.get_transaction_count(wallet_address),
        })
        
        # Sign transaction
        signed_txn = web3.eth.account.sign_transaction(approve_tx, private_key=PRIVATE_KEY)
        
        # Send transaction
        print(f"Sending approval transaction for position manager...")
        approve_tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        print(f"Approval transaction sent with hash: {approve_tx_hash.hex()}")
        
        # Wait for transaction receipt
        print("Waiting for approval confirmation...")
        approve_receipt = web3.eth.wait_for_transaction_receipt(approve_tx_hash)
        
        if approve_receipt.status != 1:
            print("Approval for position manager failed!")
            return False
        
        print("Approval for position manager successful!")
    else:
        print(f"Token {token_symbol} already approved for position manager")
    
    return True

def test_provide_liquidity(uniswap, web3, wallet_address, token0, token1, amount0, amount1, fee=3000):
    """Test providing liquidity to a pool"""
    print(f"\n=== Testing Provide Liquidity: {amount0} token0, {amount1} token1 ===")
    
    try:
        from flare_uniswap_add_liquidity import add_liquidity
        result = add_liquidity(token0, token1, amount0, amount1, fee)
        
        if result:
            print("Provide liquidity test successful!")
            
            # Try to get the token ID from the transaction logs
            try:
                # Parse the logs to find the token ID
                logs = uniswap.nonFungiblePositionManager.events.IncreaseLiquidity().process_receipt(result)
                if logs:
                    token_id = logs[0]['args']['tokenId']
                    print(f"Position created with token ID: {token_id}")
                    return token_id
            except Exception as log_error:
                print(f"Error parsing logs: {log_error}")
                
            return True
        else:
            print("Provide liquidity test failed!")
            return None
    except ImportError:
        print("flare_uniswap_add_liquidity module not found. Skipping provide liquidity test.")
        return None

def test_remove_liquidity(uniswap, web3, position_id, percent_to_remove=100):
    """Test removing liquidity from a position"""
    print(f"\n=== Testing Remove Liquidity: Position ID {position_id}, {percent_to_remove}% ===")
    
    try:
        from flare_uniswap_remove_liquidity import remove_liquidity
        result = remove_liquidity(position_id, percent_to_remove)
        
        if result:
            print("Remove liquidity test successful!")
            return True
        else:
            print("Remove liquidity test failed!")
            return None
    except ImportError:
        print("flare_uniswap_remove_liquidity module not found. Skipping remove liquidity test.")
        return None

def test_get_positions(uniswap, web3, wallet_address):
    """Test getting all positions owned by the wallet"""
    print("\n=== Testing Get Positions ===")
    
    try:
        # Get the position manager contract
        position_manager = uniswap.nonFungiblePositionManager
        
        # Get the number of positions owned by the wallet
        balance = position_manager.functions.balanceOf(wallet_address).call()
        print(f"Number of positions owned: {balance}")
        
        if balance == 0:
            print("No positions found")
            return []
        
        # Get all position IDs
        position_ids = []
        for i in range(balance):
            try:
                token_id = position_manager.functions.tokenOfOwnerByIndex(wallet_address, i).call()
                position_ids.append(token_id)
                print(f"Found position with ID: {token_id}")
                
                # Get position information
                try:
                    position = position_manager.functions.positions(token_id).call()
                    print(f"Raw position data: {position}")
                    
                    # The position data structure on Flare seems to be different
                    # Based on the output, it appears the structure is:
                    # [nonce, operator, token0, token1, fee, tickLower, tickUpper, liquidity, ...]
                    
                    # Extract position data safely
                    if len(position) >= 8:
                        # Adjust indices based on observed data structure
                        nonce = position[0]
                        operator = position[1]
                        token0 = position[2]
                        token1 = position[3]
                        fee = position[4]
                        tick_lower = position[5]
                        tick_upper = position[6]
                        liquidity = position[7]
                        
                        print(f"Position {token_id}:")
                        print(f"  Nonce: {nonce}")
                        print(f"  Operator: {operator}")
                        print(f"  Token0: {token0}")
                        print(f"  Token1: {token1}")
                        print(f"  Fee: {fee}")
                        print(f"  Tick Lower: {tick_lower}")
                        print(f"  Tick Upper: {tick_upper}")
                        print(f"  Liquidity: {liquidity}")
                        
                        # Try to get token information if addresses are valid
                        try:
                            if token0 and token0 != "0x0" and token0 != 0:
                                token0_contract = uniswap.get_token(token0)
                                print(f"  Token0 Symbol: {token0_contract.symbol}")
                        except Exception as token0_error:
                            print(f"  Error getting token0 info: {token0_error}")
                            
                        try:
                            if token1 and token1 != "0x0" and token1 != 0:
                                token1_contract = uniswap.get_token(token1)
                                print(f"  Token1 Symbol: {token1_contract.symbol}")
                        except Exception as token1_error:
                            print(f"  Error getting token1 info: {token1_error}")
                    else:
                        print(f"Position {token_id} has unexpected data format: {position}")
                except Exception as position_error:
                    print(f"Error getting position {token_id} details: {position_error}")
            except Exception as token_error:
                print(f"Error getting token ID at index {i}: {token_error}")
        
        return position_ids
    except Exception as e:
        print(f"Error getting positions: {e}")
        traceback.print_exc()
        return []

def main():
    """Main function to run all tests"""
    parser = argparse.ArgumentParser(description='Test Uniswap V3 on Flare network')
    parser.add_argument('--swap', action='store_true', help='Test swapping tokens')
    parser.add_argument('--pool', action='store_true', help='Test getting pool information')
    parser.add_argument('--positions', action='store_true', help='Test getting positions')
    parser.add_argument('--provide', action='store_true', help='Test providing liquidity')
    parser.add_argument('--remove', type=int, help='Test removing liquidity from position ID')
    parser.add_argument('--percent', type=float, default=100, help='Percentage of liquidity to remove (1-100, default: 100)')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    
    args = parser.parse_args()
    
    # Initialize Uniswap
    uniswap, web3, wallet_address = initialize_uniswap()
    
    # Test token balances
    token_addresses = [WFLR_ADDRESS, USDC_ADDRESS]
    test_token_balances(uniswap, web3, token_addresses)
    
    # Test getting pool information
    if args.pool or args.all:
        pool = test_get_pool_info(uniswap, WFLR_ADDRESS, USDC_ADDRESS, FEE_TIER_MEDIUM)
    
    # Test getting positions
    if args.positions or args.all:
        position_ids = test_get_positions(uniswap, web3, wallet_address)
    
    # Test swapping tokens
    if args.swap or args.all:
        # Swap a small amount of WFLR for USDC
        test_swap(uniswap, WFLR_ADDRESS, USDC_ADDRESS, 0.01, FEE_TIER_MEDIUM)
    
    # Test providing liquidity
    if args.provide or args.all:
        # Ensure token0 address is less than token1 address (required by Uniswap V3)
        if int(WFLR_ADDRESS, 16) < int(USDC_ADDRESS, 16):
            token0 = WFLR_ADDRESS
            token1 = USDC_ADDRESS
            # Provide a small amount of liquidity
            amount0 = 0.01  # 0.01 WFLR
            amount1 = 0.01  # 0.01 USDC
        else:
            token0 = USDC_ADDRESS
            token1 = WFLR_ADDRESS
            # Provide a small amount of liquidity
            amount0 = 0.01  # 0.01 USDC
            amount1 = 0.01  # 0.01 WFLR
        
        # Approve tokens first
        approve_token(uniswap, web3, wallet_address, token0)
        approve_token(uniswap, web3, wallet_address, token1)
        
        # Provide liquidity
        position_id = test_provide_liquidity(uniswap, web3, wallet_address, token0, token1, amount0, amount1, FEE_TIER_MEDIUM)
    
    # Test removing liquidity
    if args.remove:
        test_remove_liquidity(uniswap, web3, args.remove, args.percent)

if __name__ == "__main__":
    main() 