#!/usr/bin/env python3
"""
Module for unwrapping WFLR to native FLR on Flare network
"""

import os
import sys
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account

# WFLR contract address on Flare network
WFLR_ADDRESS = "0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d"

# WFLR ABI (only the necessary parts)
WFLR_ABI = [
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
    {
        "constant": False,
        "inputs": [],
        "name": "deposit",
        "outputs": [],
        "payable": True,
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [{"name": "wad", "type": "uint256"}],
        "name": "withdraw",
        "outputs": [],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

def unwrap_flare(amount_wflr, private_key=None, rpc_url=None):
    """
    Unwrap WFLR to native FLR on Flare network
    
    Args:
        amount_wflr (float): Amount of WFLR to unwrap
        private_key (str): Private key for the wallet
        rpc_url (str): RPC URL for the Flare network
        
    Returns:
        dict: Transaction receipt
    """
    print(f"Unwrapping {amount_wflr} WFLR to FLR...")
    
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
    
    # Initialize WFLR contract
    wflr_contract = web3.eth.contract(address=Web3.to_checksum_address(WFLR_ADDRESS), abi=WFLR_ABI)
    
    # Check WFLR balance
    wflr_balance = wflr_contract.functions.balanceOf(wallet_address).call()
    wflr_decimals = wflr_contract.functions.decimals().call()
    wflr_balance_eth = wflr_balance / (10 ** wflr_decimals)
    print(f"Current WFLR balance: {wflr_balance_eth} WFLR")
    
    # Convert amount to wei
    amount_wei = int(amount_wflr * (10 ** wflr_decimals))
    
    # Ensure we have enough balance
    if amount_wei > wflr_balance:
        raise ValueError(f"Insufficient WFLR balance. Have {wflr_balance_eth} WFLR, need {amount_wflr} WFLR")
    
    # Check FLR balance before unwrapping
    flr_balance_before = web3.eth.get_balance(wallet_address)
    flr_balance_before_eth = web3.from_wei(flr_balance_before, 'ether')
    print(f"FLR balance before unwrapping: {flr_balance_before_eth} FLR")
    
    # Build transaction to unwrap WFLR
    print(f"Building transaction to unwrap {amount_wflr} WFLR...")
    
    # Get current gas price
    gas_price = web3.eth.gas_price
    print(f"Current gas price: {web3.from_wei(gas_price, 'gwei')} gwei")
    
    # Build the transaction
    tx = wflr_contract.functions.withdraw(amount_wei).build_transaction({
        'from': wallet_address,
        'gas': 100000,  # Estimate gas limit
        'gasPrice': gas_price,
        'nonce': web3.eth.get_transaction_count(wallet_address),
        'chainId': web3.eth.chain_id
    })
    
    # Sign the transaction
    print("Signing transaction...")
    signed_tx = web3.eth.account.sign_transaction(tx, private_key)
    
    # Send the transaction
    print("Sending transaction...")
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    print(f"Transaction sent with hash: {tx_hash.hex()}")
    
    # Wait for transaction receipt
    print("Waiting for transaction confirmation...")
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    
    # Check if transaction was successful
    if tx_receipt.status == 1:
        print(f"Transaction successful! Gas used: {tx_receipt.gasUsed}")
        
        # Check FLR balance after unwrapping
        flr_balance_after = web3.eth.get_balance(wallet_address)
        flr_balance_after_eth = web3.from_wei(flr_balance_after, 'ether')
        print(f"FLR balance after unwrapping: {flr_balance_after_eth} FLR")
        print(f"Unwrapped {amount_wflr} WFLR to FLR successfully!")
        
        return tx_receipt
    else:
        print("Transaction failed!")
        return None

if __name__ == "__main__":
    # This allows the script to be run directly for testing
    import argparse
    
    parser = argparse.ArgumentParser(description='Unwrap WFLR to native FLR on Flare network')
    parser.add_argument('--amount', type=float, required=True, help='Amount of WFLR to unwrap')
    parser.add_argument('--rpc', type=str, help='RPC URL for the Flare network')
    
    args = parser.parse_args()
    
    receipt = unwrap_flare(args.amount, rpc_url=args.rpc)
    
    if receipt:
        print(f"Unwrap successful! Transaction hash: {receipt.transactionHash.hex()}")
    else:
        print("Unwrap failed!") 