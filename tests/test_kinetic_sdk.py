#!/usr/bin/env python3
"""
Test script for the Kinetic SDK.
This script demonstrates various features of the Kinetic SDK including:
- Checking account balances
- Supplying tokens to the protocol
- Borrowing tokens from the protocol
- Repaying borrowed tokens
- Redeeming supplied tokens
- Getting account liquidity
- Entering and exiting markets
"""

import os
import sys
import time
from dotenv import load_dotenv

# Import the Kinetic SDK
from kinetic_py.kinetic_sdk import KineticSDK
from kinetic_py.constants import KINETIC_TOKENS

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

    # Test 1: Get all available markets
    print_separator("Available Markets")
    try:
        markets = kinetic.get_all_markets()
        print(f"Available markets: {markets}")
    except Exception as e:
        print(f"Error getting markets: {e}")

    # Test 2: Check account balances for all tokens
    print_separator("Account Balances")
    for token_name in KINETIC_TOKENS:
        if not token_name.startswith('k'):  # Only check underlying tokens
            try:
                balance = kinetic.get_account_balance(token_name)
                print(f"{token_name} balance: {balance}")
            except Exception as e:
                print(f"Error getting {token_name} balance: {e}")

    # Test 3: Check kToken balances
    print_separator("kToken Balances")
    for token_name in KINETIC_TOKENS:
        if token_name.startswith('k'):  # Only check kTokens
            try:
                balance = kinetic.get_ktoken_balance(token_name)
                print(f"{token_name} balance: {balance}")
            except Exception as e:
                print(f"Error getting {token_name} balance: {e}")

    # Test 4: Get exchange rates for all tokens
    print_separator("Exchange Rates")
    for token_name in KINETIC_TOKENS:
        if not token_name.startswith('k'):  # Only check underlying tokens
            try:
                exchange_rate = kinetic.get_exchange_rate(token_name)
                print(f"{token_name} exchange rate: {exchange_rate} {token_name} per k{token_name}")
            except Exception as e:
                print(f"Error getting {token_name} exchange rate: {e}")

    # Test 5: Get account liquidity
    print_separator("Account Liquidity")
    try:
        liquidity = kinetic.get_account_liquidity()
        print(f"Account liquidity: {liquidity}")
    except Exception as e:
        print(f"Error getting account liquidity: {e}")

    # Test 6: Enter markets (if not already entered)
    print_separator("Enter Markets")
    try:
        # Choose a few tokens to enter markets with
        tokens_to_enter = ['flETH', 'USDC.e']
        result = kinetic.enter_markets(tokens_to_enter)
        print(f"Enter markets result: {result}")
    except Exception as e:
        print(f"Error entering markets: {e}")

    # Test 7: Supply a small amount of flETH (if available)
    print_separator("Supply flETH")
    try:
        fleth_balance = kinetic.get_account_balance("flETH")
        print(f"Current flETH balance: {fleth_balance}")
        
        if fleth_balance > 0:
            # Supply a very small amount (0.00001 flETH)
            amount_to_supply = min(0.00001, fleth_balance * 0.01)  # Use at most 1% of balance
            
            # Get initial kflETH balance
            initial_kfleth_balance = kinetic.get_ktoken_balance("kflETH")
            print(f"Initial kflETH balance: {initial_kfleth_balance}")
            
            # Supply flETH
            print(f"Supplying {amount_to_supply} flETH to the Kinetic protocol...")
            tx_hash = kinetic.supply("flETH", amount_to_supply)
            print(f"Supply transaction successful with hash: {tx_hash}")
            
            # Wait a bit for the transaction to be processed
            print("Waiting for transaction to be processed...")
            time.sleep(5)
            
            # Get new kflETH balance
            new_kfleth_balance = kinetic.get_ktoken_balance("kflETH")
            print(f"New kflETH balance: {new_kfleth_balance}")
            print(f"Change: {new_kfleth_balance - initial_kfleth_balance} kflETH")
        else:
            print("Not enough flETH balance to supply.")
    except Exception as e:
        print(f"Error supplying flETH: {e}")

    # Test 8: Borrow a small amount of USDC.e (if available and enough collateral)
    print_separator("Borrow USDC.e")
    try:
        # Check if we have enough collateral
        liquidity = kinetic.get_account_liquidity()
        print(f"Account liquidity before borrowing: {liquidity}")
        
        if liquidity.get('liquidity', 0) > 0:
            # Borrow a very small amount (0.01 USDC.e)
            amount_to_borrow = 0.01
            
            # Get initial USDC.e balance
            initial_usdc_balance = kinetic.get_account_balance("USDC.e")
            print(f"Initial USDC.e balance: {initial_usdc_balance}")
            
            # Borrow USDC.e
            print(f"Borrowing {amount_to_borrow} USDC.e from the Kinetic protocol...")
            tx_hash = kinetic.borrow("USDC.e", amount_to_borrow)
            print(f"Borrow transaction successful with hash: {tx_hash}")
            
            # Wait a bit for the transaction to be processed
            print("Waiting for transaction to be processed...")
            time.sleep(5)
            
            # Get new USDC.e balance
            new_usdc_balance = kinetic.get_account_balance("USDC.e")
            print(f"New USDC.e balance: {new_usdc_balance}")
            print(f"Change: {new_usdc_balance - initial_usdc_balance} USDC.e")
            
            # Check liquidity after borrowing
            liquidity = kinetic.get_account_liquidity()
            print(f"Account liquidity after borrowing: {liquidity}")
        else:
            print("Not enough collateral to borrow.")
    except Exception as e:
        print(f"Error borrowing USDC.e: {e}")

    # Test 9: Repay borrowed USDC.e (if any was borrowed)
    print_separator("Repay USDC.e")
    try:
        # Check if we have any USDC.e to repay
        usdc_balance = kinetic.get_account_balance("USDC.e")
        print(f"Current USDC.e balance: {usdc_balance}")
        
        if usdc_balance > 0:
            # Repay a very small amount (0.005 USDC.e)
            amount_to_repay = min(0.005, usdc_balance * 0.5)  # Use at most 50% of balance
            
            # Repay USDC.e
            print(f"Repaying {amount_to_repay} USDC.e to the Kinetic protocol...")
            tx_hash = kinetic.repay_borrow("USDC.e", amount_to_repay)
            print(f"Repay transaction successful with hash: {tx_hash}")
            
            # Wait a bit for the transaction to be processed
            print("Waiting for transaction to be processed...")
            time.sleep(5)
            
            # Get new USDC.e balance
            new_usdc_balance = kinetic.get_account_balance("USDC.e")
            print(f"New USDC.e balance: {new_usdc_balance}")
            print(f"Change: {new_usdc_balance - usdc_balance} USDC.e")
        else:
            print("No USDC.e balance to repay.")
    except Exception as e:
        print(f"Error repaying USDC.e: {e}")

    # Test 10: Redeem supplied flETH (if any was supplied)
    print_separator("Redeem flETH")
    try:
        # Check if we have any kflETH to redeem
        kfleth_balance = kinetic.get_ktoken_balance("kflETH")
        print(f"Current kflETH balance: {kfleth_balance}")
        
        if kfleth_balance > 0:
            # Redeem a very small amount (10% of kflETH balance)
            amount_to_redeem = kfleth_balance * 0.1
            
            # Get initial flETH balance
            initial_fleth_balance = kinetic.get_account_balance("flETH")
            print(f"Initial flETH balance: {initial_fleth_balance}")
            
            # Redeem kflETH
            print(f"Redeeming {amount_to_redeem} kflETH from the Kinetic protocol...")
            tx_hash = kinetic.redeem("flETH", amount_to_redeem, redeem_type="ktoken")
            print(f"Redeem transaction successful with hash: {tx_hash}")
            
            # Wait a bit for the transaction to be processed
            print("Waiting for transaction to be processed...")
            time.sleep(5)
            
            # Get new flETH balance
            new_fleth_balance = kinetic.get_account_balance("flETH")
            print(f"New flETH balance: {new_fleth_balance}")
            print(f"Change: {new_fleth_balance - initial_fleth_balance} flETH")
        else:
            print("No kflETH balance to redeem.")
    except Exception as e:
        print(f"Error redeeming flETH: {e}")

    # Test 11: Exit market (if entered)
    print_separator("Exit Market")
    try:
        # Exit the USDC.e market
        result = kinetic.exit_market("USDC.e")
        print(f"Exit market result: {result}")
    except Exception as e:
        print(f"Error exiting market: {e}")

    # Final check: Get account liquidity
    print_separator("Final Account Liquidity")
    try:
        liquidity = kinetic.get_account_liquidity()
        print(f"Final account liquidity: {liquidity}")
    except Exception as e:
        print(f"Error getting final account liquidity: {e}")

if __name__ == "__main__":
    main() 