#!/usr/bin/env python3
"""
Script to get flrETH tokens on Flare network
"""

from dotenv import load_dotenv
import os
import json
import sys
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

# Load environment variables from .env file
load_dotenv()

def get_flreth(amount_flr):
    """
    Get flrETH tokens by swapping FLR or using a wrapper contract
    
    Args:
        amount_flr (float): Amount of FLR to convert to flrETH
        
    Returns:
        dict: Transaction receipt if successful, None otherwise
    """
    # Get environment variables
    FLARE_RPC_URL = os.getenv("FLARE_RPC_URL")
    WALLET_ADDRESS = os.getenv("WALLET_ADDRESS")
    PRIVATE_KEY = os.getenv("PRIVATE_KEY")

    # Validate environment variables
    if not FLARE_RPC_URL:
        print("Error: FLARE_RPC_URL environment variable is not set.")
        print("Please create a .env file with FLARE_RPC_URL=https://flare-api.flare.network/ext/C/rpc")
        return None

    if not WALLET_ADDRESS:
        print("Error: WALLET_ADDRESS environment variable is not set.")
        print("Please create a .env file with WALLET_ADDRESS=your_wallet_address")
        return None

    if not PRIVATE_KEY:
        print("Error: PRIVATE_KEY environment variable is not set.")
        print("Please create a .env file with PRIVATE_KEY=your_private_key")
        return None

    print(f"Using RPC URL: {FLARE_RPC_URL}")
    print(f"Using wallet address: {WALLET_ADDRESS}")

    # Connect to the Flare network
    web3 = Web3(Web3.HTTPProvider(FLARE_RPC_URL))

    # Add middleware for POA networks
    web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

    # Check if connected to the network
    if not web3.is_connected():
        print("Error: Failed to connect to the Flare network")
        return None

    print(f"Connected to Flare network: {web3.is_connected()}")
    print(f"Current block number: {web3.eth.block_number}")

    # Check account balance
    try:
        account_balance = web3.eth.get_balance(WALLET_ADDRESS)
        print(f"Account balance: {web3.from_wei(account_balance, 'ether')} FLR")
        
        if account_balance < web3.to_wei(amount_flr, 'ether'):
            print(f"Not enough FLR balance. You need at least {amount_flr} FLR.")
            return None
    except Exception as e:
        print(f"Error getting account balance: {e}")
        print("Please check that your WALLET_ADDRESS is correct")
        return None

    # flrETH token address (from your lending script)
    flreth_address = '0x26A1faB310bd080542DC864647d05985360B16A5'
    
    # ERC20 ABI for flrETH
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
            "constant": false,
            "inputs": [],
            "name": "deposit",
            "outputs": [],
            "payable": true,
            "stateMutability": "payable",
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
        }
    ]
    '''

    # Create flrETH contract instance
    flreth_contract = web3.eth.contract(address=flreth_address, abi=erc20_abi)
    
    # Check if we already have flrETH
    try:
        flreth_balance = flreth_contract.functions.balanceOf(WALLET_ADDRESS).call()
        flreth_name = flreth_contract.functions.name().call()
        flreth_symbol = flreth_contract.functions.symbol().call()
        
        print(f"Current {flreth_symbol} balance: {web3.from_wei(flreth_balance, 'ether')} {flreth_symbol}")
        
        if flreth_balance >= web3.to_wei(0.1, 'ether'):
            print(f"You already have enough {flreth_symbol} to lend to Kinetic!")
            return None
    except Exception as e:
        print(f"Error checking flrETH balance: {e}")
    
    print(f"Attempting to get {amount_flr} {flreth_symbol} tokens...")
    
    # Try to use the deposit function if it exists (for wrapped tokens)
    try:
        # Check if the contract has a deposit function
        print("Checking if flrETH is a wrapped token with deposit function...")
        
        # Get current gas price
        gas_price = web3.eth.gas_price
        print(f"Current gas price: {web3.from_wei(gas_price, 'gwei')} gwei")
        
        # Use a slightly higher gas price to ensure transaction goes through
        suggested_gas_price = int(gas_price * 1.1)
        print(f"Suggested gas price: {web3.from_wei(suggested_gas_price, 'gwei')} gwei")
        
        # Amount to convert
        amount_to_convert = web3.to_wei(amount_flr, 'ether')
        
        # Try to build a deposit transaction
        try:
            deposit_tx = flreth_contract.functions.deposit().build_transaction({
                'from': WALLET_ADDRESS,
                'gas': 200000,
                'gasPrice': suggested_gas_price,
                'nonce': web3.eth.get_transaction_count(WALLET_ADDRESS),
                'value': amount_to_convert
            })
            
            print(f"flrETH appears to be a wrapped token. Wrapping {amount_flr} FLR...")
            
            # Sign transaction
            signed_deposit_tx = web3.eth.account.sign_transaction(deposit_tx, private_key=PRIVATE_KEY)
            
            # Send transaction
            print(f"Sending deposit transaction...")
            deposit_tx_hash = web3.eth.send_raw_transaction(signed_deposit_tx.raw_transaction)
            print(f"Deposit transaction sent with hash: {deposit_tx_hash.hex()}")
            
            # Wait for transaction receipt
            print("Waiting for deposit transaction confirmation...")
            deposit_tx_receipt = web3.eth.wait_for_transaction_receipt(deposit_tx_hash)
            
            if deposit_tx_receipt.status == 1:
                print("Deposit transaction successful!")
                
                # Check new flrETH balance
                new_flreth_balance = flreth_contract.functions.balanceOf(WALLET_ADDRESS).call()
                print(f"New {flreth_symbol} balance: {web3.from_wei(new_flreth_balance, 'ether')} {flreth_symbol}")
                print(f"Change: {web3.from_wei(new_flreth_balance - flreth_balance, 'ether')} {flreth_symbol}")
                
                return deposit_tx_receipt
            else:
                print("Deposit transaction failed!")
                return None
                
        except Exception as e:
            print(f"Error with deposit function: {e}")
            print("flrETH might not be a simple wrapped token.")
    except Exception as e:
        print(f"Could not use deposit function: {e}")
    
    # If we get here, we couldn't use the deposit function
    print("\nCould not directly wrap FLR to flrETH.")
    print("You may need to:")
    print("1. Use a DEX (decentralized exchange) to swap FLR for flrETH")
    print("2. Check if there's a staking mechanism to get flrETH")
    print("3. Look for a bridge that allows you to bring ETH from Ethereum to Flare as flrETH")
    print("4. Check the Flare documentation for how to acquire flrETH")
    
    # Try to find a router or exchange contract
    print("\nLooking for known DEX routers on Flare...")
    
    # Common DEX router addresses on Flare (these are examples and may not be accurate)
    # You would need to replace these with actual DEX router addresses on Flare
    dex_routers = {
        "FlareSwap": "0x...",  # Replace with actual address if known
        "SushiSwap": "0x...",  # Replace with actual address if known
        "PangolinDEX": "0x..."  # Replace with actual address if known
    }
    
    print("\nPlease visit one of these DEXes to swap FLR for flrETH:")
    print("- FlareSwap: https://flareswap.org")  # Replace with actual URL
    print("- SushiSwap Flare: https://app.sushi.com/swap")  # Replace with actual URL
    print("- Other Flare DEXes")
    
    return None

if __name__ == "__main__":
    # Try to get 0.1 flrETH
    get_flreth(0.1) 