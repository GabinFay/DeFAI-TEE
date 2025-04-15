"""
Main tools module for Flare Bot.
This file re-exports all the necessary functions and constants from the tools package.
"""

# Import constants from the tools package
from tools.constants import (
    FLARE_TOKENS,
    KINETIC_TOKENS,
    ERC20_ABI,
    WFLR_ABI,
    WFLR_ADDRESS,
    DEFAULT_FLARE_RPC_URL
)

# Import Uniswap functions from their respective modules
from tools.uniswap.swap import swap_tokens
from tools.uniswap.add_liquidity import add_liquidity
from tools.uniswap.remove_liquidity import remove_liquidity
from tools.uniswap.positions import get_positions
from tools.uniswap.pool_info import get_pool_info

# Import token functions from their respective modules
from tools.tokens.wrap import wrap_flare
from tools.tokens.unwrap import unwrap_flare
from tools.tokens.balance import display_token_balances as get_token_balances

# Import utility functions
from tools.utils.formatting import format_tx_hash_as_link
from tools.utils.web3_helpers import get_web3, get_account_from_private_key

# Import lending functions
from tools.lending import borrow, repay, supply

# Import function declarations
from tools.function_declarations import (
    get_swap_tool,
    get_lending_tool,
    get_liquidity_tools,
    get_wrap_unwrap_tools,
    get_all_tools
)

# Helper functions to get token dictionaries
def get_flare_tokens():
    return FLARE_TOKENS

def get_kinetic_tokens():
    return KINETIC_TOKENS 