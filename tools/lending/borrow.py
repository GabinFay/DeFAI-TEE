#!/usr/bin/env python3
"""
Example script to borrow tokens from the Kinetic protocol using the KineticSDK.
This example demonstrates how to:
1. Check account balances
2. Enter markets (to use tokens as collateral)
3. Supply tokens as collateral
4. Borrow other tokens against the collateral
"""

import os
import sys
import time
from dotenv import load_dotenv

# Import the Kinetic SDK
from kinetic_py.kinetic_sdk import KineticSDK

# Load environment variables from .env file
load_dotenv()

def print_separator(title):
    """Print a separator with a title."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")

def main():
    # Get environment variables
    FLARE_RPC_URL = os.getenv("FLARE_RPC_URL")
    WALLET_ADDRESS = os.getenv("WALLET_ADDRESS")
    PRIVATE_KEY = os.getenv("PRIVATE_KEY")

    # Validate environment variables
    if not FLARE_RPC_URL:
        print("Error: FLARE_RPC_URL environment variable is not set.")
        print("Please create a .env file with FLARE_RPC_URL=https://flare-api.flare.network/ext/C/rpc")
        return

    if not WALLET_ADDRESS:
        print("Error: WALLET_ADDRESS environment variable is not set.")
        print("Please create a .env file with WALLET_ADDRESS=your_wallet_address")
        return

    if not PRIVATE_KEY:
        print("Error: PRIVATE_KEY environment variable is not set.")
        print("Please create a .env file with PRIVATE_KEY=your_private_key")
        return

    print(f"Using RPC URL: {FLARE_RPC_URL}")
    print(f"Using wallet address: {WALLET_ADDRESS}")

    # Initialize the Kinetic SDK
    print_separator("Initializing Kinetic SDK")
    kinetic = KineticSDK(
        provider=FLARE_RPC_URL,
        options={
            'privateKey': PRIVATE_KEY,
            'walletAddress': WALLET_ADDRESS
        }
    )

    # Check if connected to the network
    print(f"Connected to Flare network: {kinetic.web3.is_connected()}")
    print(f"Current block number: {kinetic.web3.eth.block_number}")

    # Define the tokens we'll be working with
    COLLATERAL_TOKEN = "flETH"  # Token to supply as collateral
    BORROW_TOKEN = "USDC.e"     # Token to borrow

    # Step 1: Check account balances
    print_separator(f"Checking Account Balances")
    try:
        collateral_balance = kinetic.get_account_balance(COLLATERAL_TOKEN)
        borrow_token_balance = kinetic.get_account_balance(BORROW_TOKEN)
        
        print(f"{COLLATERAL_TOKEN} balance: {collateral_balance}")
        print(f"{BORROW_TOKEN} balance: {borrow_token_balance}")
        
        # Check if we have any collateral token to supply
        if collateral_balance <= 0:
            print(f"You don't have any {COLLATERAL_TOKEN} to supply as collateral.")
            print(f"Please get some {COLLATERAL_TOKEN} before running this script.")
            return
    except Exception as e:
        print(f"Error checking balances: {e}")
        return

    # Step 2: Enter markets (to use tokens as collateral)
    print_separator(f"Entering {COLLATERAL_TOKEN} Market")
    try:
        result = kinetic.enter_markets([COLLATERAL_TOKEN])
        print(f"Enter markets result: {result}")
    except Exception as e:
        print(f"Error entering markets: {e}")
        return

    # Step 3: Supply tokens as collateral
    print_separator(f"Supplying {COLLATERAL_TOKEN} as Collateral")
    try:
        # Supply a small amount (0.00001 or 1% of balance, whichever is smaller)
        amount_to_supply = min(0.00001, collateral_balance * 0.01)
        
        # Get initial kToken balance
        k_token = f"k{COLLATERAL_TOKEN}"
        initial_ktoken_balance = kinetic.get_ktoken_balance(k_token)
        print(f"Initial {k_token} balance: {initial_ktoken_balance}")
        
        # Supply collateral
        print(f"Supplying {amount_to_supply} {COLLATERAL_TOKEN} to the Kinetic protocol...")
        tx_hash = kinetic.supply(COLLATERAL_TOKEN, amount_to_supply)
        print(f"Supply transaction successful with hash: {tx_hash}")
        
        # Wait for the transaction to be processed
        print("Waiting for transaction to be processed...")
        time.sleep(5)
        
        # Get new kToken balance
        new_ktoken_balance = kinetic.get_ktoken_balance(k_token)
        print(f"New {k_token} balance: {new_ktoken_balance}")
        print(f"Change: {new_ktoken_balance - initial_ktoken_balance} {k_token}")
    except Exception as e:
        print(f"Error supplying {COLLATERAL_TOKEN}: {e}")
        return

    # Step 4: Check account liquidity
    print_separator("Checking Account Liquidity")
    try:
        liquidity = kinetic.get_account_liquidity()
        print(f"Account liquidity: {liquidity}")
        
        # Check if we have enough liquidity to borrow
        if liquidity.get('liquidity', 0) <= 0:
            print(f"Not enough liquidity to borrow. Please supply more collateral.")
            return
    except Exception as e:
        print(f"Error checking liquidity: {e}")
        return

    # Step 5: Borrow tokens
    print_separator(f"Borrowing {BORROW_TOKEN}")
    try:
        # Borrow a very small amount (0.01 USDC.e or equivalent)
        amount_to_borrow = 0.01
        
        # Get initial borrow token balance
        initial_borrow_balance = kinetic.get_account_balance(BORROW_TOKEN)
        print(f"Initial {BORROW_TOKEN} balance: {initial_borrow_balance}")
        
        # Borrow tokens
        print(f"Borrowing {amount_to_borrow} {BORROW_TOKEN} from the Kinetic protocol...")
        tx_hash = kinetic.borrow(BORROW_TOKEN, amount_to_borrow)
        print(f"Borrow transaction successful with hash: {tx_hash}")
        
        # Wait for the transaction to be processed
        print("Waiting for transaction to be processed...")
        time.sleep(5)
        
        # Get new borrow token balance
        new_borrow_balance = kinetic.get_account_balance(BORROW_TOKEN)
        print(f"New {BORROW_TOKEN} balance: {new_borrow_balance}")
        print(f"Change: {new_borrow_balance - initial_borrow_balance} {BORROW_TOKEN}")
    except Exception as e:
        print(f"Error borrowing {BORROW_TOKEN}: {e}")
        return

    # Step 6: Check final account liquidity
    print_separator("Final Account Liquidity")
    try:
        liquidity = kinetic.get_account_liquidity()
        print(f"Final account liquidity: {liquidity}")
    except Exception as e:
        print(f"Error checking final liquidity: {e}")

    print_separator("Borrowing Process Complete")
    print(f"You have successfully:")
    print(f"1. Supplied {COLLATERAL_TOKEN} as collateral")
    print(f"2. Borrowed {BORROW_TOKEN} against your collateral")
    print(f"Remember to repay your loan to avoid liquidation!")

if __name__ == "__main__":
    main() 