#!/usr/bin/env python3
"""
Script to fetch and display token balances for a user on Flare network
"""

import os
from dotenv import load_dotenv
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account
import json
from tabulate import tabulate

# Load environment variables
load_dotenv()

# Token contract addresses on Flare network
FLARE_TOKENS = {
    'flrETH': '0x26A1faB310bd080542DC864647d05985360B16A5',
    'sFLR': '0x12e605bc104e93B45e1aD99F9e555f659051c2BB',
    'Joule': '0xE6505f92583103AF7ed9974DEC451A7Af4e3A3bE',
    'Usdx': '0xFE2907DFa8DB6e320cDbF45f0aa888F6135ec4f8',
    'USDT': '0x0B38e83B86d491735fEaa0a791F65c2B99535396',
    'USDC': '0xFbDa5F676cB37624f28265A144A48B0d6e87d3b6',
    'XVN': '0xaFBdD875858Dd48EE32A68Ac1349A5017095B161',
    'WFLR': '0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d',
    'cysFLR': '0x19831cfB53A0dbeAD9866C43557C1D48DfF76567',
    'WETH': '0x1502FA4be69d526124D453619276FacCab275d3D',
}

# ERC20 Token ABI (only the necessary parts)
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
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
]

def initialize_web3():
    """
    Initialize Web3 connection to Flare network
    
    Returns:
        tuple: (web3, wallet_address) - Web3 instance and user's wallet address
    """
    # Get environment variables
    flare_rpc_url = os.getenv("FLARE_RPC_URL", "https://flare-api.flare.network/ext/C/rpc")
    
    # Get wallet address from environment or private key
    wallet_address = os.getenv("WALLET_ADDRESS")
    private_key = os.getenv("PRIVATE_KEY")
    
    if private_key and not wallet_address:
        # Derive wallet address from private key
        account = Account.from_key(private_key)
        wallet_address = account.address
    
    if not wallet_address:
        raise ValueError("WALLET_ADDRESS must be set in .env file or derived from PRIVATE_KEY")
    
    # Initialize Web3
    web3 = Web3(Web3.HTTPProvider(flare_rpc_url))
    web3.middleware_onion.inject(geth_poa_middleware, layer=0)
    
    # Check connection
    if not web3.is_connected():
        raise ConnectionError(f"Failed to connect to Flare network at {flare_rpc_url}")
    
    print(f"Connected to Flare network: Chain ID {web3.eth.chain_id}")
    print(f"Using wallet address: {wallet_address}")
    
    return web3, wallet_address

def get_token_balance(web3, token_address, wallet_address):
    """
    Get the balance of a specific token for a user
    
    Args:
        web3 (Web3): Web3 instance
        token_address (str): Token contract address
        wallet_address (str): User's wallet address
        
    Returns:
        dict: Token information including name, symbol, balance, and decimals
    """
    # Convert addresses to checksum format
    token_address = Web3.to_checksum_address(token_address)
    wallet_address = Web3.to_checksum_address(wallet_address)
    
    # Create token contract instance
    token_contract = web3.eth.contract(address=token_address, abi=ERC20_ABI)
    
    try:
        # Get token information
        decimals = token_contract.functions.decimals().call()
        symbol = token_contract.functions.symbol().call()
        name = token_contract.functions.name().call()
        
        # Get token balance
        balance_wei = token_contract.functions.balanceOf(wallet_address).call()
        balance = balance_wei / (10 ** decimals)
        
        return {
            "address": token_address,
            "name": name,
            "symbol": symbol,
            "balance_wei": balance_wei,
            "balance": balance,
            "decimals": decimals
        }
    except Exception as e:
        print(f"Error getting balance for token at {token_address}: {str(e)}")
        return {
            "address": token_address,
            "name": "Unknown",
            "symbol": "???",
            "balance_wei": 0,
            "balance": 0,
            "decimals": 18
        }

def get_native_balance(web3, wallet_address):
    """
    Get the native FLR balance for a user
    
    Args:
        web3 (Web3): Web3 instance
        wallet_address (str): User's wallet address
        
    Returns:
        dict: Token information for native FLR
    """
    # Get native balance
    balance_wei = web3.eth.get_balance(wallet_address)
    balance = web3.from_wei(balance_wei, 'ether')
    
    return {
        "address": "0x0000000000000000000000000000000000000000",
        "name": "Flare",
        "symbol": "FLR",
        "balance_wei": balance_wei,
        "balance": balance,
        "decimals": 18
    }

def display_token_balances(wallet_address=None):
    """
    Display token balances for a user on Flare network
    
    Args:
        wallet_address (str, optional): User's wallet address. If None, will use from .env
        
    Returns:
        list: List of token balance information dictionaries
    """
    # Initialize Web3 and get wallet address
    web3, user_address = initialize_web3()
    
    # Use provided wallet address if specified
    if wallet_address:
        user_address = wallet_address
    
    # Get native FLR balance
    balances = [get_native_balance(web3, user_address)]
    
    # Get token balances
    for token_name, token_address in FLARE_TOKENS.items():
        token_info = get_token_balance(web3, token_address, user_address)
        balances.append(token_info)
    
    # Filter out zero balances
    non_zero_balances = [b for b in balances if b["balance"] > 0]
    
    # Prepare data for tabulate
    table_data = [
        [
            i+1,
            b["symbol"],
            b["name"],
            f"{b['balance']:.6f}",
            b["address"]
        ] for i, b in enumerate(non_zero_balances)
    ]
    
    # Display balances in a table
    headers = ["#", "Symbol", "Name", "Balance", "Contract Address"]
    print("\nToken Balances:")
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    # Also display all tokens including zero balances
    if len(non_zero_balances) < len(balances):
        print("\nAll Tokens (including zero balances):")
        all_table_data = [
            [
                i+1,
                b["symbol"],
                b["name"],
                f"{b['balance']:.6f}",
                b["address"]
            ] for i, b in enumerate(balances)
        ]
        print(tabulate(all_table_data, headers=headers, tablefmt="grid"))
    
    return balances

if __name__ == "__main__":
    display_token_balances()