"""
Tools module for Flare Bot.
This module exports all the necessary functions and constants for the bot.
"""

# Export constants
from .constants import (
    FLARE_TOKENS,
    KINETIC_TOKENS,
    ERC20_ABI,
    WFLR_ABI,
    WFLR_ADDRESS,
    DEFAULT_FLARE_RPC_URL
)

# Export Uniswap functions
from .uniswap.swap import swap_tokens
from .uniswap.add_liquidity import add_liquidity
from .uniswap.remove_liquidity import remove_liquidity
from .uniswap.positions import get_positions
from .uniswap.pool_info import get_pool_info

# Export token functions
from .tokens.wrap import wrap_flare
from .tokens.unwrap import unwrap_flare
from .tokens.balance import display_token_balances as get_token_balances

# Export lending functions
from .lending import borrow, repay, supply

# Export tool getter functions
from .function_declarations import (
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
