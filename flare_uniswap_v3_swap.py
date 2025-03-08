#!/usr/bin/env python3
"""
Script to make a swap on Flare network using Uniswap V3 protocol
"""

# Load wallet details from .env file
from dotenv import load_dotenv
import os
import json
import time
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from web3.exceptions import ContractLogicError

def swap_tokens(token_in, token_out, amount_in_eth, fee=3000):
    """
    Swap tokens on Flare network using Uniswap V3
    
    Args:
        token_in (str): Address of the input token
        token_out (str): Address of the output token
        amount_in_eth (float): Amount of input token in ETH units (e.g., 0.01 for 0.01 WFLR)
        fee (int): Fee tier (3000 = 0.3%)
        
    Returns:
        dict: Transaction receipt if successful, None otherwise
    """
    load_dotenv()

    # Flare RPC URL
    FLARE_RPC_URL = os.getenv("FLARE_RPC_URL")
    WALLET_ADDRESS = os.getenv("WALLET_ADDRESS")
    PRIVATE_KEY = os.getenv("PRIVATE_KEY")

    # Uniswap V3 Router address on Flare
    ROUTER_ADDRESS = "0x8a1E35F5c98C4E85B36B7B253222eE17773b2781"

    # Initialize Web3
    web3 = Web3(Web3.HTTPProvider(FLARE_RPC_URL))
    web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

    print(f"Connected to Flare network: {web3.is_connected()}")
    print(f"Chain ID: {web3.eth.chain_id}")

    # Convert addresses to checksum format
    token_in_address = Web3.to_checksum_address(token_in)
    token_out_address = Web3.to_checksum_address(token_out)
    router_address = Web3.to_checksum_address(ROUTER_ADDRESS)

    # Convert amount to wei
    amount_in_wei = web3.to_wei(amount_in_eth, 'ether')
    print(f"Swapping {amount_in_eth} tokens for output token")

    # ERC20 ABI for token operations
    erc20_abi = '''
    [
        {
            "constant": true,
            "inputs": [],
            "name": "name",
            "outputs": [{"name": "", "type": "string"}],
            "payable": false,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": false,
            "inputs": [{"name": "_spender", "type": "address"}, {"name": "_value", "type": "uint256"}],
            "name": "approve",
            "outputs": [{"name": "", "type": "bool"}],
            "payable": false,
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "constant": true,
            "inputs": [],
            "name": "totalSupply",
            "outputs": [{"name": "", "type": "uint256"}],
            "payable": false,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": false,
            "inputs": [{"name": "_from", "type": "address"}, {"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}],
            "name": "transferFrom",
            "outputs": [{"name": "", "type": "bool"}],
            "payable": false,
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "constant": true,
            "inputs": [],
            "name": "decimals",
            "outputs": [{"name": "", "type": "uint8"}],
            "payable": false,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": true,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "payable": false,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": true,
            "inputs": [],
            "name": "symbol",
            "outputs": [{"name": "", "type": "string"}],
            "payable": false,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": false,
            "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}],
            "name": "transfer",
            "outputs": [{"name": "", "type": "bool"}],
            "payable": false,
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "constant": true,
            "inputs": [{"name": "_owner", "type": "address"}, {"name": "_spender", "type": "address"}],
            "name": "allowance",
            "outputs": [{"name": "", "type": "uint256"}],
            "payable": false,
            "stateMutability": "view",
            "type": "function"
        }
    ]
    '''

    # Uniswap V3 Router ABI
    router_abi = '''
    [
        {
            "inputs": [
                {
                    "components": [
                        {"internalType": "address", "name": "tokenIn", "type": "address"},
                        {"internalType": "address", "name": "tokenOut", "type": "address"},
                        {"internalType": "uint24", "name": "fee", "type": "uint24"},
                        {"internalType": "address", "name": "recipient", "type": "address"},
                        {"internalType": "uint256", "name": "deadline", "type": "uint256"},
                        {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                        {"internalType": "uint256", "name": "amountOutMinimum", "type": "uint256"},
                        {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"}
                    ],
                    "internalType": "struct ISwapRouter.ExactInputSingleParams",
                    "name": "params",
                    "type": "tuple"
                }
            ],
            "name": "exactInputSingle",
            "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}],
            "stateMutability": "payable",
            "type": "function"
        }
    ]
    '''

    try:
        # Create token contract instances
        token_in_contract = web3.eth.contract(address=token_in_address, abi=erc20_abi)
        token_out_contract = web3.eth.contract(address=token_out_address, abi=erc20_abi)
        
        # Create router contract instance
        router_contract = web3.eth.contract(address=router_address, abi=router_abi)
        
        # Get token information
        token_in_symbol = token_in_contract.functions.symbol().call()
        token_out_symbol = token_out_contract.functions.symbol().call()
        token_in_decimals = token_in_contract.functions.decimals().call()
        token_out_decimals = token_out_contract.functions.decimals().call()
        
        print(f"Swapping {amount_in_eth} {token_in_symbol} for {token_out_symbol}")
        print(f"{token_in_symbol} decimals: {token_in_decimals}")
        print(f"{token_out_symbol} decimals: {token_out_decimals}")
        
        # Check token balances
        token_in_balance = token_in_contract.functions.balanceOf(WALLET_ADDRESS).call()
        token_out_balance_before = token_out_contract.functions.balanceOf(WALLET_ADDRESS).call()
        
        print(f"{token_in_symbol} Balance: {token_in_balance / (10**token_in_decimals)} {token_in_symbol}")
        print(f"{token_out_symbol} Balance before swap: {token_out_balance_before / (10**token_out_decimals)} {token_out_symbol}")
        
        if token_in_balance < amount_in_wei:
            print(f"Insufficient balance. You have {token_in_balance / (10**token_in_decimals)} {token_in_symbol} but trying to swap {amount_in_eth} {token_in_symbol}")
            return None
            
        # Check allowance
        allowance = token_in_contract.functions.allowance(WALLET_ADDRESS, router_address).call()
        print(f"Current allowance: {allowance / (10**token_in_decimals)} {token_in_symbol}")
        
        if allowance < amount_in_wei:
            print(f"Approving {token_in_symbol} for spending...")
            
            # Get current gas price
            gas_price = web3.eth.gas_price
            print(f"Current gas price: {web3.from_wei(gas_price, 'gwei')} gwei")
            
            # Use a slightly higher gas price to ensure transaction goes through
            suggested_gas_price = int(gas_price * 1.1)
            print(f"Suggested gas price: {web3.from_wei(suggested_gas_price, 'gwei')} gwei")
            
            # Approve tokens for the router
            approve_tx = token_in_contract.functions.approve(
                router_address,
                2**256 - 1  # Max approval
            ).build_transaction({
                'from': WALLET_ADDRESS,
                'gas': 200000,
                'gasPrice': suggested_gas_price,
                'nonce': web3.eth.get_transaction_count(WALLET_ADDRESS),
            })
            
            # Sign transaction
            signed_txn = web3.eth.account.sign_transaction(approve_tx, private_key=PRIVATE_KEY)
            
            # Send transaction
            print("Sending approval transaction...")
            txn_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
            print(f"Transaction sent with hash: {txn_hash.hex()}")
            
            # Wait for transaction receipt
            print("Waiting for transaction confirmation...")
            txn_receipt = web3.eth.wait_for_transaction_receipt(txn_hash)
            
            if txn_receipt.status == 1:
                print("Approval successful!")
            else:
                print("Approval failed!")
                return None
        
        # Execute the swap using exactInputSingle
        print("Executing swap...")
        
        # Set deadline to 10 minutes from now
        deadline = int(time.time() + 600)
        
        # Get current gas price for the swap
        gas_price = web3.eth.gas_price
        print(f"Current gas price: {web3.from_wei(gas_price, 'gwei')} gwei")
        
        # Use a slightly higher gas price to ensure transaction goes through
        suggested_gas_price = int(gas_price * 1.1)
        print(f"Suggested gas price: {web3.from_wei(suggested_gas_price, 'gwei')} gwei")
        
        # Set a small amount out minimum to ensure the transaction doesn't fail
        amount_out_min = 1  # Just a very small amount to ensure it's not 0
        
        # Try to estimate gas for the transaction
        try:
            estimated_gas = router_contract.functions.exactInputSingle(
                [
                    token_in_address,  # tokenIn
                    token_out_address,  # tokenOut
                    fee,               # fee
                    WALLET_ADDRESS,    # recipient
                    deadline,          # deadline
                    amount_in_wei,     # amountIn
                    amount_out_min,    # amountOutMinimum
                    0                  # sqrtPriceLimitX96 (0 = no limit)
                ]
            ).estimate_gas({
                'from': WALLET_ADDRESS,
                'value': 0
            })
            print(f"Estimated gas: {estimated_gas}")
            
            # Add 20% buffer to estimated gas
            gas_limit = int(estimated_gas * 1.2)
        except ContractLogicError as gas_error:
            print(f"Gas estimation failed: {gas_error}")
            print("Using default gas limit of 500,000")
            gas_limit = 500000
        
        # Build swap transaction
        swap_tx = router_contract.functions.exactInputSingle(
            [
                token_in_address,  # tokenIn
                token_out_address,  # tokenOut
                fee,               # fee
                WALLET_ADDRESS,    # recipient
                deadline,          # deadline
                amount_in_wei,     # amountIn
                amount_out_min,    # amountOutMinimum
                0                  # sqrtPriceLimitX96 (0 = no limit)
            ]
        ).build_transaction({
            'from': WALLET_ADDRESS,
            'gas': gas_limit,
            'gasPrice': suggested_gas_price,
            'nonce': web3.eth.get_transaction_count(WALLET_ADDRESS),
            'value': 0
        })
        
        # Sign transaction
        signed_swap_txn = web3.eth.account.sign_transaction(swap_tx, private_key=PRIVATE_KEY)
        
        # Send transaction
        print("Sending swap transaction...")
        swap_txn_hash = web3.eth.send_raw_transaction(signed_swap_txn.raw_transaction)
        print(f"Swap transaction sent with hash: {swap_txn_hash.hex()}")
        
        # Wait for transaction receipt
        print("Waiting for swap confirmation...")
        swap_txn_receipt = web3.eth.wait_for_transaction_receipt(swap_txn_hash)
        
        if swap_txn_receipt.status == 1:
            print("Swap successful!")
            
            # Check token balance after swap
            token_out_balance_after = token_out_contract.functions.balanceOf(WALLET_ADDRESS).call()
            token_out_received = token_out_balance_after - token_out_balance_before
            
            print(f"{token_out_symbol} Balance after swap: {token_out_balance_after / (10**token_out_decimals)} {token_out_symbol}")
            print(f"{token_out_symbol} received: {token_out_received / (10**token_out_decimals)} {token_out_symbol}")
            
            return swap_txn_receipt
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