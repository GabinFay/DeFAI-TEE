#!/usr/bin/env python3
"""
Script to make a swap on Flare network using Uniswap V3 protocol via the uniswap-python SDK
"""

import os
import time
from dotenv import load_dotenv
from web3 import Web3
# Fix: Use the correct middleware for newer Web3.py versions
from web3.middleware import geth_poa_middleware
from uniswap import Uniswap
from eth_account import Account

def swap_tokens(token_in, token_out, amount_in_eth, fee=3000):
    """
    Swap tokens on Flare network using Uniswap V3 via the uniswap-python SDK
    
    Args:
        token_in (str): Address of the input token
        token_out (str): Address of the output token
        amount_in_eth (float): Amount of input token in ETH units (e.g., 0.01 for 0.01 WFLR)
        fee (int): Fee tier (3000 = 0.3%)
        
    Returns:
        dict: Transaction receipt if successful, None otherwise
    """
    # Load environment variables
    load_dotenv()
    
    # Get environment variables
    FLARE_RPC_URL = os.getenv("FLARE_RPC_URL")
    PRIVATE_KEY = os.getenv("PRIVATE_KEY")
    
    # Derive wallet address from private key to ensure they match
    account = Account.from_key(PRIVATE_KEY)
    wallet_address = account.address
    print(f"Using wallet address: {wallet_address}")
    
    # Initialize Web3
    web3 = Web3(Web3.HTTPProvider(FLARE_RPC_URL))
    # Fix: Use geth_poa_middleware instead of ExtraDataToPOAMiddleware
    web3.middleware_onion.inject(geth_poa_middleware, layer=0)
    
    print(f"Connected to Flare network: {web3.is_connected()}")
    print(f"Chain ID: {web3.eth.chain_id}")
    
    # Convert addresses to checksum format
    token_in_address = Web3.to_checksum_address(token_in)
    token_out_address = Web3.to_checksum_address(token_out)
    wallet_address = Web3.to_checksum_address(wallet_address)
    
    # Initialize Uniswap SDK with version 3 for V3 swaps
    # The SDK will use the Flare network contracts we added in constants.py
    uniswap = Uniswap(
        address=wallet_address,
        private_key=PRIVATE_KEY,
        web3=web3,
        version=3,
        default_slippage=0.01  # 1% slippage
    )
    
    # Print the router address being used to verify it's correct
    print(f"Using Uniswap V3 Router address: {uniswap.router.address}")
    
    # Convert amount to wei
    amount_in_wei = web3.to_wei(amount_in_eth, 'ether')
    print(f"Swapping {amount_in_eth} tokens for output token")
    
    try:
        # Create token contract instances to get token information
        token_in_contract = uniswap.get_token(token_in_address)
        token_out_contract = uniswap.get_token(token_out_address)
        
        # Get token information
        token_in_symbol = token_in_contract.symbol
        token_out_symbol = token_out_contract.symbol
        token_in_decimals = token_in_contract.decimals
        token_out_decimals = token_out_contract.decimals
        
        print(f"Swapping {amount_in_eth} {token_in_symbol} for {token_out_symbol}")
        print(f"{token_in_symbol} decimals: {token_in_decimals}")
        print(f"{token_out_symbol} decimals: {token_out_decimals}")
        
        # Check token balances
        token_in_balance = uniswap.get_token_balance(token_in_address)
        token_out_balance_before = uniswap.get_token_balance(token_out_address)
        
        print(f"{token_in_symbol} Balance: {token_in_balance / (10**token_in_decimals)} {token_in_symbol}")
        print(f"{token_out_symbol} Balance before swap: {token_out_balance_before / (10**token_out_decimals)} {token_out_symbol}")
        
        if token_in_balance < amount_in_wei:
            print(f"Insufficient balance. You have {token_in_balance / (10**token_in_decimals)} {token_in_symbol} but trying to swap {amount_in_eth} {token_in_symbol}")
            return None
        
        # Check and handle token approval
        # Create ERC20 contract instance for token_in
        erc20_abi = '''[{"constant":true,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_from","type":"address"},{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transferFrom","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"}]'''
        token_contract = web3.eth.contract(address=token_in_address, abi=erc20_abi)
        
        # Check allowance
        allowance = token_contract.functions.allowance(wallet_address, uniswap.router.address).call()
        print(f"Current allowance: {allowance / (10**token_in_decimals)} {token_in_symbol}")
        
        if allowance < amount_in_wei:
            print(f"Approving {token_in_symbol} for spending...")
            
            # Approve tokens for the router
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
            print("Sending approval transaction...")
            approve_tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            print(f"Approval transaction sent with hash: {approve_tx_hash.hex()}")
            
            # Wait for transaction receipt
            print("Waiting for approval confirmation...")
            approve_receipt = web3.eth.wait_for_transaction_receipt(approve_tx_hash)
            
            if approve_receipt.status == 1:
                print("Approval successful!")
            else:
                print("Approval failed!")
                return None
        
        # Set a deadline for the transaction (10 minutes from now)
        deadline = int(time.time() + 600)
        
        # Try to estimate the output amount
        try:
            # Use the quoter contract to get the expected output amount
            sqrtPriceLimitX96 = 0
            
            # Print the quoter address being used
            print(f"Using Quoter address: {uniswap.quoter.address}")
            
            # Handle the tuple return value correctly
            quoter_result = uniswap.quoter.functions.quoteExactInputSingle(
                token_in_address, 
                token_out_address, 
                fee, 
                amount_in_wei, 
                sqrtPriceLimitX96
            ).call()
            
            # The quoter might return a tuple or a single value depending on the contract version
            if isinstance(quoter_result, tuple):
                expected_output = quoter_result[0]  # Extract the first element if it's a tuple
            else:
                expected_output = quoter_result
                
            # Calculate minimum output with 1% slippage
            min_output = int(expected_output * 0.99)
            
            print(f"Expected output: {expected_output / (10**token_out_decimals)} {token_out_symbol}")
            print(f"Minimum output with slippage: {min_output / (10**token_out_decimals)} {token_out_symbol}")
            
        except Exception as quote_error:
            print(f"Error estimating output: {quote_error}")
            # Set a very low minimum output if estimation fails
            min_output = 1
            print(f"Using minimum output of {min_output} wei")
        
        # Execute the swap directly using the router contract
        print("Executing swap...")
        
        # Build the swap transaction
        swap_tx = uniswap.router.functions.exactInputSingle({
            "tokenIn": token_in_address,
            "tokenOut": token_out_address,
            "fee": fee,
            "recipient": wallet_address,
            "deadline": deadline,
            "amountIn": amount_in_wei,
            "amountOutMinimum": min_output,
            "sqrtPriceLimitX96": 0
        }).build_transaction({
            'from': wallet_address,
            'gas': 350000,  # Higher gas limit for safety
            'gasPrice': web3.eth.gas_price,
            'nonce': web3.eth.get_transaction_count(wallet_address),
        })
        
        # Sign and send the transaction
        signed_swap_tx = web3.eth.account.sign_transaction(swap_tx, private_key=PRIVATE_KEY)
        tx_hash = web3.eth.send_raw_transaction(signed_swap_tx.rawTransaction)
        print(f"Swap transaction sent with hash: {tx_hash.hex()}")
        
        # Wait for transaction receipt
        print("Waiting for swap confirmation...")
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        
        if tx_receipt.status == 1:
            print("Swap successful!")
            
            # Check token balance after swap
            token_out_balance_after = uniswap.get_token_balance(token_out_address)
            token_out_received = token_out_balance_after - token_out_balance_before
            
            print(f"{token_out_symbol} Balance after swap: {token_out_balance_after / (10**token_out_decimals)} {token_out_symbol}")
            print(f"{token_out_symbol} received: {token_out_received / (10**token_out_decimals)} {token_out_symbol}")
            
            return tx_receipt
        else:
            print("Swap failed!")
            return None
            
    except Exception as error:
        print(f"Error: {error}")
        return None

if __name__ == "__main__":
    # WFLR and USDC addresses on Flare
    WFLR_ADDRESS = "0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d"
    USDC_ADDRESS = "0xFbDa5F676cB37624f28265A144A48B0d6e87d3b6"
    
    # Swap 0.01 WFLR for USDC
    swap_tokens(WFLR_ADDRESS, USDC_ADDRESS, 0.01) 