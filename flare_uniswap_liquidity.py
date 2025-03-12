#!/usr/bin/env python3
"""
Functions for adding and removing liquidity on Uniswap V3 pools on Flare network
"""

import os
import time
import json
from web3 import Web3
from web3.middleware import geth_poa_middleware
from uniswap import Uniswap
from eth_account import Account

def add_liquidity(token0, token1, amount0, amount1, fee=3000, private_key=None, rpc_url=None):
    """
    Add liquidity to a Uniswap V3 pool on Flare network
    
    Args:
        token0 (str): Address of token0 (must be lower address than token1)
        token1 (str): Address of token1 (must be higher address than token1)
        amount0 (float): Amount of token0 in token units
        amount1 (float): Amount of token1 in token units
        fee (int): Fee tier (3000 = 0.3%, 500 = 0.05%, 10000 = 1%)
        private_key (str): Private key for the wallet (if not provided, uses env var)
        rpc_url (str): RPC URL for Flare network (if not provided, uses env var)
        
    Returns:
        dict: Result with transaction hash and status
    """
    # Get private key and RPC URL
    if not private_key:
        private_key = os.getenv("PRIVATE_KEY")
    if not rpc_url:
        rpc_url = os.getenv("FLARE_RPC_URL", "https://flare-api.flare.network/ext/C/rpc")
    
    if not private_key:
        return {
            "success": False,
            "message": "No private key provided"
        }
    
    # Derive wallet address from private key
    account = Account.from_key(private_key)
    wallet_address = account.address
    print(f"Using wallet address: {wallet_address}")
    
    # Initialize Web3
    web3 = Web3(Web3.HTTPProvider(rpc_url))
    web3.middleware_onion.inject(geth_poa_middleware, layer=0)
    
    if not web3.is_connected():
        return {
            "success": False,
            "message": f"Failed to connect to Flare network at {rpc_url}"
        }
    
    print(f"Connected to Flare network: {web3.is_connected()}")
    print(f"Chain ID: {web3.eth.chain_id}")
    
    # Convert addresses to checksum format
    token0_address = Web3.to_checksum_address(token0)
    token1_address = Web3.to_checksum_address(token1)
    wallet_address = Web3.to_checksum_address(wallet_address)
    
    # Verify token0 address is less than token1 address (required by Uniswap V3)
    if int(token0_address, 16) > int(token1_address, 16):
        return {
            "success": False,
            "message": "token0 address must be less than token1 address"
        }
    
    # Initialize Uniswap SDK with version 3 for V3 swaps
    uniswap = Uniswap(
        address=wallet_address,
        private_key=private_key,
        web3=web3,
        version=3,
        default_slippage=0.01  # 1% slippage
    )
    
    try:
        # Get pool instance
        pool = uniswap.get_pool_instance(token0_address, token1_address, fee)
        print(f"Pool address: {pool.address}")
        
        # Get pool immutables and state
        pool_immutables = uniswap.get_pool_immutables(pool)
        pool_state = uniswap.get_pool_state(pool)
        
        # Get token contracts
        token0_contract = uniswap.get_token(token0_address)
        token1_contract = uniswap.get_token(token1_address)
        
        # Get token information
        token0_symbol = token0_contract.symbol
        token1_symbol = token1_contract.symbol
        token0_decimals = token0_contract.decimals
        token1_decimals = token1_contract.decimals
        
        print(f"Token0: {token0_symbol} ({token0_decimals} decimals)")
        print(f"Token1: {token1_symbol} ({token1_decimals} decimals)")
        
        # Check token balances
        token0_balance = uniswap.get_token_balance(token0_address)
        token1_balance = uniswap.get_token_balance(token1_address)
        
        print(f"{token0_symbol} Balance: {token0_balance / (10**token0_decimals)} {token0_symbol}")
        print(f"{token1_symbol} Balance: {token1_balance / (10**token1_decimals)} {token1_symbol}")
        
        # Convert amounts to wei
        amount0_wei = web3.to_wei(amount0, 'ether') if token0_decimals == 18 else int(amount0 * (10**token0_decimals))
        amount1_wei = web3.to_wei(amount1, 'ether') if token1_decimals == 18 else int(amount1 * (10**token1_decimals))
        
        print(f"Amount0 in wei: {amount0_wei}")
        print(f"Amount1 in wei: {amount1_wei}")
        
        if token0_balance < amount0_wei:
            return {
                "success": False,
                "message": f"Insufficient {token0_symbol} balance. You have {token0_balance / (10**token0_decimals)} but trying to add {amount0}"
            }
        
        if token1_balance < amount1_wei:
            return {
                "success": False,
                "message": f"Insufficient {token1_symbol} balance. You have {token1_balance / (10**token1_decimals)} but trying to add {amount1}"
            }
        
        # Approve tokens if needed
        # Create ERC20 contract instances
        erc20_abi = '''[{"constant":true,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_from","type":"address"},{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transferFrom","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"}]'''
        token0_contract_web3 = web3.eth.contract(address=token0_address, abi=erc20_abi)
        token1_contract_web3 = web3.eth.contract(address=token1_address, abi=erc20_abi)
        
        # Get the position manager address
        position_manager_address = uniswap.nonFungiblePositionManager.address
        print(f"Position Manager address: {position_manager_address}")
        
        # Check allowances
        token0_allowance = token0_contract_web3.functions.allowance(wallet_address, position_manager_address).call()
        token1_allowance = token1_contract_web3.functions.allowance(wallet_address, position_manager_address).call()
        
        # Approve token0 if needed
        if token0_allowance < amount0_wei:
            print(f"Approving {token0_symbol} for Position Manager...")
            approve_tx = token0_contract_web3.functions.approve(
                position_manager_address,
                2**256 - 1  # Max approval
            ).build_transaction({
                'from': wallet_address,
                'gas': 200000,
                'gasPrice': web3.eth.gas_price,
                'nonce': web3.eth.get_transaction_count(wallet_address),
            })
            
            # Sign transaction
            signed_txn = web3.eth.account.sign_transaction(approve_tx, private_key=private_key)
            
            # Send transaction
            approve_tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            print(f"Approval transaction sent with hash: {approve_tx_hash.hex()}")
            
            # Wait for transaction receipt
            approve_receipt = web3.eth.wait_for_transaction_receipt(approve_tx_hash)
            
            if approve_receipt.status != 1:
                return {
                    "success": False,
                    "message": f"Approval for {token0_symbol} failed!"
                }
            
            print(f"Approval for {token0_symbol} successful!")
        
        # Approve token1 if needed
        if token1_allowance < amount1_wei:
            print(f"Approving {token1_symbol} for Position Manager...")
            approve_tx = token1_contract_web3.functions.approve(
                position_manager_address,
                2**256 - 1  # Max approval
            ).build_transaction({
                'from': wallet_address,
                'gas': 200000,
                'gasPrice': web3.eth.gas_price,
                'nonce': web3.eth.get_transaction_count(wallet_address),
            })
            
            # Sign transaction
            signed_txn = web3.eth.account.sign_transaction(approve_tx, private_key=private_key)
            
            # Send transaction
            approve_tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            print(f"Approval transaction sent with hash: {approve_tx_hash.hex()}")
            
            # Wait for transaction receipt
            approve_receipt = web3.eth.wait_for_transaction_receipt(approve_tx_hash)
            
            if approve_receipt.status != 1:
                return {
                    "success": False,
                    "message": f"Approval for {token1_symbol} failed!"
                }
            
            print(f"Approval for {token1_symbol} successful!")
        
        # Calculate tick range (wide range around current tick)
        current_tick = pool_state['tick']
        tick_spacing = pool_immutables['tickSpacing']
        
        # Create a narrower position (50 tick spacings in each direction)
        tick_lower = current_tick - (tick_spacing * 50)
        tick_upper = current_tick + (tick_spacing * 50)
        
        # Ensure ticks are multiples of tick spacing
        tick_lower = tick_lower - (tick_lower % tick_spacing)
        tick_upper = tick_upper - (tick_upper % tick_spacing)
        
        print(f"Current tick: {current_tick}")
        print(f"Using tick range: {tick_lower} to {tick_upper}")
        
        # Set deadline (10 minutes from now)
        deadline = int(time.time() + 600)
        
        # Create the mint parameters
        mint_params = {
            'token0': token0_address,
            'token1': token1_address,
            'fee': fee,
            'tickLower': tick_lower,
            'tickUpper': tick_upper,
            'amount0Desired': amount0_wei,
            'amount1Desired': amount1_wei,
            'amount0Min': 0,  # No minimum (accepting slippage)
            'amount1Min': 0,  # No minimum (accepting slippage)
            'recipient': wallet_address,
            'deadline': deadline
        }
        
        # Get the position manager contract
        position_manager = uniswap.nonFungiblePositionManager
        
        # Get current gas price and estimate gas
        gas_price = web3.eth.gas_price
        
        try:
            # Estimate gas for the mint transaction
            gas_estimate = position_manager.functions.mint(mint_params).estimate_gas({
                'from': wallet_address,
            })
            
            # Add 20% buffer to gas estimate
            gas_limit = int(gas_estimate * 1.2)
        except Exception as gas_error:
            print(f"Error estimating gas: {gas_error}")
            # Use a higher gas limit as fallback
            gas_limit = 1000000
        
        # Build the mint transaction
        mint_tx = position_manager.functions.mint(mint_params).build_transaction({
            'from': wallet_address,
            'gas': gas_limit,
            'gasPrice': gas_price,
            'nonce': web3.eth.get_transaction_count(wallet_address),
        })
        
        # Sign and send the transaction
        signed_mint_tx = web3.eth.account.sign_transaction(mint_tx, private_key=private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_mint_tx.rawTransaction)
        print(f"Mint transaction sent with hash: {tx_hash.hex()}")
        
        # Wait for transaction receipt
        print("Waiting for transaction confirmation...")
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        
        if tx_receipt.status == 1:
            print("Liquidity provision successful!")
            
            # Try to parse the logs to get the token ID
            token_id = None
            liquidity = None
            amount0_used = None
            amount1_used = None
            
            try:
                # Get the IncreaseLiquidity event logs
                logs = position_manager.events.IncreaseLiquidity().process_receipt(tx_receipt)
                if logs:
                    token_id = logs[0]['args']['tokenId']
                    liquidity = logs[0]['args']['liquidity']
                    amount0_used = logs[0]['args']['amount0']
                    amount1_used = logs[0]['args']['amount1']
            except Exception as log_error:
                print(f"Error parsing logs: {log_error}")
            
            return {
                "success": True,
                "transaction_hash": tx_hash.hex(),
                "token_id": str(token_id) if token_id else None,
                "liquidity": str(liquidity) if liquidity else None,
                "amount0_used": str(amount0_used) if amount0_used else str(amount0_wei),
                "amount1_used": str(amount1_used) if amount1_used else str(amount1_wei),
                "token0": token0_address,
                "token1": token1_address,
                "token0_symbol": token0_symbol,
                "token1_symbol": token1_symbol,
                "fee": fee
            }
        else:
            return {
                "success": False,
                "message": "Liquidity provision failed!",
                "transaction_hash": tx_hash.hex()
            }
            
    except Exception as error:
        return {
            "success": False,
            "message": f"Error: {str(error)}"
        }

def remove_liquidity(position_id, percent_to_remove=100, private_key=None, rpc_url=None):
    """
    Remove liquidity from a Uniswap V3 position on Flare network
    
    Args:
        position_id (int): The ID of the position to remove liquidity from
        percent_to_remove (float): Percentage of liquidity to remove (1-100)
        private_key (str): Private key for the wallet (if not provided, uses env var)
        rpc_url (str): RPC URL for Flare network (if not provided, uses env var)
        
    Returns:
        dict: Result with transaction hash and status
    """
    # Get private key and RPC URL
    if not private_key:
        private_key = os.getenv("PRIVATE_KEY")
    if not rpc_url:
        rpc_url = os.getenv("FLARE_RPC_URL", "https://flare-api.flare.network/ext/C/rpc")
    
    if not private_key:
        return {
            "success": False,
            "message": "No private key provided"
        }
    
    # Derive wallet address from private key
    account = Account.from_key(private_key)
    wallet_address = account.address
    print(f"Using wallet address: {wallet_address}")
    
    # Initialize Web3
    web3 = Web3(Web3.HTTPProvider(rpc_url))
    web3.middleware_onion.inject(geth_poa_middleware, layer=0)
    
    if not web3.is_connected():
        return {
            "success": False,
            "message": f"Failed to connect to Flare network at {rpc_url}"
        }
    
    # Convert position_id to int if it's a string
    if isinstance(position_id, str):
        position_id = int(position_id)
    
    # Ensure percent_to_remove is between 1 and 100
    percent_to_remove = max(1, min(100, float(percent_to_remove)))
    
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
        
        # Check if the user owns the position
        try:
            owner_of = position_manager.functions.ownerOf(position_id).call()
            if owner_of.lower() != wallet_address.lower():
                return {
                    "success": False,
                    "message": f"Position {position_id} is not owned by {wallet_address}"
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error checking position ownership: {str(e)}"
            }
        
        # Get position information
        try:
            position = position_manager.functions.positions(position_id).call()
            token0 = position[2]
            token1 = position[3]
            fee = position[4]
            liquidity = position[7]
            
            # Get token contracts
            token0_contract = web3.eth.contract(address=token0, abi=uniswap.ERC20_ABI)
            token1_contract = web3.eth.contract(address=token1, abi=uniswap.ERC20_ABI)
            
            # Get token symbols
            token0_symbol = token0_contract.functions.symbol().call()
            token1_symbol = token1_contract.functions.symbol().call()
            
            print(f"Position {position_id} has {liquidity} liquidity for {token0_symbol}/{token1_symbol} pair")
        except Exception as e:
            return {
                "success": False,
                "message": f"Error getting position information: {str(e)}"
            }
        
        # Calculate liquidity to remove
        liquidity_to_remove = int(liquidity * percent_to_remove / 100)
        
        if liquidity_to_remove <= 0:
            return {
                "success": False,
                "message": "No liquidity to remove"
            }
        
        # Set deadline (10 minutes from now)
        deadline = int(time.time() + 600)
        
        # Create the decrease liquidity parameters
        decrease_params = {
            'tokenId': position_id,
            'liquidity': liquidity_to_remove,
            'amount0Min': 0,  # No minimum (accepting slippage)
            'amount1Min': 0,  # No minimum (accepting slippage)
            'deadline': deadline
        }
        
        # Get current gas price
        gas_price = web3.eth.gas_price
        
        # Build the decrease liquidity transaction
        decrease_tx = position_manager.functions.decreaseLiquidity(decrease_params).build_transaction({
            'from': wallet_address,
            'gas': 500000,  # Higher gas limit for safety
            'gasPrice': gas_price,
            'nonce': web3.eth.get_transaction_count(wallet_address),
        })
        
        # Sign and send the transaction
        signed_decrease_tx = web3.eth.account.sign_transaction(decrease_tx, private_key=private_key)
        decrease_tx_hash = web3.eth.send_raw_transaction(signed_decrease_tx.rawTransaction)
        print(f"Decrease liquidity transaction sent with hash: {decrease_tx_hash.hex()}")
        
        # Wait for transaction receipt
        decrease_receipt = web3.eth.wait_for_transaction_receipt(decrease_tx_hash)
        
        if decrease_receipt.status != 1:
            return {
                "success": False,
                "message": "Decrease liquidity transaction failed",
                "transaction_hash": decrease_tx_hash.hex()
            }
        
        # Create the collect parameters to collect the tokens
        collect_params = {
            'tokenId': position_id,
            'recipient': wallet_address,
            'amount0Max': 2**128 - 1,  # Max uint128
            'amount1Max': 2**128 - 1   # Max uint128
        }
        
        # Build the collect transaction
        collect_tx = position_manager.functions.collect(collect_params).build_transaction({
            'from': wallet_address,
            'gas': 300000,
            'gasPrice': gas_price,
            'nonce': web3.eth.get_transaction_count(wallet_address),
        })
        
        # Sign and send the transaction
        signed_collect_tx = web3.eth.account.sign_transaction(collect_tx, private_key=private_key)
        collect_tx_hash = web3.eth.send_raw_transaction(signed_collect_tx.rawTransaction)
        print(f"Collect transaction sent with hash: {collect_tx_hash.hex()}")
        
        # Wait for transaction receipt
        collect_receipt = web3.eth.wait_for_transaction_receipt(collect_tx_hash)
        
        if collect_receipt.status != 1:
            return {
                "success": False,
                "message": "Collect transaction failed",
                "transaction_hash": collect_tx_hash.hex()
            }
        
        # Try to parse the logs to get the collected amounts
        amount0_collected = None
        amount1_collected = None
        
        try:
            # Get the Collect event logs
            logs = position_manager.events.Collect().process_receipt(collect_receipt)
            if logs:
                amount0_collected = logs[0]['args']['amount0']
                amount1_collected = logs[0]['args']['amount1']
        except Exception as log_error:
            print(f"Error parsing logs: {log_error}")
        
        return {
            "success": True,
            "transaction_hash": collect_tx_hash.hex(),
            "decrease_transaction_hash": decrease_tx_hash.hex(),
            "position_id": position_id,
            "liquidity_removed": str(liquidity_to_remove),
            "percent_removed": percent_to_remove,
            "amount0_collected": str(amount0_collected) if amount0_collected else None,
            "amount1_collected": str(amount1_collected) if amount1_collected else None,
            "token0": token0,
            "token1": token1,
            "token0_symbol": token0_symbol,
            "token1_symbol": token1_symbol
        }
        
    except Exception as error:
        return {
            "success": False,
            "message": f"Error: {str(error)}"
        } 