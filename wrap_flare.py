#!/usr/bin/env python3
"""
Module for wrapping native FLR to WFLR on Flare network
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

def wrap_flare(amount_flr, private_key=None, rpc_url=None):
    """
    Wrap native FLR to WFLR (Wrapped Flare) on Flare network
    
    Args:
        amount_flr (float): Amount of FLR to wrap
        private_key (str): Private key for the wallet
        rpc_url (str): RPC URL for the Flare network
        
    Returns:
        dict: Transaction receipt
    """
    print(f"Wrapping {amount_flr} FLR to WFLR...")
    
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
    
    # Check FLR balance
    flr_balance = web3.eth.get_balance(wallet_address)
    flr_balance_eth = web3.from_wei(flr_balance, 'ether')
    print(f"Current FLR balance: {flr_balance_eth} FLR")
    
    # Convert amount to wei
    amount_wei = web3.to_wei(amount_flr, 'ether')
    
    # Ensure we have enough balance
    if amount_wei > flr_balance:
        raise ValueError(f"Insufficient FLR balance. Have {flr_balance_eth} FLR, need {amount_flr} FLR")
    
    # Initialize WFLR contract
    wflr_contract = web3.eth.contract(address=Web3.to_checksum_address(WFLR_ADDRESS), abi=WFLR_ABI)
    
    # Check WFLR balance before wrapping
    wflr_balance_before = wflr_contract.functions.balanceOf(wallet_address).call()
    wflr_decimals = wflr_contract.functions.decimals().call()
    wflr_balance_before_eth = wflr_balance_before / (10 ** wflr_decimals)
    print(f"WFLR balance before wrapping: {wflr_balance_before_eth} WFLR")
    
    # Build transaction to wrap FLR
    print(f"Building transaction to wrap {amount_flr} FLR...")
    
    # Get current gas price
    gas_price = web3.eth.gas_price
    print(f"Current gas price: {web3.from_wei(gas_price, 'gwei')} gwei")
    
    # Build the transaction
    tx = {
        'from': wallet_address,
        'to': WFLR_ADDRESS,
        'value': amount_wei,
        'gas': 100000,  # Estimate gas limit
        'gasPrice': gas_price,
        'nonce': web3.eth.get_transaction_count(wallet_address),
        'chainId': web3.eth.chain_id,
        'data': wflr_contract.encodeABI(fn_name='deposit')
    }
    
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
        
        # Check WFLR balance after wrapping
        wflr_balance_after = wflr_contract.functions.balanceOf(wallet_address).call()
        wflr_balance_after_eth = wflr_balance_after / (10 ** wflr_decimals)
        print(f"WFLR balance after wrapping: {wflr_balance_after_eth} WFLR")
        print(f"Wrapped {amount_flr} FLR to WFLR successfully!")
        
        return tx_receipt
    else:
        print("Transaction failed!")
        return None

if __name__ == "__main__":
    # This allows the script to be run directly for testing
    import argparse
    
    parser = argparse.ArgumentParser(description='Wrap native FLR to WFLR on Flare network')
    parser.add_argument('--amount', type=float, required=True, help='Amount of FLR to wrap')
    parser.add_argument('--rpc', type=str, help='RPC URL for the Flare network')
    
    args = parser.parse_args()
    
    receipt = wrap_flare(args.amount, rpc_url=args.rpc)
    
    if receipt:
        print(f"Wrap successful! Transaction hash: {receipt.transactionHash.hex()}")
    else:
        print("Wrap failed!") 