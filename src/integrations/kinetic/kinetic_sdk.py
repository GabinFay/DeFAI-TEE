"""
Kinetic SDK - A Python SDK for interacting with the Kinetic protocol (a Compound v2 fork) on Flare.

This SDK is modeled after the compound-js SDK but implemented in Python.
"""

import os
import json
import time
import re
import functools
from typing import Dict, List, Optional, Tuple, Union, Any, Callable

from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3.types import TxReceipt, Wei
from web3.contract import Contract
from eth_account.account import Account
from eth_typing import ChecksumAddress, Address
from hexbytes import HexBytes

from .constants import (
    KINETIC_ADDRESSES,
    KINETIC_TOKENS,
    TOKEN_DECIMALS,
    ERC20_ABI,
    CERC20_ABI,
    COMPTROLLER_ABI,
    ERROR_CODES,
)

# Turn off Web3 warnings
import logging
logging.getLogger('web3').setLevel(logging.ERROR)

# Type aliases
AddressLike = Union[Address, ChecksumAddress, str]
TxParams = Dict[str, Any]


class KineticSDK:
    """
    A Python SDK for interacting with the Kinetic protocol (a Compound v2 fork) on Flare.
    Modeled after the compound-js SDK.
    """

    address: AddressLike
    web3: Web3
    account: Optional[Account]
    wallet_address: Optional[AddressLike]
    
    # Contract instances
    comptroller: Contract
    token_contracts: Dict[str, Contract]
    ktoken_contracts: Dict[str, Contract]

    def __init__(
        self,
        provider: Union[str, Web3] = None,
        options: Dict[str, Any] = None,
    ):
        """
        Initialize the Kinetic SDK.

        Args:
            provider: A Web3 provider instance, a provider URL string, or a network name
            options: Optional configuration options including privateKey or mnemonic
        """
        if options is None:
            options = {}

        # Initialize Web3 provider
        if isinstance(provider, Web3):
            self.web3 = provider
        elif isinstance(provider, str):
            if provider.startswith('http') or provider.startswith('ws'):
                self.web3 = Web3(Web3.HTTPProvider(provider))
            else:
                # Default to Flare mainnet if no provider is specified
                self.web3 = Web3(Web3.HTTPProvider('https://flare-api.flare.network/ext/C/rpc'))
        else:
            # Default to Flare mainnet if no provider is specified
            self.web3 = Web3(Web3.HTTPProvider('https://flare-api.flare.network/ext/C/rpc'))

        # Add middleware for POA networks
        self.web3.middleware_onion.inject(geth_poa_middleware, layer=0)

        # Set up account from private key or mnemonic if provided
        self.account = None
        if 'privateKey' in options:
            self.account = Account.from_key(options['privateKey'])
            self.wallet_address = self.account.address
        elif 'mnemonic' in options:
            # Create account from mnemonic
            Account.enable_unaudited_hdwallet_features()
            self.account = Account.from_mnemonic(options['mnemonic'])
            self.wallet_address = self.account.address
        else:
            self.wallet_address = options.get('walletAddress')

        # Check if connected to the network
        if not self.web3.is_connected():
            raise ConnectionError("Failed to connect to the Flare network")

        # Initialize contract instances
        self.comptroller = self.web3.eth.contract(
            address=KINETIC_ADDRESSES["Unitroller"],
            abi=COMPTROLLER_ABI,
        )

        # Create token contract instances
        self.token_contracts = {}
        self.ktoken_contracts = {}
        self._initialize_contracts()

        # Create namespaces for different functionality groups
        self.cToken = self._create_ctoken_namespace()
        self.comptroller_methods = self._create_comptroller_namespace()
        self.eth = self._create_eth_namespace()
        self.util = self._create_util_namespace()

    def _initialize_contracts(self) -> None:
        """Initialize token and kToken contract instances."""
        # Initialize token contracts
        for token_name, token_address in KINETIC_TOKENS.items():
            if token_name.startswith('k'):
                # This is a kToken
                self.ktoken_contracts[token_name] = self.web3.eth.contract(
                    address=token_address,
                    abi=CERC20_ABI,
                )
            else:
                # This is a regular token
                self.token_contracts[token_name] = self.web3.eth.contract(
                    address=token_address,
                    abi=ERC20_ABI,
                )

    def _get_wallet_address(self) -> str:
        """
        Get the wallet address.

        Returns:
            str: The wallet address
        """
        if self.wallet_address:
            return self.wallet_address
        elif hasattr(self.web3.eth, "accounts") and self.web3.eth.accounts:
            return self.web3.eth.accounts[0]
        else:
            raise ValueError("No wallet address available. Please provide a wallet address or connect to a wallet.")

    def _get_token_decimals(self, token_name: str) -> int:
        """
        Get the number of decimals for a token.

        Args:
            token_name: The name of the token

        Returns:
            int: The number of decimals for the token
        """
        if token_name in TOKEN_DECIMALS:
            return TOKEN_DECIMALS[token_name]
        
        # Try to get decimals from the token contract
        if token_name in self.token_contracts:
            try:
                return self.token_contracts[token_name].functions.decimals().call()
            except Exception:
                pass
        
        # Default to 18 decimals
        return 18

    def _to_wei(self, amount: Union[int, float], token_name: str) -> int:
        """
        Convert an amount to wei (the smallest unit) based on the token's decimals.

        Args:
            amount: The amount to convert
            token_name: The name of the token

        Returns:
            int: The amount in wei
        """
        decimals = self._get_token_decimals(token_name)
        return int(amount * (10 ** decimals))

    def _from_wei(self, amount: int, token_name: str) -> float:
        """
        Convert an amount from wei (the smallest unit) to a human-readable format.

        Args:
            amount: The amount in wei
            token_name: The name of the token

        Returns:
            float: The human-readable amount
        """
        decimals = self._get_token_decimals(token_name)
        return amount / (10 ** decimals)

    def _get_ktoken_for_token(self, token_name: str) -> str:
        """
        Get the kToken name for a given token.

        Args:
            token_name: The name of the token

        Returns:
            str: The name of the corresponding kToken
        """
        # If it's already a kToken, return it
        if token_name.startswith('k'):
            return token_name
        
        # Otherwise, prepend 'k' to the token name
        ktoken_name = f"k{token_name}"
        
        # Check if the kToken exists
        if ktoken_name in KINETIC_TOKENS:
            return ktoken_name
        
        # If not found, raise an error
        raise ValueError(f"No kToken found for {token_name}")

    def _get_token_for_ktoken(self, ktoken_name: str) -> str:
        """
        Get the underlying token name for a given kToken.

        Args:
            ktoken_name: The name of the kToken

        Returns:
            str: The name of the underlying token
        """
        # If it's not a kToken, return it
        if not ktoken_name.startswith('k'):
            return ktoken_name
        
        # Otherwise, remove the 'k' prefix
        token_name = ktoken_name[1:]
        
        # Check if the token exists
        if token_name in KINETIC_TOKENS:
            return token_name
        
        # If not found, raise an error
        raise ValueError(f"No underlying token found for {ktoken_name}")

    def _get_error_message(self, error_code: int) -> str:
        """
        Get the error message for a given error code.

        Args:
            error_code: The error code

        Returns:
            str: The error message
        """
        if error_code in ERROR_CODES:
            return ERROR_CODES[error_code]
        return f"Unknown error code: {error_code}"

    def _parse_error(self, exception: Exception) -> str:
        """
        Parse an exception to extract the error message.

        Args:
            exception: The exception to parse

        Returns:
            str: The parsed error message
        """
        error_str = str(exception)
        
        # Try to extract error code
        error_code_match = re.search(r'Error code: (\d+)', error_str)
        if error_code_match:
            error_code = int(error_code_match.group(1))
            return self._get_error_message(error_code)
        
        return error_str

    def _create_ctoken_namespace(self) -> Dict[str, Callable]:
        """
        Create the cToken namespace with methods for interacting with cTokens.

        Returns:
            Dict[str, Callable]: A dictionary of cToken methods
        """
        return {
            'supply': self.supply,
            'redeem': self.redeem,
            'borrow': self.borrow,
            'repay_borrow': self.repay_borrow,
            'get_balance': self.get_ktoken_balance,
            'get_underlying_balance': self.get_account_balance,
            'get_exchange_rate': self.get_exchange_rate,
        }

    def _create_comptroller_namespace(self) -> Dict[str, Callable]:
        """
        Create the comptroller namespace with methods for interacting with the comptroller.

        Returns:
            Dict[str, Callable]: A dictionary of comptroller methods
        """
        return {
            'enter_markets': self.enter_markets,
            'exit_market': self.exit_market,
            'get_account_liquidity': self.get_account_liquidity,
            'get_all_markets': self.get_all_markets,
        }

    def _create_eth_namespace(self) -> Dict[str, Callable]:
        """
        Create the eth namespace with methods for interacting with Ethereum.

        Returns:
            Dict[str, Callable]: A dictionary of eth methods
        """
        return {
            'get_balance': lambda address=None: self.web3.eth.get_balance(address or self._get_wallet_address()),
            'send_transaction': lambda tx: self.web3.eth.send_transaction(tx),
            'get_transaction_receipt': lambda tx_hash: self.web3.eth.get_transaction_receipt(tx_hash),
            'get_block_number': lambda: self.web3.eth.block_number,
        }

    def _create_util_namespace(self) -> Dict[str, Callable]:
        """
        Create the util namespace with utility methods.

        Returns:
            Dict[str, Callable]: A dictionary of utility methods
        """
        return {
            'to_wei': self._to_wei,
            'from_wei': self._from_wei,
            'get_token_decimals': self._get_token_decimals,
            'get_ktoken_for_token': self._get_ktoken_for_token,
            'get_token_for_ktoken': self._get_token_for_ktoken,
        }

    def get_account_balance(self, token_name: str, address: Optional[str] = None) -> float:
        """
        Get the balance of a token for an account.

        Args:
            token_name: The name of the token
            address: The address to check the balance for (defaults to the wallet address)

        Returns:
            float: The token balance
        """
        address = address or self._get_wallet_address()
        
        if token_name not in self.token_contracts:
            raise ValueError(f"Unknown token: {token_name}")
        
        token_contract = self.token_contracts[token_name]
        balance_wei = token_contract.functions.balanceOf(address).call()
        
        return self._from_wei(balance_wei, token_name)

    def get_ktoken_balance(self, ktoken_name: str, address: Optional[str] = None) -> float:
        """
        Get the balance of a kToken for an account.

        Args:
            ktoken_name: The name of the kToken
            address: The address to check the balance for (defaults to the wallet address)

        Returns:
            float: The kToken balance
        """
        address = address or self._get_wallet_address()
        
        if ktoken_name not in self.ktoken_contracts:
            raise ValueError(f"Unknown kToken: {ktoken_name}")
        
        ktoken_contract = self.ktoken_contracts[ktoken_name]
        balance_wei = ktoken_contract.functions.balanceOf(address).call()
        
        return self._from_wei(balance_wei, ktoken_name)

    def get_exchange_rate(self, token_name: str) -> float:
        """
        Get the exchange rate between a token and its kToken.

        Args:
            token_name: The name of the token

        Returns:
            float: The exchange rate (how much of the underlying token 1 kToken is worth)
        """
        ktoken_name = self._get_ktoken_for_token(token_name)
        ktoken_contract = self.ktoken_contracts[ktoken_name]
        
        # Call exchangeRateStored() to get the exchange rate
        exchange_rate_mantissa = ktoken_contract.functions.exchangeRateStored().call()
        
        # The exchange rate is scaled by 1e18
        return exchange_rate_mantissa / 1e18

    def get_account_liquidity(self, address: Optional[str] = None) -> Dict[str, float]:
        """
        Get the account liquidity in the protocol.

        Args:
            address: The address to check the liquidity for (defaults to the wallet address)

        Returns:
            Dict[str, float]: A dictionary with liquidity information
        """
        address = address or self._get_wallet_address()
        
        # Call getAccountLiquidity() to get the liquidity
        error, liquidity, shortfall = self.comptroller.functions.getAccountLiquidity(address).call()
        
        if error != 0:
            raise ValueError(f"Error getting account liquidity: {self._get_error_message(error)}")
        
        return {
            'error': error,
            'liquidity': liquidity / 1e18,  # Convert to ETH units
            'shortfall': shortfall / 1e18,  # Convert to ETH units
        }

    def get_all_markets(self) -> List[str]:
        """
        Get all markets (kTokens) in the protocol.

        Returns:
            List[str]: A list of kToken addresses
        """
        return self.comptroller.functions.getAllMarkets().call()

    def enter_markets(self, token_names: List[str]) -> List[int]:
        """
        Enter markets (enable tokens as collateral).

        Args:
            token_names: A list of token names to enter

        Returns:
            List[int]: A list of error codes (0 means success)
        """
        if not self.account:
            raise ValueError("Private key required for this operation")
        
        # Convert token names to kToken addresses
        ktoken_addresses = []
        for token_name in token_names:
            ktoken_name = self._get_ktoken_for_token(token_name)
            ktoken_addresses.append(KINETIC_TOKENS[ktoken_name])
        
        # Build the transaction
        tx = self.comptroller.functions.enterMarkets(ktoken_addresses).build_transaction({
            'from': self._get_wallet_address(),
            'gas': 200000,
            'gasPrice': self.web3.eth.gas_price,
            'nonce': self.web3.eth.get_transaction_count(self._get_wallet_address()),
        })
        
        # Sign and send the transaction
        signed_tx = self.account.sign_transaction(tx)
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        # Wait for the transaction to be mined
        receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt.status == 0:
            raise ValueError("Transaction failed")
        
        # Get the result from the transaction logs
        # In a real implementation, you would parse the logs to get the actual error codes
        # For simplicity, we'll just return a list of zeros (success)
        return [0] * len(token_names)

    def exit_market(self, token_name: str) -> int:
        """
        Exit a market (disable a token as collateral).

        Args:
            token_name: The name of the token to exit

        Returns:
            int: The error code (0 means success)
        """
        if not self.account:
            raise ValueError("Private key required for this operation")
        
        # Convert token name to kToken address
        ktoken_name = self._get_ktoken_for_token(token_name)
        ktoken_address = KINETIC_TOKENS[ktoken_name]
        
        # Build the transaction
        tx = self.comptroller.functions.exitMarket(ktoken_address).build_transaction({
            'from': self._get_wallet_address(),
            'gas': 200000,
            'gasPrice': self.web3.eth.gas_price,
            'nonce': self.web3.eth.get_transaction_count(self._get_wallet_address()),
        })
        
        # Sign and send the transaction
        signed_tx = self.account.sign_transaction(tx)
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        # Wait for the transaction to be mined
        receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt.status == 0:
            raise ValueError("Transaction failed")
        
        # In a real implementation, you would parse the logs to get the actual error code
        # For simplicity, we'll just return 0 (success)
        return 0

    def supply(self, token_name: str, amount: Union[int, float], no_approve: bool = False) -> str:
        """
        Supply tokens to the Kinetic protocol.

        Args:
            token_name: The name of the token to supply
            amount: The amount to supply
            no_approve: Whether to skip the approval step

        Returns:
            str: The transaction hash
        """
        if not self.account:
            raise ValueError("Private key required for this operation")
        
        # Get the token and kToken contracts
        if token_name not in self.token_contracts:
            raise ValueError(f"Unknown token: {token_name}")
        
        token_contract = self.token_contracts[token_name]
        ktoken_name = self._get_ktoken_for_token(token_name)
        ktoken_contract = self.ktoken_contracts[ktoken_name]
        
        # Convert amount to wei
        amount_wei = self._to_wei(amount, token_name)
        
        # Check if we need to approve the token
        if not no_approve:
            # Check current allowance
            allowance = token_contract.functions.allowance(
                self._get_wallet_address(),
                KINETIC_TOKENS[ktoken_name]
            ).call()
            
            if allowance < amount_wei:
                # Approve the token
                approve_tx = token_contract.functions.approve(
                    KINETIC_TOKENS[ktoken_name],
                    amount_wei
                ).build_transaction({
                    'from': self._get_wallet_address(),
                    'gas': 100000,
                    'gasPrice': self.web3.eth.gas_price,
                    'nonce': self.web3.eth.get_transaction_count(self._get_wallet_address()),
                })
                
                # Sign and send the approval transaction
                signed_approve_tx = self.account.sign_transaction(approve_tx)
                approve_tx_hash = self.web3.eth.send_raw_transaction(signed_approve_tx.rawTransaction)
                
                # Wait for the approval transaction to be mined
                approve_receipt = self.web3.eth.wait_for_transaction_receipt(approve_tx_hash)
                
                if approve_receipt.status == 0:
                    raise ValueError("Approval transaction failed")
        
        try:
            # Build the mint transaction with the full amount
            mint_tx = ktoken_contract.functions.mint(amount_wei).build_transaction({
                'from': self._get_wallet_address(),
                'gas': 500000,  # Increased gas limit
                'gasPrice': self.web3.eth.gas_price,
                'nonce': self.web3.eth.get_transaction_count(self._get_wallet_address()),
            })
            
            # Sign and send the mint transaction
            signed_mint_tx = self.account.sign_transaction(mint_tx)
            mint_tx_hash = self.web3.eth.send_raw_transaction(signed_mint_tx.rawTransaction)
            
            # Wait for the mint transaction to be mined
            mint_receipt = self.web3.eth.wait_for_transaction_receipt(mint_tx_hash)
            
            if mint_receipt.status == 0:
                # Try to get more detailed error information
                error_message = self._parse_error(Exception("Transaction status 0"))
                raise ValueError(f"Mint transaction failed: {error_message}")
            
            return mint_tx_hash.hex()
        except Exception as e:
            # Try to parse the error to get more information
            error_message = self._parse_error(e)
            raise ValueError(f"Mint transaction failed: {error_message}")

    def redeem(self, token_name: str, amount: Union[int, float], redeem_type: str = "token") -> str:
        """
        Redeem tokens from the Kinetic protocol.

        Args:
            token_name: The name of the token to redeem
            amount: The amount to redeem
            redeem_type: The type of redemption ('token' for underlying tokens, 'ktoken' for kTokens)

        Returns:
            str: The transaction hash
        """
        if not self.account:
            raise ValueError("Private key required for this operation")
        
        # Get the kToken contract
        ktoken_name = self._get_ktoken_for_token(token_name)
        ktoken_contract = self.ktoken_contracts[ktoken_name]
        
        # Convert amount to wei
        if redeem_type == "token":
            # Redeeming underlying tokens
            amount_wei = self._to_wei(amount, token_name)
            
            # Build the redeemUnderlying transaction
            redeem_tx = ktoken_contract.functions.redeemUnderlying(amount_wei).build_transaction({
                'from': self._get_wallet_address(),
                'gas': 300000,
                'gasPrice': self.web3.eth.gas_price,
                'nonce': self.web3.eth.get_transaction_count(self._get_wallet_address()),
            })
        else:
            # Redeeming kTokens
            amount_wei = self._to_wei(amount, ktoken_name)
            
            # Build the redeem transaction
            redeem_tx = ktoken_contract.functions.redeem(amount_wei).build_transaction({
                'from': self._get_wallet_address(),
                'gas': 300000,
                'gasPrice': self.web3.eth.gas_price,
                'nonce': self.web3.eth.get_transaction_count(self._get_wallet_address()),
            })
        
        # Sign and send the redeem transaction
        signed_redeem_tx = self.account.sign_transaction(redeem_tx)
        redeem_tx_hash = self.web3.eth.send_raw_transaction(signed_redeem_tx.rawTransaction)
        
        # Wait for the redeem transaction to be mined
        redeem_receipt = self.web3.eth.wait_for_transaction_receipt(redeem_tx_hash)
        
        if redeem_receipt.status == 0:
            raise ValueError("Redeem transaction failed")
        
        return redeem_tx_hash.hex()

    def borrow(self, token_name: str, amount: Union[int, float]) -> str:
        """
        Borrow tokens from the Kinetic protocol.

        Args:
            token_name: The name of the token to borrow
            amount: The amount to borrow

        Returns:
            str: The transaction hash
        """
        if not self.account:
            raise ValueError("Private key required for this operation")
        
        # Get the kToken contract
        ktoken_name = self._get_ktoken_for_token(token_name)
        ktoken_contract = self.ktoken_contracts[ktoken_name]
        
        # Convert amount to wei
        amount_wei = self._to_wei(amount, token_name)
        
        # Build the borrow transaction
        borrow_tx = ktoken_contract.functions.borrow(amount_wei).build_transaction({
            'from': self._get_wallet_address(),
            'gas': 300000,
            'gasPrice': self.web3.eth.gas_price,
            'nonce': self.web3.eth.get_transaction_count(self._get_wallet_address()),
        })
        
        # Sign and send the borrow transaction
        signed_borrow_tx = self.account.sign_transaction(borrow_tx)
        borrow_tx_hash = self.web3.eth.send_raw_transaction(signed_borrow_tx.rawTransaction)
        
        # Wait for the borrow transaction to be mined
        borrow_receipt = self.web3.eth.wait_for_transaction_receipt(borrow_tx_hash)
        
        if borrow_receipt.status == 0:
            raise ValueError("Borrow transaction failed")
        
        return borrow_tx_hash.hex()

    def repay_borrow(self, token_name: str, amount: Union[int, float], borrower: Optional[str] = None, no_approve: bool = False) -> str:
        """
        Repay a borrow from the Kinetic protocol.

        Args:
            token_name: The name of the token to repay
            amount: The amount to repay
            borrower: The address of the borrower (defaults to the wallet address)
            no_approve: Whether to skip the approval step

        Returns:
            str: The transaction hash
        """
        if not self.account:
            raise ValueError("Private key required for this operation")
        
        # Get the token and kToken contracts
        if token_name not in self.token_contracts:
            raise ValueError(f"Unknown token: {token_name}")
        
        token_contract = self.token_contracts[token_name]
        ktoken_name = self._get_ktoken_for_token(token_name)
        ktoken_contract = self.ktoken_contracts[ktoken_name]
        
        # Convert amount to wei
        amount_wei = self._to_wei(amount, token_name)
        
        # Set borrower address
        borrower = borrower or self._get_wallet_address()
        
        # Check if we need to approve the token
        if not no_approve:
            # Check current allowance
            allowance = token_contract.functions.allowance(
                self._get_wallet_address(),
                KINETIC_TOKENS[ktoken_name]
            ).call()
            
            if allowance < amount_wei:
                # Approve the token
                approve_tx = token_contract.functions.approve(
                    KINETIC_TOKENS[ktoken_name],
                    amount_wei
                ).build_transaction({
                    'from': self._get_wallet_address(),
                    'gas': 100000,
                    'gasPrice': self.web3.eth.gas_price,
                    'nonce': self.web3.eth.get_transaction_count(self._get_wallet_address()),
                })
                
                # Sign and send the approval transaction
                signed_approve_tx = self.account.sign_transaction(approve_tx)
                approve_tx_hash = self.web3.eth.send_raw_transaction(signed_approve_tx.rawTransaction)
                
                # Wait for the approval transaction to be mined
                approve_receipt = self.web3.eth.wait_for_transaction_receipt(approve_tx_hash)
                
                if approve_receipt.status == 0:
                    raise ValueError("Approval transaction failed")
        
        # Build the repayBorrow transaction
        if borrower == self._get_wallet_address():
            # Repaying own borrow
            repay_tx = ktoken_contract.functions.repayBorrow(amount_wei).build_transaction({
                'from': self._get_wallet_address(),
                'gas': 300000,
                'gasPrice': self.web3.eth.gas_price,
                'nonce': self.web3.eth.get_transaction_count(self._get_wallet_address()),
            })
        else:
            # Repaying someone else's borrow
            repay_tx = ktoken_contract.functions.repayBorrowBehalf(borrower, amount_wei).build_transaction({
                'from': self._get_wallet_address(),
                'gas': 300000,
                'gasPrice': self.web3.eth.gas_price,
                'nonce': self.web3.eth.get_transaction_count(self._get_wallet_address()),
            })
        
        # Sign and send the repay transaction
        signed_repay_tx = self.account.sign_transaction(repay_tx)
        repay_tx_hash = self.web3.eth.send_raw_transaction(signed_repay_tx.rawTransaction)
        
        # Wait for the repay transaction to be mined
        repay_receipt = self.web3.eth.wait_for_transaction_receipt(repay_tx_hash)
        
        if repay_receipt.status == 0:
            raise ValueError("Repay transaction failed")
        
        return repay_tx_hash.hex() 