#!/usr/bin/env python3
"""
Script to lend WFLR token on Kinetic Money Market protocol
"""

# Load wallet details from .env file
from dotenv import load_dotenv
import os
import json
import sys
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

# Load environment variables from .env file
load_dotenv()

def lend_wflr(amount_wflr):
    """
    Lend WFLR tokens on Kinetic Money Market protocol
    
    Args:
        amount_wflr (float): Amount of WFLR to lend
        
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
    except Exception as e:
        print(f"Error getting account balance: {e}")
        print("Please check that your WALLET_ADDRESS is correct")
        return None

    # Contract addresses - using the kFLRETH address from the output
    kwflr_address = '0x40eE5dfe1D4a957cA8AC4DD4ADaf8A8fA76b1C16'  # kFLRETH address
    comptroller_address = '0x8041680Fb73E1Fe5F851e76233DCDfA0f2D2D7c8'  # Comptroller address from the output

    # ERC20 ABI (for WFLR/flrETH)
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
        }
    ]
    '''

    # CErc20 ABI (for kWFLR/kFLRETH) - Updated with more complete interface
    cerc20_abi = '''
    [
        {
            "constant": false,
            "inputs": [{"name": "mintAmount", "type": "uint256"}],
            "name": "mint",
            "outputs": [{"name": "", "type": "uint256"}],
            "payable": false,
            "stateMutability": "nonpayable",
            "type": "function"
        },
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
            "constant": true,
            "inputs": [],
            "name": "symbol",
            "outputs": [{"name": "", "type": "string"}],
            "payable": false,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": true,
            "inputs": [{"name": "owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "", "type": "uint256"}],
            "payable": false,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": true,
            "inputs": [],
            "name": "comptroller",
            "outputs": [{"name": "", "type": "address"}],
            "payable": false,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": true,
            "inputs": [],
            "name": "underlying",
            "outputs": [{"name": "", "type": "address"}],
            "payable": false,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": true,
            "inputs": [],
            "name": "exchangeRateStored",
            "outputs": [{"name": "", "type": "uint256"}],
            "payable": false,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": false,
            "inputs": [],
            "name": "accrueInterest",
            "outputs": [{"name": "", "type": "uint256"}],
            "payable": false,
            "stateMutability": "nonpayable",
            "type": "function"
        }
    ]
    '''

    # Comptroller ABI (updated with more accurate interface for Kinetic/Compound)
    comptroller_abi = '''
    [
        {
            "constant": true,
            "inputs": [{"name": "", "type": "address"}],
            "name": "markets",
            "outputs": [
                {"name": "isListed", "type": "bool"},
                {"name": "collateralFactorMantissa", "type": "uint256"},
                {"name": "isComped", "type": "bool"}
            ],
            "payable": false,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": true,
            "inputs": [{"name": "", "type": "address"}],
            "name": "mintGuardianPaused",
            "outputs": [{"name": "", "type": "bool"}],
            "payable": false,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": false,
            "inputs": [{"name": "cToken", "type": "address"}, {"name": "minter", "type": "address"}, {"name": "mintAmount", "type": "uint256"}],
            "name": "mintAllowed",
            "outputs": [{"name": "", "type": "uint256"}],
            "payable": false,
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "constant": true,
            "inputs": [],
            "name": "getAllMarkets",
            "outputs": [{"name": "", "type": "address[]"}],
            "payable": false,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": true,
            "inputs": [{"name": "account", "type": "address"}],
            "name": "getAccountLiquidity",
            "outputs": [
                {"name": "", "type": "uint256"},
                {"name": "", "type": "uint256"},
                {"name": "", "type": "uint256"}
            ],
            "payable": false,
            "stateMutability": "view",
            "type": "function"
        }
    ]
    '''

    # Create kWFLR contract instance first to get the underlying token address
    kwflr_contract = web3.eth.contract(address=kwflr_address, abi=cerc20_abi)
    
    # Try to get the comptroller address from the kWFLR contract
    try:
        contract_comptroller_address = kwflr_contract.functions.comptroller().call()
        print(f"Comptroller address from kWFLR contract: {contract_comptroller_address}")
        comptroller_address = contract_comptroller_address
    except Exception as e:
        print(f"Could not get comptroller address from kWFLR contract: {e}")
        print(f"Using default comptroller address: {comptroller_address}")
    
    # Create comptroller contract instance
    comptroller_contract = web3.eth.contract(address=comptroller_address, abi=comptroller_abi)

    # Get the underlying token address for kWFLR - this is critical
    try:
        underlying_address = kwflr_contract.functions.underlying().call()
        print(f"Underlying token address for kWFLR: {underlying_address}")
        # Use the correct underlying token address from the contract
        wflr_address = underlying_address
    except Exception as e:
        print(f"Error getting underlying token address: {e}")
        return None
    
    # Create the underlying token contract with the correct address
    wflr_contract = web3.eth.contract(address=wflr_address, abi=erc20_abi)
    
    # Amount of WFLR to lend (in wei, 1 WFLR = 10^18 wei)
    amount_to_lend = web3.to_wei(amount_wflr, 'ether')
    
    print(f"Preparing to lend {amount_wflr} tokens to the Kinetic protocol...")

    try:
        # Try to get the exchange rate
        try:
            exchange_rate = kwflr_contract.functions.exchangeRateStored().call()
            print(f"Current exchange rate: {web3.from_wei(exchange_rate, 'ether')} tokens per kToken")
        except Exception as e:
            print(f"Error getting exchange rate: {e}")
        
        # Try to get all markets from the comptroller
        try:
            all_markets = comptroller_contract.functions.getAllMarkets().call()
            print(f"All markets in Comptroller: {all_markets}")
            
            if kwflr_address in all_markets:
                print(f"kToken market is listed in the Comptroller's getAllMarkets()")
            else:
                print(f"Warning: kToken market is NOT listed in the Comptroller's getAllMarkets()!")
                print("This might cause the mint transaction to fail.")
                return None
        except Exception as e:
            print(f"Error getting all markets: {e}")
        
        # Check if minting is paused
        try:
            is_mint_paused = comptroller_contract.functions.mintGuardianPaused(kwflr_address).call()
            print(f"Is minting paused: {is_mint_paused}")
            
            if is_mint_paused:
                print("Warning: Minting is currently paused for this market!")
                print("This will cause the mint transaction to fail.")
                return None
        except Exception as e:
            print(f"Error checking if minting is paused: {e}")
        
        # Try to get contract names and symbols
        try:
            wflr_name = wflr_contract.functions.name().call()
            wflr_symbol = wflr_contract.functions.symbol().call()
            print(f"Underlying token name: {wflr_name}")
            print(f"Underlying token symbol: {wflr_symbol}")
            
            kwflr_name = kwflr_contract.functions.name().call()
            kwflr_symbol = kwflr_contract.functions.symbol().call()
            print(f"kToken contract name: {kwflr_name}")
            print(f"kToken contract symbol: {kwflr_symbol}")
        except Exception as e:
            print(f"Could not get contract name/symbol: {e}")
        
        # Check token balance
        try:
            wflr_balance = wflr_contract.functions.balanceOf(WALLET_ADDRESS).call()
            print(f"Token balance: {web3.from_wei(wflr_balance, 'ether')} {wflr_symbol}")
            
            if wflr_balance < amount_to_lend:
                print(f"Not enough token balance. You need at least {amount_wflr} {wflr_symbol}.")
                return None
        except Exception as e:
            print(f"Could not get token balance: {e}")
            return None
            
        # Check initial kToken balance
        try:
            initial_kwflr_balance = kwflr_contract.functions.balanceOf(WALLET_ADDRESS).call()
            print(f"Initial kToken balance: {web3.from_wei(initial_kwflr_balance, 'ether')} {kwflr_symbol}")
        except Exception as e:
            print(f"Could not get initial kToken balance: {e}")
            initial_kwflr_balance = 0

        # Step 1: Approve kToken contract to spend tokens
        print(f"Approving kToken contract to spend {amount_wflr} {wflr_symbol}...")
        
        # Get current gas price
        gas_price = web3.eth.gas_price
        print(f"Current gas price: {web3.from_wei(gas_price, 'gwei')} gwei")
        
        # Use a slightly higher gas price to ensure transaction goes through
        suggested_gas_price = int(gas_price * 1.1)
        print(f"Suggested gas price: {web3.from_wei(suggested_gas_price, 'gwei')} gwei")
        
        # Build approval transaction
        approve_tx = wflr_contract.functions.approve(kwflr_address, amount_to_lend).build_transaction({
            'from': WALLET_ADDRESS,
            'gas': 200000,
            'gasPrice': suggested_gas_price,
            'nonce': web3.eth.get_transaction_count(WALLET_ADDRESS),
        })
        
        # Sign transaction
        signed_approve_tx = web3.eth.account.sign_transaction(approve_tx, private_key=PRIVATE_KEY)

        # Send transaction
        print(f"Sending approval transaction...")
        approve_tx_hash = web3.eth.send_raw_transaction(signed_approve_tx.raw_transaction)
        print(f"Approval transaction sent with hash: {approve_tx_hash.hex()}")

        # Wait for transaction receipt
        print("Waiting for approval transaction confirmation...")
        approve_tx_receipt = web3.eth.wait_for_transaction_receipt(approve_tx_hash)
        
        if approve_tx_receipt.status != 1:
            print("Approval transaction failed!")
            return None
            
        print("Approval transaction successful!")
        
        # Check allowance after approval
        try:
            allowance = wflr_contract.functions.allowance(WALLET_ADDRESS, kwflr_address).call()
            print(f"Current allowance for kToken contract: {web3.from_wei(allowance, 'ether')} {wflr_symbol}")
            if allowance < amount_to_lend:
                print(f"Warning: Allowance ({web3.from_wei(allowance, 'ether')} {wflr_symbol}) is less than the amount to lend ({amount_wflr} {wflr_symbol})")
                return None
        except Exception as e:
            print(f"Error checking allowance: {e}")
        
        # Step 2: Mint kToken tokens (lend tokens)
        print(f"Lending {amount_wflr} {wflr_symbol} to get {kwflr_symbol} tokens...")
        
        # Get current nonce
        current_nonce = web3.eth.get_transaction_count(WALLET_ADDRESS)
        print(f"Current nonce: {current_nonce}")
        
        # Try to estimate gas with a higher gas limit
        try:
            print("Attempting to estimate gas with higher limit...")
            estimated_gas = kwflr_contract.functions.mint(amount_to_lend).estimate_gas({
                'from': WALLET_ADDRESS,
                'gasPrice': suggested_gas_price,
                'nonce': current_nonce,
                'gas': 1000000  # Use a higher gas limit for estimation
            })
            print(f"Estimated gas for mint transaction: {estimated_gas}")
            # Add 20% buffer to estimated gas
            gas_limit = int(estimated_gas * 1.2)
            print(f"Using gas limit with buffer: {gas_limit}")
        except Exception as e:
            print(f"Error estimating gas: {e}")
            print("Using default gas limit of 500000")
            gas_limit = 500000
        
        # Build mint transaction
        mint_tx = kwflr_contract.functions.mint(amount_to_lend).build_transaction({
            'from': WALLET_ADDRESS,
            'gas': gas_limit,
            'gasPrice': suggested_gas_price,
            'nonce': current_nonce,
        })
        
        # Sign transaction
        signed_mint_tx = web3.eth.account.sign_transaction(mint_tx, private_key=PRIVATE_KEY)

        # Send transaction
        print(f"Sending mint transaction...")
        mint_tx_hash = web3.eth.send_raw_transaction(signed_mint_tx.raw_transaction)
        print(f"Mint transaction sent with hash: {mint_tx_hash.hex()}")

        # Wait for transaction receipt
        print("Waiting for mint transaction confirmation...")
        mint_tx_receipt = web3.eth.wait_for_transaction_receipt(mint_tx_hash)
        
        if mint_tx_receipt.status == 1:
            print("Mint transaction successful!")
            
            # Check new kToken balance
            try:
                new_kwflr_balance = kwflr_contract.functions.balanceOf(WALLET_ADDRESS).call()
                print(f"New kToken balance: {web3.from_wei(new_kwflr_balance, 'ether')} {kwflr_symbol}")
                print(f"Change: {web3.from_wei(new_kwflr_balance - initial_kwflr_balance, 'ether')} {kwflr_symbol}")
            except Exception as e:
                print(f"Could not get new kToken balance: {e}")
                
            return mint_tx_receipt
        else:
            print("Mint transaction failed!")
            
            # Try to get more information about the failure
            print(f"Transaction receipt details:")
            print(f"  Gas used: {mint_tx_receipt.gasUsed} / {gas_limit} ({mint_tx_receipt.gasUsed / gas_limit * 100:.2f}%)")
            print(f"  Block number: {mint_tx_receipt.blockNumber}")
            print(f"  Transaction index: {mint_tx_receipt.transactionIndex}")
            
            # Try to get transaction trace or revert reason
            try:
                # Try to get the revert reason
                tx = web3.eth.get_transaction(mint_tx_hash)
                replay_tx = {
                    'to': tx['to'],
                    'from': tx['from'],
                    'data': tx['input'],
                    'gas': tx['gas'],
                    'gasPrice': tx['gasPrice'],
                    'value': tx['value']
                }
                
                try:
                    # Try to call the function with the same parameters to get the revert reason
                    print("Attempting to replay transaction to get revert reason...")
                    web3.eth.call(replay_tx, mint_tx_receipt.blockNumber)
                except Exception as call_exception:
                    error_message = str(call_exception)
                    print(f"Revert reason: {error_message}")
                    
                    # Common error codes and their meanings for Compound/Kinetic
                    error_codes = {
                        "0": "NO_ERROR",
                        "1": "UNAUTHORIZED",
                        "2": "COMPTROLLER_MISMATCH",
                        "3": "INSUFFICIENT_LIQUIDITY",
                        "4": "INSUFFICIENT_BALANCE",
                        "5": "COMPTROLLER_REJECTION",
                        "6": "COMPTROLLER_CALCULATION_ERROR",
                        "7": "INTEREST_RATE_MODEL_ERROR",
                        "8": "INVALID_ACCOUNT_PAIR",
                        "9": "INVALID_CLOSE_AMOUNT_REQUESTED",
                        "10": "INVALID_COLLATERAL_FACTOR",
                        "11": "MATH_ERROR",
                        "12": "MARKET_NOT_FRESH",
                        "13": "MARKET_NOT_LISTED",
                        "14": "TOKEN_INSUFFICIENT_ALLOWANCE",
                        "15": "TOKEN_INSUFFICIENT_BALANCE",
                        "16": "TOKEN_INSUFFICIENT_CASH",
                        "17": "TOKEN_TRANSFER_IN_FAILED",
                        "18": "TOKEN_TRANSFER_OUT_FAILED"
                    }
                    
                    # Try to extract error code from the error message
                    import re
                    error_code_match = re.search(r'Error\((\d+)\)', error_message)
                    if error_code_match:
                        error_code = error_code_match.group(1)
                        error_name = error_codes.get(error_code, "UNKNOWN_ERROR")
                        print(f"Error code: {error_code} ({error_name})")
                        
                        # Provide more specific guidance based on the error
                        if error_code == "5":
                            print("This suggests the Comptroller rejected the mint operation.")
                            print("Possible reasons: market not listed, mint paused, or other comptroller restrictions.")
                        elif error_code == "14":
                            print("This suggests the kToken contract doesn't have enough allowance to transfer your tokens.")
                            print("Try increasing the allowance or checking if the approval transaction was successful.")
                        elif error_code == "15":
                            print("This suggests you don't have enough token balance for the mint operation.")
                            print("Check your token balance and try with a smaller amount.")
                        elif error_code == "16":
                            print("This suggests the protocol doesn't have enough liquidity to fulfill your request.")
                            print("Try with a smaller amount or try again later.")
                        elif error_code == "17":
                            print("This suggests the transfer of tokens into the protocol failed.")
                            print("Check if your tokens are locked or if there's an issue with the token contract.")
            except Exception as trace_exception:
                print(f"Could not get transaction trace: {trace_exception}")
            
            return None

    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    # Lend 0.1 tokens
    lend_wflr(0.00001) 