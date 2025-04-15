# Flare Bot Tools

This directory contains all the tools and utilities used by the Flare Bot application.

## Directory Structure

```
tools/
├── __init__.py             # Main exports
├── constants.py            # Constants (token addresses, ABIs, etc.)
├── function_declarations.py # Gemini AI function declarations
├── README.md               # This file
├── lending/                # Lending protocol tools
│   ├── __init__.py
│   ├── borrow.py           # Borrow functionality
│   ├── repay.py            # Repay functionality
│   └── supply.py           # Supply functionality
├── tokens/                 # Token-related tools
│   ├── __init__.py
│   ├── balance.py          # Token balance functionality
│   ├── unwrap.py           # Unwrap WFLR to FLR
│   └── wrap.py             # Wrap FLR to WFLR
├── uniswap/                # Uniswap V3 tools
│   ├── __init__.py
│   ├── add_liquidity.py    # Add liquidity functionality
│   ├── liquidity.py        # Liquidity management
│   ├── pool_info.py        # Pool information
│   ├── positions.py        # Position management
│   ├── remove_liquidity.py # Remove liquidity functionality
│   └── swap.py             # Token swap functionality
└── utils/                  # Utility functions
    ├── __init__.py
    ├── formatting.py       # Formatting utilities
    └── web3_helpers.py     # Web3 helper functions
```

## Usage

Import tools from the main module:

```python
from tools import (
    # Constants
    FLARE_TOKENS,
    KINETIC_TOKENS,
    
    # Uniswap functions
    swap_tokens,
    add_liquidity,
    remove_liquidity,
    get_positions,
    get_pool_info,
    
    # Token functions
    wrap_flare,
    unwrap_flare,
    get_token_balances,
    
    # Helper functions
    get_flare_tokens,
    get_kinetic_tokens
)

# Import utility functions
from tools.utils.formatting import format_tx_hash_as_link
from tools.utils.web3_helpers import get_web3, get_account_from_private_key
```

## Adding New Tools

To add a new tool:

1. Create a new file in the appropriate subdirectory
2. Export the tool's functions in the subdirectory's `__init__.py`
3. Import and export the tool in the main `tools/__init__.py`
4. Add function declarations to `function_declarations.py` if needed for Gemini AI 