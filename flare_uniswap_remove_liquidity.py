#!/usr/bin/env python3
"""
Script to remove liquidity from a Uniswap V3 position on Flare network
"""

import os
import time
import json
from dotenv import load_dotenv
from web3 import Web3
from web3.middleware import geth_poa_middleware
from uniswap import Uniswap
from eth_account import Account

# Load environment variables
load_dotenv()

# Get environment variables
FLARE_RPC_URL = os.getenv("FLARE_RPC_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

# Token addresses on Flare
WFLR_ADDRESS = "0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d"
USDC_ADDRESS = "0xFbDa5F676cB37624f28265A144A48B0d6e87d3b6"

def remove_liquidity(position_id, percent_to_remove=100):
    """
    Remove liquidity from a Uniswap V3 position on Flare network
    
    Args:
        position_id (int): The ID of the position to remove liquidity from
        percent_to_remove (int): Percentage of liquidity to remove (1-100)
        
    Returns:
        dict: Transaction receipt if successful, None otherwise
    """
    # Validate input
    if not isinstance(position_id, int) or position_id <= 0:
        print(f"Invalid position ID: {position_id}")
        return None
    
    if not isinstance(percent_to_remove, (int, float)) or percent_to_remove <= 0 or percent_to_remove > 100:
        print(f"Invalid percent to remove: {percent_to_remove}. Must be between 1 and 100.")
        return None
    
    # Derive wallet address from private key
    account = Account.from_key(PRIVATE_KEY)
    wallet_address = account.address
    print(f"Using wallet address: {wallet_address}")
    
    # Initialize Web3
    web3 = Web3(Web3.HTTPProvider(FLARE_RPC_URL))
    web3.middleware_onion.inject(geth_poa_middleware, layer=0)
    
    print(f"Connected to Flare network: {web3.is_connected()}")
    print(f"Chain ID: {web3.eth.chain_id}")
    
    # Convert address to checksum format
    wallet_address = Web3.to_checksum_address(wallet_address)
    
    # Initialize Uniswap SDK with version 3 for V3 operations
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
    print(f"Using Uniswap V3 Position Manager address: {uniswap.positionManager_addr}")
    
    try:
        # Get the position manager contract
        position_manager = uniswap.nonFungiblePositionManager
        
        # Check if the user owns the position
        try:
            # Get the owner of the position
            owner_of = position_manager.functions.ownerOf(position_id).call()
            if owner_of.lower() != wallet_address.lower():
                print(f"Position {position_id} is not owned by {wallet_address}")
                print(f"Owner: {owner_of}")
                return None
        except Exception as e:
            print(f"Error checking position ownership: {e}")
            print("This could mean the position doesn't exist or has been burned")
            return None
        
        # Get position information
        try:
            position = position_manager.functions.positions(position_id).call()
            print(f"Raw position data: {position}")
            
            # The position data structure on Flare is:
            # [nonce, operator, token0, token1, fee, tickLower, tickUpper, liquidity, ...]
            if len(position) >= 8:
                nonce = position[0]
                operator = position[1]
                token0 = position[2]
                token1 = position[3]
                fee = position[4]
                tick_lower = position[5]
                tick_upper = position[6]
                liquidity = position[7]
                
                print(f"Position {position_id} information:")
                print(f"Nonce: {nonce}")
                print(f"Operator: {operator}")
                print(f"Token0: {token0}")
                print(f"Token1: {token1}")
                print(f"Fee: {fee}")
                print(f"Tick Lower: {tick_lower}")
                print(f"Tick Upper: {tick_upper}")
                print(f"Liquidity: {liquidity}")
                
                # Get token information
                token0_contract = uniswap.get_token(token0)
                token1_contract = uniswap.get_token(token1)
                
                token0_symbol = token0_contract.symbol
                token1_symbol = token1_contract.symbol
                token0_decimals = token0_contract.decimals
                token1_decimals = token1_contract.decimals
                
                print(f"Token0: {token0_symbol} ({token0_decimals} decimals)")
                print(f"Token1: {token1_symbol} ({token1_decimals} decimals)")
                
                # Calculate liquidity to remove
                liquidity_to_remove = int(liquidity * percent_to_remove / 100)
                
                print(f"Total liquidity: {liquidity}")
                print(f"Removing {percent_to_remove}% liquidity: {liquidity_to_remove}")
                
                if liquidity_to_remove <= 0:
                    print("No liquidity to remove")
                    return None
                
                # Set deadline (10 minutes from now)
                deadline = int(time.time() + 600)
                
                # Create the decrease liquidity parameters
                decrease_liquidity_params = {
                    'tokenId': position_id,
                    'liquidity': liquidity_to_remove,
                    'amount0Min': 0,  # No minimum (accepting slippage)
                    'amount1Min': 0,  # No minimum (accepting slippage)
                    'deadline': deadline
                }
                
                print(f"Decrease liquidity parameters: {json.dumps(decrease_liquidity_params, indent=2, default=str)}")
                
                # Get current gas price and estimate gas
                gas_price = web3.eth.gas_price
                print(f"Current gas price: {web3.from_wei(gas_price, 'gwei')} gwei")
                
                try:
                    # Estimate gas for the decrease liquidity transaction
                    gas_estimate = position_manager.functions.decreaseLiquidity(decrease_liquidity_params).estimate_gas({
                        'from': wallet_address,
                    })
                    print(f"Estimated gas for decreaseLiquidity: {gas_estimate}")
                    
                    # Add 20% buffer to gas estimate
                    gas_limit = int(gas_estimate * 1.2)
                except Exception as gas_error:
                    print(f"Error estimating gas for decreaseLiquidity: {gas_error}")
                    # Use a higher gas limit as fallback
                    gas_limit = 500000
                    print(f"Using fallback gas limit: {gas_limit}")
                
                # Build the decrease liquidity transaction
                decrease_tx = position_manager.functions.decreaseLiquidity(decrease_liquidity_params).build_transaction({
                    'from': wallet_address,
                    'gas': gas_limit,
                    'gasPrice': gas_price,
                    'nonce': web3.eth.get_transaction_count(wallet_address),
                })
                
                # Sign and send the transaction
                signed_decrease_tx = web3.eth.account.sign_transaction(decrease_tx, private_key=PRIVATE_KEY)
                tx_hash = web3.eth.send_raw_transaction(signed_decrease_tx.rawTransaction)
                print(f"Decrease liquidity transaction sent with hash: {tx_hash.hex()}")
                
                # Wait for transaction receipt
                print("Waiting for decrease liquidity transaction confirmation...")
                decrease_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
                
                if decrease_receipt.status != 1:
                    print("Decrease liquidity transaction failed!")
                    return None
                
                print("Decrease liquidity transaction successful!")
                
                # Now collect the tokens
                # Create the collect parameters
                collect_params = {
                    'tokenId': position_id,
                    'recipient': wallet_address,
                    'amount0Max': 2**128 - 1,  # Max uint128
                    'amount1Max': 2**128 - 1,  # Max uint128
                }
                
                print(f"Collect parameters: {json.dumps(collect_params, indent=2, default=str)}")
                
                try:
                    # Estimate gas for the collect transaction
                    gas_estimate = position_manager.functions.collect(collect_params).estimate_gas({
                        'from': wallet_address,
                    })
                    print(f"Estimated gas for collect: {gas_estimate}")
                    
                    # Add 20% buffer to gas estimate
                    gas_limit = int(gas_estimate * 1.2)
                except Exception as gas_error:
                    print(f"Error estimating gas for collect: {gas_error}")
                    # Use a higher gas limit as fallback
                    gas_limit = 300000
                    print(f"Using fallback gas limit: {gas_limit}")
                
                # Build the collect transaction
                collect_tx = position_manager.functions.collect(collect_params).build_transaction({
                    'from': wallet_address,
                    'gas': gas_limit,
                    'gasPrice': gas_price,
                    'nonce': web3.eth.get_transaction_count(wallet_address),
                })
                
                # Sign and send the transaction
                signed_collect_tx = web3.eth.account.sign_transaction(collect_tx, private_key=PRIVATE_KEY)
                tx_hash = web3.eth.send_raw_transaction(signed_collect_tx.rawTransaction)
                print(f"Collect transaction sent with hash: {tx_hash.hex()}")
                
                # Wait for transaction receipt
                print("Waiting for collect transaction confirmation...")
                collect_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
                
                if collect_receipt.status != 1:
                    print("Collect transaction failed!")
                    return None
                
                print("Collect transaction successful!")
                
                # If we removed 100% of the liquidity, we can burn the position
                if percent_to_remove == 100:
                    print("Removing 100% of liquidity, burning the position...")
                    
                    try:
                        # Estimate gas for the burn transaction
                        gas_estimate = position_manager.functions.burn(position_id).estimate_gas({
                            'from': wallet_address,
                        })
                        print(f"Estimated gas for burn: {gas_estimate}")
                        
                        # Add 20% buffer to gas estimate
                        gas_limit = int(gas_estimate * 1.2)
                    except Exception as gas_error:
                        print(f"Error estimating gas for burn: {gas_error}")
                        # Use a higher gas limit as fallback
                        gas_limit = 200000
                        print(f"Using fallback gas limit: {gas_limit}")
                    
                    # Build the burn transaction
                    burn_tx = position_manager.functions.burn(position_id).build_transaction({
                        'from': wallet_address,
                        'gas': gas_limit,
                        'gasPrice': gas_price,
                        'nonce': web3.eth.get_transaction_count(wallet_address),
                    })
                    
                    # Sign and send the transaction
                    signed_burn_tx = web3.eth.account.sign_transaction(burn_tx, private_key=PRIVATE_KEY)
                    tx_hash = web3.eth.send_raw_transaction(signed_burn_tx.rawTransaction)
                    print(f"Burn transaction sent with hash: {tx_hash.hex()}")
                    
                    # Wait for transaction receipt
                    print("Waiting for burn transaction confirmation...")
                    burn_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
                    
                    if burn_receipt.status != 1:
                        print("Burn transaction failed!")
                    else:
                        print("Burn transaction successful! Position has been burned.")
                
                # Check token balances after removing liquidity
                token0_balance = uniswap.get_token_balance(token0)
                token1_balance = uniswap.get_token_balance(token1)
                
                print(f"{token0_symbol} Balance after: {token0_balance / (10**token0_decimals)} {token0_symbol}")
                print(f"{token1_symbol} Balance after: {token1_balance / (10**token1_decimals)} {token1_symbol}")
                
                return collect_receipt
            else:
                print(f"Position {position_id} has unexpected data format: {position}")
                return None
                
        except Exception as position_error:
            print(f"Error getting position information: {position_error}")
            return None
        
    except Exception as error:
        print(f"Error: {error}")
        return None

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Remove liquidity from a Uniswap V3 position on Flare network')
    parser.add_argument('position_id', type=int, help='The ID of the position to remove liquidity from')
    parser.add_argument('--percent', type=float, default=100, help='Percentage of liquidity to remove (1-100, default: 100)')
    
    args = parser.parse_args()
    
    remove_liquidity(args.position_id, args.percent) 