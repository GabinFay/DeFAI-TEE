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
    
    # Print the router address being used to verify it's correct
    print(f"Using Uniswap V3 Router address: {uniswap.router.address}")
    print(f"Using Uniswap V3 Quoter address: {uniswap.quoter.address}")
    
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
    
    from flare_uniswap_sdk_swap import swap_tokens
    result = swap_tokens(token_in, token_out, amount_in_eth, fee)
    
    if result:
        print("Swap test successful!")
    else:
        print("Swap test failed!")
    
    return result

def test_get_pool_info(uniswap, token0, token1, fee=3000):
    """Test getting pool information"""
    print(f"\n=== Testing Get Pool Info: {fee} fee tier ===")
    
    # Convert addresses to checksum format
    token0_address = Web3.to_checksum_address(token0)
    token1_address = Web3.to_checksum_address(token1)
    
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
    """Approve token for spending by the router"""
    token_contract = uniswap.get_token(token_address)
    token_symbol = token_contract.symbol
    
    print(f"Approving {token_symbol} for spending...")
    
    # Create ERC20 contract instance
    erc20_abi = '''[{"constant":true,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_from","type":"address"},{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transferFrom","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"}]'''
    token_contract = web3.eth.contract(address=token_address, abi=erc20_abi)
    
    # Check allowance
    allowance = token_contract.functions.allowance(wallet_address, uniswap.router.address).call()
    print(f"Current allowance for router: {allowance}")
    
    # Also check allowance for position manager
    try:
        position_manager_address = uniswap.nonFungiblePositionManager.address
        print(f"Position manager address: {position_manager_address}")
        
        position_manager_allowance = token_contract.functions.allowance(wallet_address, position_manager_address).call()
        print(f"Current allowance for position manager: {position_manager_allowance}")
        
        if position_manager_allowance == 0:
            # Approve tokens for the position manager
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
            
            if approve_receipt.status == 1:
                print("Approval for position manager successful!")
                return True
            else:
                print("Approval for position manager failed!")
                return False
        else:
            print(f"Token {token_symbol} already approved for position manager")
            return True
    except AttributeError as e:
        print(f"Error accessing position manager: {e}")
        print("Falling back to standard approval method")
        
        # Use the standard approve method from the SDK
        try:
            uniswap.approve(token_address)
            print(f"Standard approval for {token_symbol} successful")
            return True
        except Exception as approve_error:
            print(f"Standard approval failed: {approve_error}")
            return False

def test_provide_liquidity(uniswap, web3, wallet_address, token0, token1, amount0, amount1, fee=3000):
    """Test providing liquidity to a pool"""
    print(f"\n=== Testing Provide Liquidity: {amount0} token0, {amount1} token1 ===")
    
    # Convert addresses to checksum format
    token0_address = Web3.to_checksum_address(token0)
    token1_address = Web3.to_checksum_address(token1)
    
    try:
        # Get or create pool instance
        try:
            pool = uniswap.get_pool_instance(token0_address, token1_address, fee)
            print(f"Using existing pool at address: {pool.address}")
        except Exception as e:
            print(f"Pool doesn't exist, creating new pool: {e}")
            pool = uniswap.create_pool_instance(token0_address, token1_address, fee)
            print(f"Created new pool at address: {pool.address}")
        
        # Check token balances before providing liquidity
        token0_contract = uniswap.get_token(token0_address)
        token1_contract = uniswap.get_token(token1_address)
        
        token0_balance_before = uniswap.get_token_balance(token0_address)
        token1_balance_before = uniswap.get_token_balance(token1_address)
        
        print(f"{token0_contract.symbol} Balance before: {token0_balance_before / (10**token0_contract.decimals)} {token0_contract.symbol}")
        print(f"{token1_contract.symbol} Balance before: {token1_balance_before / (10**token1_contract.decimals)} {token1_contract.symbol}")
        
        # Manually approve tokens for the position manager
        approve_token0 = approve_token(uniswap, web3, wallet_address, token0_address)
        approve_token1 = approve_token(uniswap, web3, wallet_address, token1_address)
        
        if not (approve_token0 and approve_token1):
            print("Token approval failed, cannot provide liquidity")
            return None, None
        
        # Convert amounts to wei
        amount0_wei = web3.to_wei(amount0, 'ether') if token0_address == WFLR_ADDRESS else int(amount0 * (10**token0_contract.decimals))
        amount1_wei = web3.to_wei(amount1, 'ether') if token1_address == WFLR_ADDRESS else int(amount1 * (10**token1_contract.decimals))
        
        # Provide liquidity
        print(f"Providing liquidity: {amount0} {token0_contract.symbol} and {amount1} {token1_contract.symbol}")
        print(f"Amount0 in wei: {amount0_wei}")
        print(f"Amount1 in wei: {amount1_wei}")
        
        # Get pool state to determine current tick
        pool_state = uniswap.get_pool_state(pool)
        current_tick = pool_state['tick']
        print(f"Current pool tick: {current_tick}")
        
        # Calculate tick range (wide range around current tick)
        tick_spacing = pool_immutables = uniswap.get_pool_immutables(pool)['tickSpacing']
        tick_lower = current_tick - (tick_spacing * 100)  # 100 tick spacings below current tick
        tick_upper = current_tick + (tick_spacing * 100)  # 100 tick spacings above current tick
        
        # Ensure ticks are multiples of tick spacing
        tick_lower = tick_lower - (tick_lower % tick_spacing)
        tick_upper = tick_upper - (tick_upper % tick_spacing)
        
        print(f"Using tick range: {tick_lower} to {tick_upper}")
        
        # Use mint_liquidity to provide liquidity with specific tick range
        deadline = int(time.time() + 600)  # 10 minutes from now
        
        try:
            tx_receipt = uniswap.mint_liquidity(
                pool,
                amount0_wei,
                amount1_wei,
                tick_lower,
                tick_upper,
                deadline
            )
            
            if tx_receipt.status == 1:
                print("Liquidity provision successful!")
                
                # Check token balances after providing liquidity
                token0_balance_after = uniswap.get_token_balance(token0_address)
                token1_balance_after = uniswap.get_token_balance(token1_address)
                
                print(f"{token0_contract.symbol} Balance after: {token0_balance_after / (10**token0_contract.decimals)} {token0_contract.symbol}")
                print(f"{token1_contract.symbol} Balance after: {token1_balance_after / (10**token1_contract.decimals)} {token1_contract.symbol}")
                
                # Get liquidity positions
                try:
                    positions = uniswap.get_liquidity_positions()
                    print(f"Current liquidity positions: {positions}")
                except Exception as pos_error:
                    print(f"Error getting positions: {pos_error}")
                    positions = []
                
                return tx_receipt, positions
            else:
                print("Liquidity provision failed!")
                return None, None
        except Exception as mint_error:
            print(f"Error in mint_liquidity: {mint_error}")
            traceback.print_exc()
            
            # Try alternative approach with mint_position
            print("Trying alternative approach with mint_position...")
            try:
                tx_hash = uniswap.mint_position(pool, amount0_wei, amount1_wei)
                print(f"Liquidity provision transaction sent with hash: {tx_hash.hex()}")
                
                # Wait for transaction receipt
                print("Waiting for transaction confirmation...")
                tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
                
                if tx_receipt.status == 1:
                    print("Liquidity provision successful!")
                    
                    # Check token balances after providing liquidity
                    token0_balance_after = uniswap.get_token_balance(token0_address)
                    token1_balance_after = uniswap.get_token_balance(token1_address)
                    
                    print(f"{token0_contract.symbol} Balance after: {token0_balance_after / (10**token0_contract.decimals)} {token0_contract.symbol}")
                    print(f"{token1_contract.symbol} Balance after: {token1_balance_after / (10**token1_contract.decimals)} {token1_contract.symbol}")
                    
                    # Get liquidity positions
                    try:
                        positions = uniswap.get_liquidity_positions()
                        print(f"Current liquidity positions: {positions}")
                    except Exception as pos_error:
                        print(f"Error getting positions: {pos_error}")
                        positions = []
                    
                    return tx_receipt, positions
                else:
                    print("Liquidity provision failed!")
                    return None, None
            except Exception as pos_error:
                print(f"Error in mint_position: {pos_error}")
                traceback.print_exc()
                return None, None
    except Exception as e:
        print(f"Error providing liquidity: {e}")
        traceback.print_exc()
        return None, None

def test_remove_liquidity(uniswap, web3, position_id):
    """Test removing liquidity from a pool"""
    print(f"\n=== Testing Remove Liquidity: Position ID {position_id} ===")
    
    try:
        # Set deadline (10 minutes from now)
        deadline = int(time.time() + 600)
        
        # Close position
        print(f"Removing liquidity for position ID: {position_id}")
        tx_receipt = uniswap.close_position(position_id, amount0Min=0, amount1Min=0, deadline=deadline)
        
        if tx_receipt.status == 1:
            print("Liquidity removal successful!")
            
            # Get liquidity positions after removal
            try:
                positions = uniswap.get_liquidity_positions()
                print(f"Remaining liquidity positions: {positions}")
            except Exception as pos_error:
                print(f"Error getting positions after removal: {pos_error}")
            
            return tx_receipt
        else:
            print("Liquidity removal failed!")
            return None
    except Exception as e:
        print(f"Error removing liquidity: {e}")
        traceback.print_exc()
        return None

def main():
    """Main function to run all tests"""
    print("=== Starting Uniswap SDK Tests on Flare Network ===")
    
    # Initialize Uniswap
    uniswap, web3, wallet_address = initialize_uniswap()
    
    # Test token balances
    test_token_balances(uniswap, web3, [WFLR_ADDRESS, USDC_ADDRESS])
    
    # Test getting pool info
    pool = test_get_pool_info(uniswap, WFLR_ADDRESS, USDC_ADDRESS, FEE_TIER_MEDIUM)
    
    # Test swap (small amount)
    swap_result = test_swap(uniswap, WFLR_ADDRESS, USDC_ADDRESS, 0.001, FEE_TIER_MEDIUM)
    
    # Test providing liquidity (small amounts)
    if pool:
        liquidity_result, positions = test_provide_liquidity(
            uniswap, web3, wallet_address, 
            WFLR_ADDRESS, USDC_ADDRESS, 
            0.001, 0.1, 
            FEE_TIER_MEDIUM
        )
        
        # If liquidity provision was successful and we have positions
        if liquidity_result and positions and len(positions) > 0:
            # Wait a bit before removing liquidity
            print("Waiting 10 seconds before removing liquidity...")
            time.sleep(10)
            
            # Test removing liquidity
            remove_result = test_remove_liquidity(uniswap, web3, positions[0])
    
    print("\n=== Uniswap SDK Tests Completed ===")

if __name__ == "__main__":
    main() 