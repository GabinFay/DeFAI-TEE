#!/usr/bin/env python3
"""
Script to unwrap WFLR (Wrapped Flare) back to native FLR on Flare network
"""

# Load wallet details from .env file
from dotenv import load_dotenv
import os
import json

load_dotenv()

from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

# Get environment variables
FLARE_RPC_URL = os.getenv("FLARE_RPC_URL")
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

print(f"Using RPC URL: {FLARE_RPC_URL}")
print(f"Using wallet address: {WALLET_ADDRESS}")

# Connect to the Flare network
web3 = Web3(Web3.HTTPProvider(FLARE_RPC_URL))

# Add middleware for POA networks
web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

# Check if connected to the network
if not web3.is_connected():
    raise Exception("Failed to connect to the Flare network")

print(f"Connected to Flare network: {web3.is_connected()}")
print(f"Current block number: {web3.eth.block_number}")

# Check account balance
account_balance = web3.eth.get_balance(WALLET_ADDRESS)
print(f"Account balance: {web3.from_wei(account_balance, 'ether')} FLR")

# WNat (WFLR) contract address on Flare
wnat_contract_address = '0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d'  # WFLR address

# Standard WETH9-like ABI (which WFLR follows)
wnat_abi = '''
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

# Create contract instance
wnat_contract = web3.eth.contract(address=wnat_contract_address, abi=wnat_abi)

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
        initial_wflr_balance = wnat_contract.functions.balanceOf(WALLET_ADDRESS).call()
        print(f"Initial WFLR balance: {web3.from_wei(initial_wflr_balance, 'ether')} WFLR")
        
        initial_flr_balance = web3.eth.get_balance(WALLET_ADDRESS)
        print(f"Initial FLR balance: {web3.from_wei(initial_flr_balance, 'ether')} FLR")
    except Exception as e:
        print(f"Could not get initial balances: {e}")
        initial_wflr_balance = 0
        initial_flr_balance = 0

    # Amount of WFLR to unwrap (in wei, 1 WFLR = 10^18 wei)
    amount_to_unwrap = web3.to_wei(1, 'ether')  # Unwrapping 1 WFLR
    
    # Check if we have enough WFLR
    if initial_wflr_balance < amount_to_unwrap:
        print(f"Not enough WFLR to unwrap. You have {web3.from_wei(initial_wflr_balance, 'ether')} WFLR but trying to unwrap {web3.from_wei(amount_to_unwrap, 'ether')} WFLR")
        exit(1)
    
    # Get current gas price
    gas_price = web3.eth.gas_price
    print(f"Current gas price: {web3.from_wei(gas_price, 'gwei')} gwei")
    
    # Use a slightly higher gas price to ensure transaction goes through
    suggested_gas_price = int(gas_price * 1.1)
    print(f"Suggested gas price: {web3.from_wei(suggested_gas_price, 'gwei')} gwei")
    
    # Build transaction to unwrap WFLR
    transaction = wnat_contract.functions.withdraw(amount_to_unwrap).build_transaction({
        'from': WALLET_ADDRESS,
        'gas': 200000,  # Gas limit
        'gasPrice': suggested_gas_price,
        'nonce': web3.eth.get_transaction_count(WALLET_ADDRESS),
    })
    
    print(f"Transaction details: {json.dumps(dict(transaction), indent=2, default=str)}")

    # Sign transaction
    signed_txn = web3.eth.account.sign_transaction(transaction, private_key=PRIVATE_KEY)

    # Send transaction
    print(f"Sending transaction to unwrap {web3.from_wei(amount_to_unwrap, 'ether')} WFLR to FLR...")
    txn_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
    print(f"Transaction sent with hash: {txn_hash.hex()}")

    # Wait for transaction receipt
    print("Waiting for transaction confirmation...")
    txn_receipt = web3.eth.wait_for_transaction_receipt(txn_hash)
    
    print(f"Transaction receipt: {json.dumps(dict(txn_receipt), indent=2, default=str)}")
    
    if txn_receipt.status == 1:
        print(f"Transaction successful!")
        print(f"Transaction hash: {txn_receipt.transactionHash.hex()}")
        print(f"Gas used: {txn_receipt.gasUsed}")
        
        # Check new balances
        try:
            new_wflr_balance = wnat_contract.functions.balanceOf(WALLET_ADDRESS).call()
            print(f"New WFLR balance: {web3.from_wei(new_wflr_balance, 'ether')} WFLR")
            print(f"WFLR Change: {web3.from_wei(new_wflr_balance - initial_wflr_balance, 'ether')} WFLR")
            
            new_flr_balance = web3.eth.get_balance(WALLET_ADDRESS)
            print(f"New FLR balance: {web3.from_wei(new_flr_balance, 'ether')} FLR")
            print(f"FLR Change: {web3.from_wei(new_flr_balance - initial_flr_balance, 'ether')} FLR")
        except Exception as e:
            print(f"Could not get new balances: {e}")
    else:
        print("Transaction failed!")
        
        # Try to get transaction details
        try:
            tx = web3.eth.get_transaction(txn_hash)
            print(f"Transaction details: {json.dumps(dict(tx), indent=2, default=str)}")
        except Exception as e:
            print(f"Error getting transaction details: {e}")

except Exception as e:
    print(f"Error: {e}") 