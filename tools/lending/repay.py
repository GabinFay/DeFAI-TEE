#!/usr/bin/env python3
"""
Example script to repay borrowed tokens to the Kinetic protocol using the KineticSDK.
This example demonstrates how to:
1. Check borrowed balances
2. Repay borrowed tokens
3. Redeem collateral after repaying
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
    COLLATERAL_TOKEN = "flETH"  # Token supplied as collateral
    BORROW_TOKEN = "USDC.e"     # Token borrowed

    # Step 1: Check account balances and borrow status
    print_separator("Checking Account Status")
    try:
        # Check token balances
        collateral_balance = kinetic.get_account_balance(COLLATERAL_TOKEN)
        borrow_token_balance = kinetic.get_account_balance(BORROW_TOKEN)
        
        print(f"{COLLATERAL_TOKEN} balance: {collateral_balance}")
        print(f"{BORROW_TOKEN} balance: {borrow_token_balance}")
        
        # Check kToken balances (collateral)
        k_token = f"k{COLLATERAL_TOKEN}"
        ktoken_balance = kinetic.get_ktoken_balance(k_token)
        print(f"{k_token} balance (supplied collateral): {ktoken_balance}")
        
        # Check if we have any borrowed tokens to repay
        if borrow_token_balance <= 0:
            print(f"You don't have any {BORROW_TOKEN} to repay.")
            print(f"Please run the borrow script first or get some {BORROW_TOKEN}.")
            return
    except Exception as e:
        print(f"Error checking balances: {e}")
        return

    # Step 2: Check account liquidity before repaying
    print_separator("Checking Account Liquidity Before Repaying")
    try:
        liquidity = kinetic.get_account_liquidity()
        print(f"Account liquidity before repaying: {liquidity}")
    except Exception as e:
        print(f"Error checking liquidity: {e}")
        return

    # Step 3: Repay borrowed tokens
    print_separator(f"Repaying {BORROW_TOKEN}")
    try:
        # Repay a small amount (0.005 USDC.e or 50% of balance, whichever is smaller)
        amount_to_repay = min(0.005, borrow_token_balance * 0.5)
        
        # Repay borrowed tokens
        print(f"Repaying {amount_to_repay} {BORROW_TOKEN} to the Kinetic protocol...")
        tx_hash = kinetic.repay_borrow(BORROW_TOKEN, amount_to_repay)
        print(f"Repay transaction successful with hash: {tx_hash}")
        
        # Wait for the transaction to be processed
        print("Waiting for transaction to be processed...")
        time.sleep(5)
        
        # Get new borrow token balance
        new_borrow_balance = kinetic.get_account_balance(BORROW_TOKEN)
        print(f"New {BORROW_TOKEN} balance: {new_borrow_balance}")
        print(f"Change: {new_borrow_balance - borrow_token_balance} {BORROW_TOKEN}")
    except Exception as e:
        print(f"Error repaying {BORROW_TOKEN}: {e}")
        return

    # Step 4: Check account liquidity after repaying
    print_separator("Checking Account Liquidity After Repaying")
    try:
        liquidity = kinetic.get_account_liquidity()
        print(f"Account liquidity after repaying: {liquidity}")
    except Exception as e:
        print(f"Error checking liquidity: {e}")
        return

    # Step 5: Redeem some collateral (if we have any)
    print_separator(f"Redeeming {COLLATERAL_TOKEN} Collateral")
    try:
        # Check if we have any collateral to redeem
        if ktoken_balance <= 0:
            print(f"You don't have any {k_token} to redeem.")
            return
        
        # Redeem a small amount (10% of kToken balance)
        amount_to_redeem = ktoken_balance * 0.1
        
        # Get initial collateral token balance
        initial_collateral_balance = kinetic.get_account_balance(COLLATERAL_TOKEN)
        print(f"Initial {COLLATERAL_TOKEN} balance: {initial_collateral_balance}")
        
        # Redeem collateral
        print(f"Redeeming {amount_to_redeem} {k_token} from the Kinetic protocol...")
        tx_hash = kinetic.redeem(COLLATERAL_TOKEN, amount_to_redeem, redeem_type="ktoken")
        print(f"Redeem transaction successful with hash: {tx_hash}")
        
        # Wait for the transaction to be processed
        print("Waiting for transaction to be processed...")
        time.sleep(5)
        
        # Get new collateral token balance
        new_collateral_balance = kinetic.get_account_balance(COLLATERAL_TOKEN)
        print(f"New {COLLATERAL_TOKEN} balance: {new_collateral_balance}")
        print(f"Change: {new_collateral_balance - initial_collateral_balance} {COLLATERAL_TOKEN}")
        
        # Get new kToken balance
        new_ktoken_balance = kinetic.get_ktoken_balance(k_token)
        print(f"New {k_token} balance: {new_ktoken_balance}")
        print(f"Change: {new_ktoken_balance - ktoken_balance} {k_token}")
    except Exception as e:
        print(f"Error redeeming {COLLATERAL_TOKEN}: {e}")
        return

    # Step 6: Check final account liquidity
    print_separator("Final Account Liquidity")
    try:
        liquidity = kinetic.get_account_liquidity()
        print(f"Final account liquidity: {liquidity}")
    except Exception as e:
        print(f"Error checking final liquidity: {e}")

    print_separator("Repayment Process Complete")
    print(f"You have successfully:")
    print(f"1. Repaid some of your borrowed {BORROW_TOKEN}")
    print(f"2. Redeemed some of your {COLLATERAL_TOKEN} collateral")
    print(f"Your account is now in a healthier position!")

if __name__ == "__main__":
    main() 