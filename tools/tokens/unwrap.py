#!/usr/bin/env python3
"""
Module for unwrapping WFLR to native FLR on Flare network
"""

import os
import sys
import json
import traceback
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# WFLR contract address on Flare network
WFLR_ADDRESS = "0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d"

# WFLR ABI (complete ABI for WETH9-like contract)
WFLR_ABI = '''
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
        "inputs": [{"name": "guy", "type": "address"}, {"name": "wad", "type": "uint256"}],
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
        "inputs": [{"name": "src", "type": "address"}, {"name": "dst", "type": "address"}, {"name": "wad", "type": "uint256"}],
        "name": "transferFrom",
        "outputs": [{"name": "", "type": "bool"}],
        "payable": false,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": false,
        "inputs": [{"name": "wad", "type": "uint256"}],
        "name": "withdraw",
        "outputs": [],
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
        "inputs": [{"name": "", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
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
        "inputs": [{"name": "dst", "type": "address"}, {"name": "wad", "type": "uint256"}],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "payable": false,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": false,
        "inputs": [],
        "name": "deposit",
        "outputs": [],
        "payable": true,
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "constant": true,
        "inputs": [{"name": "", "type": "address"}, {"name": "", "type": "address"}],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": false,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "payable": true,
        "stateMutability": "payable",
        "type": "fallback"
    },
    {
        "anonymous": false,
        "inputs": [{"indexed": true, "name": "src", "type": "address"}, {"indexed": true, "name": "guy", "type": "address"}, {"indexed": false, "name": "wad", "type": "uint256"}],
        "name": "Approval",
        "type": "event"
    },
    {
        "anonymous": false,
        "inputs": [{"indexed": true, "name": "src", "type": "address"}, {"indexed": true, "name": "dst", "type": "address"}, {"indexed": false, "name": "wad", "type": "uint256"}],
        "name": "Transfer",
        "type": "event"
    },
    {
        "anonymous": false,
        "inputs": [{"indexed": true, "name": "dst", "type": "address"}, {"indexed": false, "name": "wad", "type": "uint256"}],
        "name": "Deposit",
        "type": "event"
    },
    {
        "anonymous": false,
        "inputs": [{"indexed": true, "name": "src", "type": "address"}, {"indexed": false, "name": "wad", "type": "uint256"}],
        "name": "Withdrawal",
        "type": "event"
    }
]
'''

def unwrap_flare(amount_wflr, private_key=None, rpc_url=None):
    """
    Unwrap WFLR to native FLR on Flare network
    
    Args:
        amount_wflr (float): Amount of WFLR to unwrap
        private_key (str): Private key for the wallet
        rpc_url (str): RPC URL for the Flare network
        
    Returns:
        dict: Transaction receipt if successful, None otherwise
    """
    # Get environment variables if not provided
    if not rpc_url:
        rpc_url = os.getenv("FLARE_RPC_URL")
        if not rpc_url:
            print("ERROR: RPC URL is missing or empty!")
            return None
    
    print(f"Using RPC URL: {rpc_url}")
    
    if not private_key:
        private_key = os.getenv("PRIVATE_KEY")
        if not private_key:
            print("ERROR: Private key is missing or empty!")
            return None
        else:
            print("Private key is available (not showing for security)")
    
    # Derive wallet address from private key
    try:
        account = Account.from_key(private_key)
        wallet_address = account.address
        print(f"Using wallet address derived from private key: {wallet_address}")
    except Exception as e:
        print(f"ERROR: Failed to derive wallet address from private key: {e}")
        print(traceback.format_exc())
        return None
    
    # Debug: Check if amount_wflr is valid
    print(f"Amount to unwrap (raw input): {amount_wflr}, type: {type(amount_wflr)}")
    
    # Validate amount_wflr
    if amount_wflr is None:
        print("ERROR: amount_wflr is None")
        return None
    
    try:
        # Convert amount_wflr to float if it's a string
        if isinstance(amount_wflr, str):
            amount_wflr = float(amount_wflr)
        
        # Ensure amount_wflr is a number
        if not isinstance(amount_wflr, (int, float)):
            print(f"ERROR: amount_wflr must be a number, got {type(amount_wflr)}")
            return None
        
        print(f"Amount to unwrap (converted): {amount_wflr} WFLR")
    except Exception as e:
        print(f"ERROR: Failed to convert amount_wflr: {e}")
        print(traceback.format_exc())
        return None
    
    # Connect to the Flare network
    web3 = Web3(Web3.HTTPProvider(rpc_url))
    
    # Add middleware for POA networks
    web3.middleware_onion.inject(geth_poa_middleware, layer=0)
    
    # Check if connected to the network
    if not web3.is_connected():
        print("ERROR: Failed to connect to the Flare network")
        return None
    
    print(f"Connected to Flare network: {web3.is_connected()}")
    print(f"Current block number: {web3.eth.block_number}")
    
    # Check account balance
    account_balance = web3.eth.get_balance(wallet_address)
    print(f"Account balance: {web3.from_wei(account_balance, 'ether')} FLR")
    
    # Create contract instance
    wnat_contract = web3.eth.contract(address=Web3.to_checksum_address(WFLR_ADDRESS), abi=WFLR_ABI)
    
    try:
        # Try to get contract name and symbol
        try:
            contract_name = wnat_contract.functions.name().call()
            contract_symbol = wnat_contract.functions.symbol().call()
            print(f"Contract name: {contract_name}")
            print(f"Contract symbol: {contract_symbol}")
        except Exception as e:
            print(f"Could not get contract name/symbol: {e}")
        
        # Check initial balances
        try:
            initial_wflr_balance = wnat_contract.functions.balanceOf(wallet_address).call()
            print(f"Initial WFLR balance: {web3.from_wei(initial_wflr_balance, 'ether')} WFLR")
            
            initial_flr_balance = web3.eth.get_balance(wallet_address)
            print(f"Initial FLR balance: {web3.from_wei(initial_flr_balance, 'ether')} FLR")
        except Exception as e:
            print(f"Could not get initial balances: {e}")
            initial_wflr_balance = 0
            initial_flr_balance = 0
        
        # Amount of WFLR to unwrap (in wei, 1 WFLR = 10^18 wei)
        amount_to_unwrap = web3.to_wei(float(amount_wflr), 'ether')
        
        # Check if we have enough WFLR
        if initial_wflr_balance < amount_to_unwrap:
            print(f"ERROR: Not enough WFLR to unwrap. You have {web3.from_wei(initial_wflr_balance, 'ether')} WFLR but trying to unwrap {amount_wflr} WFLR")
            return None
        
        print(f"Preparing to unwrap {amount_wflr} WFLR to FLR...")
        
        # Get current gas price
        gas_price = web3.eth.gas_price
        print(f"Current gas price: {web3.from_wei(gas_price, 'gwei')} gwei")
        
        # Use a slightly higher gas price to ensure transaction goes through
        suggested_gas_price = int(gas_price * 1.1)
        print(f"Suggested gas price: {web3.from_wei(suggested_gas_price, 'gwei')} gwei")
        
        # Build transaction to unwrap WFLR
        transaction = wnat_contract.functions.withdraw(amount_to_unwrap).build_transaction({
            'from': wallet_address,
            'gas': 200000,  # Gas limit
            'gasPrice': suggested_gas_price,
            'nonce': web3.eth.get_transaction_count(wallet_address),
        })
        
        print(f"Transaction details: {json.dumps(dict(transaction), indent=2, default=str)}")
        
        # Sign transaction
        try:
            signed_txn = web3.eth.account.sign_transaction(transaction, private_key=private_key)
            print("Transaction signed successfully")
        except Exception as e:
            print(f"ERROR: Failed to sign transaction: {e}")
            print(traceback.format_exc())
            return None
        
        # Send transaction
        try:
            print(f"Sending transaction to unwrap {amount_wflr} WFLR to FLR...")
            txn_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            print(f"Transaction sent with hash: {txn_hash.hex()}")
        except Exception as e:
            print(f"ERROR: Failed to send transaction: {e}")
            print(traceback.format_exc())
            return None
        
        # Wait for transaction receipt
        try:
            print("Waiting for transaction confirmation...")
            txn_receipt = web3.eth.wait_for_transaction_receipt(txn_hash)
            print(f"Transaction receipt received")
        except Exception as e:
            print(f"ERROR: Failed to get transaction receipt: {e}")
            print(traceback.format_exc())
            return None
        
        print(f"Transaction receipt: {json.dumps(dict(txn_receipt), indent=2, default=str)}")
        
        if txn_receipt.status == 1:
            print(f"Transaction successful!")
            print(f"Transaction hash: {txn_receipt.transactionHash.hex()}")
            print(f"Gas used: {txn_receipt.gasUsed}")
            
            # Check new balances
            try:
                new_wflr_balance = wnat_contract.functions.balanceOf(wallet_address).call()
                new_flr_balance = web3.eth.get_balance(wallet_address)
                
                print(f"New WFLR balance: {web3.from_wei(new_wflr_balance, 'ether')} WFLR")
                print(f"WFLR change: {web3.from_wei(new_wflr_balance - initial_wflr_balance, 'ether')} WFLR")
                
                print(f"New FLR balance: {web3.from_wei(new_flr_balance, 'ether')} FLR")
                print(f"FLR change: {web3.from_wei(new_flr_balance - initial_flr_balance, 'ether')} FLR")
            except Exception as e:
                print(f"Could not get new balances: {e}")
            
            return txn_receipt
        else:
            print("Transaction failed!")
            
            # Try to get transaction details
            try:
                tx = web3.eth.get_transaction(txn_hash)
                print(f"Transaction details: {json.dumps(dict(tx), indent=2, default=str)}")
            except Exception as e:
                print(f"Error getting transaction details: {e}")
            
            return None
    
    except Exception as e:
        print(f"ERROR: Unexpected exception: {e}")
        print(traceback.format_exc())
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