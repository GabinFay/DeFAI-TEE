#!/usr/bin/env python3
"""
Script to add liquidity to a Uniswap V3 pool on Flare network
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

# Fee tiers
FEE_TIER_LOW = 500      # 0.05%
FEE_TIER_MEDIUM = 3000  # 0.3%
FEE_TIER_HIGH = 10000   # 1%

def add_liquidity(token0, token1, amount0, amount1, fee=3000):
    """
    Add liquidity to a Uniswap V3 pool on Flare network
    
    Args:
        token0 (str): Address of token0 (must be lower address than token1)
        token1 (str): Address of token1 (must be higher address than token0)
        amount0 (float): Amount of token0 in token units
        amount1 (float): Amount of token1 in token units
        fee (int): Fee tier (3000 = 0.3%)
        
    Returns:
        dict: Transaction receipt if successful, None otherwise
    """
    # Derive wallet address from private key
    account = Account.from_key(PRIVATE_KEY)
    wallet_address = account.address
    print(f"Using wallet address: {wallet_address}")
    
    # Initialize Web3
    web3 = Web3(Web3.HTTPProvider(FLARE_RPC_URL))
    web3.middleware_onion.inject(geth_poa_middleware, layer=0)
    
    print(f"Connected to Flare network: {web3.is_connected()}")
    print(f"Chain ID: {web3.eth.chain_id}")
    
    # Convert addresses to checksum format
    token0_address = Web3.to_checksum_address(token0)
    token1_address = Web3.to_checksum_address(token1)
    wallet_address = Web3.to_checksum_address(wallet_address)
    
    # Verify token0 address is less than token1 address (required by Uniswap V3)
    if int(token0_address, 16) > int(token1_address, 16):
        print("Error: token0 address must be less than token1 address")
        print(f"token0: {token0_address}")
        print(f"token1: {token1_address}")
        return None
    
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
    
    try:
        # Get pool instance
        pool = uniswap.get_pool_instance(token0_address, token1_address, fee)
        print(f"Pool address: {pool.address}")
        
        # Get pool immutables and state
        pool_immutables = uniswap.get_pool_immutables(pool)
        pool_state = uniswap.get_pool_state(pool)
        
        print(f"Pool immutables: {json.dumps(pool_immutables, indent=2)}")
        print(f"Pool state: {json.dumps(pool_state, indent=2)}")
        
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
            print(f"Insufficient {token0_symbol} balance. You have {token0_balance / (10**token0_decimals)} but trying to add {amount0}")
            return None
        
        if token1_balance < amount1_wei:
            print(f"Insufficient {token1_symbol} balance. You have {token1_balance / (10**token1_decimals)} but trying to add {amount1}")
            return None
        
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
        
        print(f"{token0_symbol} allowance for Position Manager: {token0_allowance / (10**token0_decimals)}")
        print(f"{token1_symbol} allowance for Position Manager: {token1_allowance / (10**token1_decimals)}")
        
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
            signed_txn = web3.eth.account.sign_transaction(approve_tx, private_key=PRIVATE_KEY)
            
            # Send transaction
            approve_tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            print(f"Approval transaction sent with hash: {approve_tx_hash.hex()}")
            
            # Wait for transaction receipt
            approve_receipt = web3.eth.wait_for_transaction_receipt(approve_tx_hash)
            
            if approve_receipt.status != 1:
                print(f"Approval for {token0_symbol} failed!")
                return None
            
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
            signed_txn = web3.eth.account.sign_transaction(approve_tx, private_key=PRIVATE_KEY)
            
            # Send transaction
            approve_tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            print(f"Approval transaction sent with hash: {approve_tx_hash.hex()}")
            
            # Wait for transaction receipt
            approve_receipt = web3.eth.wait_for_transaction_receipt(approve_tx_hash)
            
            if approve_receipt.status != 1:
                print(f"Approval for {token1_symbol} failed!")
                return None
            
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
        
        print(f"Mint parameters: {json.dumps(mint_params, indent=2, default=str)}")
        
        # Get the position manager contract
        position_manager = uniswap.nonFungiblePositionManager
        
        # Get current gas price and estimate gas
        gas_price = web3.eth.gas_price
        print(f"Current gas price: {web3.from_wei(gas_price, 'gwei')} gwei")
        
        try:
            # Estimate gas for the mint transaction
            gas_estimate = position_manager.functions.mint(mint_params).estimate_gas({
                'from': wallet_address,
            })
            print(f"Estimated gas: {gas_estimate}")
            
            # Add 20% buffer to gas estimate
            gas_limit = int(gas_estimate * 1.2)
        except Exception as gas_error:
            print(f"Error estimating gas: {gas_error}")
            # Use a higher gas limit as fallback
            gas_limit = 1000000
            print(f"Using fallback gas limit: {gas_limit}")
        
        # Build the mint transaction
        mint_tx = position_manager.functions.mint(mint_params).build_transaction({
            'from': wallet_address,
            'gas': gas_limit,
            'gasPrice': gas_price,
            'nonce': web3.eth.get_transaction_count(wallet_address),
        })
        
        # Sign and send the transaction
        signed_mint_tx = web3.eth.account.sign_transaction(mint_tx, private_key=PRIVATE_KEY)
        tx_hash = web3.eth.send_raw_transaction(signed_mint_tx.rawTransaction)
        print(f"Mint transaction sent with hash: {tx_hash.hex()}")
        
        # Wait for transaction receipt
        print("Waiting for transaction confirmation...")
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        
        if tx_receipt.status == 1:
            print("Liquidity provision successful!")
            
            # Try to parse the logs to get the token ID
            try:
                # Get the IncreaseLiquidity event logs
                logs = position_manager.events.IncreaseLiquidity().process_receipt(tx_receipt)
                if logs:
                    print(f"Position created with token ID: {logs[0]['args']['tokenId']}")
                    print(f"Liquidity added: {logs[0]['args']['liquidity']}")
                    print(f"Amount0 used: {logs[0]['args']['amount0']} {token0_symbol}")
                    print(f"Amount1 used: {logs[0]['args']['amount1']} {token1_symbol}")
            except Exception as log_error:
                print(f"Error parsing logs: {log_error}")
            
            return tx_receipt
        else:
            print("Liquidity provision failed!")
            
            # Try to get more information about the failure
            try:
                # Get the transaction details
                tx = web3.eth.get_transaction(tx_hash)
                # Try to replay the transaction to get the revert reason
                result = web3.eth.call({
                    'to': tx['to'],
                    'from': tx['from'],
                    'data': tx['input'],
                    'gas': tx['gas'],
                    'gasPrice': tx['gasPrice'],
                    'value': tx['value'],
                }, tx_receipt.blockNumber)
                print(f"Transaction replay result: {result}")
            except Exception as replay_error:
                print(f"Error replaying transaction: {replay_error}")
            
            return None
            
    except Exception as error:
        print(f"Error: {error}")
        return None

if __name__ == "__main__":
    # WFLR and USDC addresses on Flare
    WFLR_ADDRESS = "0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d"
    USDC_ADDRESS = "0xFbDa5F676cB37624f28265A144A48B0d6e87d3b6"
    
    # Ensure token0 address is less than token1 address (required by Uniswap V3)
    if int(WFLR_ADDRESS, 16) < int(USDC_ADDRESS, 16):
        token0 = WFLR_ADDRESS
        token1 = USDC_ADDRESS
        # Set amounts (0.1 WFLR and 0.1 USDC)
        amount0 = 0.1
        amount1 = 0.1
    else:
        token0 = USDC_ADDRESS
        token1 = WFLR_ADDRESS
        # Set amounts (0.1 USDC and 0.1 WFLR)
        amount0 = 0.1
        amount1 = 0.1
    
    print(f"Adding liquidity: {amount0} of {token0} and {amount1} of {token1}")
    add_liquidity(token0, token1, amount0, amount1, FEE_TIER_MEDIUM) 