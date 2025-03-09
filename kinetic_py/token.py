"""
Token-related functionality for the Kinetic SDK.
"""

from typing import Optional, Dict, Any
from web3 import Web3
from web3.contract import Contract
from eth_typing import ChecksumAddress, Address
from .constants import ERC20_ABI


class ERC20Token:
    """
    Class representing an ERC20 token.
    """
    
    def __init__(self, address: str, web3: Web3):
        """
        Initialize an ERC20 token.
        
        Args:
            address: Token address
            web3: Web3 instance
        """
        self.address = Web3.to_checksum_address(address)
        self.web3 = web3
        self.contract = self.web3.eth.contract(address=self.address, abi=ERC20_ABI)
        
        # Cache token properties
        self._name = None
        self._symbol = None
        self._decimals = None
        
    @property
    def name(self) -> str:
        """Get the token name."""
        if self._name is None:
            self._name = self.contract.functions.name().call()
        return self._name
    
    @property
    def symbol(self) -> str:
        """Get the token symbol."""
        if self._symbol is None:
            self._symbol = self.contract.functions.symbol().call()
        return self._symbol
    
    @property
    def decimals(self) -> int:
        """Get the token decimals."""
        if self._decimals is None:
            self._decimals = self.contract.functions.decimals().call()
        return self._decimals
    
    def balance_of(self, address: str) -> int:
        """
        Get the token balance of an address.
        
        Args:
            address: Address to check
            
        Returns:
            Token balance in wei
        """
        return self.contract.functions.balanceOf(Web3.to_checksum_address(address)).call()
    
    def allowance(self, owner: str, spender: str) -> int:
        """
        Get the allowance of a spender for an owner.
        
        Args:
            owner: Token owner
            spender: Token spender
            
        Returns:
            Allowance in wei
        """
        return self.contract.functions.allowance(
            Web3.to_checksum_address(owner),
            Web3.to_checksum_address(spender)
        ).call()
    
    def __repr__(self) -> str:
        return f"<ERC20Token {self.symbol} at {self.address}>" 