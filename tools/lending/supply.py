#!/usr/bin/env python3
"""
Example script to supply flETH to the Kinetic protocol using the new KineticSDK.
This example demonstrates how to use the SDK in a similar way to the compound-js SDK.
"""

import os
import sys
from dotenv import load_dotenv

# Add the parent directory to the path so we can import the kinetic_py module directly
from kinetic_py.kinetic_sdk import KineticSDK

# Load environment variables from .env file
load_dotenv()

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

    # Check account balance
    try:
        fleth_balance = kinetic.get_account_balance("flETH")
        print(f"flETH balance: {fleth_balance}")
    except Exception as e:
        print(f"Error getting flETH balance: {e}")
        return

    # Amount of flETH to supply
    amount_to_supply = 0.00001

    # Check if we have enough flETH
    if fleth_balance < amount_to_supply:
        print(f"Not enough flETH balance. You have {fleth_balance} flETH, but you need {amount_to_supply} flETH.")
        return

    # Get initial kflETH balance
    try:
        initial_kfleth_balance = kinetic.get_ktoken_balance("kflETH")
        print(f"Initial kflETH balance: {initial_kfleth_balance}")
    except Exception as e:
        print(f"Error getting initial kflETH balance: {e}")
        initial_kfleth_balance = 0

    # Get current exchange rate
    try:
        exchange_rate = kinetic.get_exchange_rate("flETH")
        print(f"Current exchange rate: {exchange_rate} flETH per kflETH")
    except Exception as e:
        print(f"Error getting exchange rate: {e}")

    # Supply flETH to the Kinetic protocol
    print(f"Supplying {amount_to_supply} flETH to the Kinetic protocol...")
    try:
        # Use the direct supply method
        tx_hash = kinetic.supply("flETH", amount_to_supply)
        print(f"Supply transaction successful with hash: {tx_hash}")
    except Exception as e:
        print(f"Error supplying flETH: {e}")
        return

    # Get new kflETH balance
    try:
        new_kfleth_balance = kinetic.get_ktoken_balance("kflETH")
        print(f"New kflETH balance: {new_kfleth_balance}")
        print(f"Change: {new_kfleth_balance - initial_kfleth_balance} kflETH")
    except Exception as e:
        print(f"Error getting new kflETH balance: {e}")

    # Get account liquidity
    try:
        liquidity = kinetic.get_account_liquidity()
        print(f"Account liquidity: {liquidity}")
    except Exception as e:
        print(f"Error getting account liquidity: {e}")

if __name__ == "__main__":
    main() 