"""
Function declarations for Gemini AI integration.
"""

import google.generativeai as genai
from google.generativeai.types import FunctionDeclaration, Tool

# Define the function for Gemini to call
swap_function = FunctionDeclaration(
    name="swap_tokens",
    description="Swap tokens on Flare network using Uniswap V3",
    parameters={
        "type": "OBJECT",
        "properties": {
            "token_in": {
                "type": "STRING",
                "description": "Name or address of the input token (e.g., 'WFLR' or '0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d')"
            },
            "token_out": {
                "type": "STRING",
                "description": "Name or address of the output token (e.g., 'USDC' or '0xFbDa5F676cB37624f28265A144A48B0d6e87d3b6')"
            },
            "amount_in_eth": {
                "type": "STRING",
                "description": "Amount of input token to swap in ETH format (e.g., '0.1' for 0.1 WFLR)"
            },
            "slippage_percent": {
                "type": "STRING",
                "description": "Maximum acceptable slippage in percentage (e.g., '0.5' for 0.5%)"
            },
            "fee_tier": {
                "type": "STRING",
                "description": "Fee tier for the swap (100 for 0.01%, 500 for 0.05%, 3000 for 0.3%, 10000 for 1%)"
            }
        },
        "required": ["token_in", "token_out", "amount_in_eth"]
    }
)

# Define a function for lending strategy recommendations
lending_strategy_function = FunctionDeclaration(
    name="recommend_lending_strategy",
    description="Provide lending strategy recommendations based on user's risk profile",
    parameters={
        "type": "OBJECT",
        "properties": {
            "risk_profile": {
                "type": "STRING",
                "description": "User's risk tolerance level (low, medium, high)"
            },
            "experience_level": {
                "type": "STRING",
                "description": "User's experience with DeFi (beginner, intermediate, experienced)"
            },
            "investment_amount": {
                "type": "STRING",
                "description": "Optional: Approximate amount user wants to invest"
            }
        },
        "required": ["risk_profile"]
    }
)

# Define function for adding liquidity
add_liquidity_function = FunctionDeclaration(
    name="add_liquidity",
    description="Add liquidity to a Uniswap V3 pool on Flare network",
    parameters={
        "type": "OBJECT",
        "properties": {
            "token0": {
                "type": "STRING",
                "description": "Name or address of token0 (must be lower address than token1)"
            },
            "token1": {
                "type": "STRING",
                "description": "Name or address of token1 (must be higher address than token0)"
            },
            "amount0": {
                "type": "NUMBER",
                "description": "Amount of token0 in token units"
            },
            "amount1": {
                "type": "NUMBER",
                "description": "Amount of token1 in token units"
            },
            "fee": {
                "type": "INTEGER",
                "description": "Fee tier (3000 = 0.3%, 500 = 0.05%, 10000 = 1%). Default is 3000."
            }
        },
        "required": ["token0", "token1", "amount0", "amount1"]
    }
)

# Define function for removing liquidity
remove_liquidity_function = FunctionDeclaration(
    name="remove_liquidity",
    description="Remove liquidity from a Uniswap V3 position on Flare network",
    parameters={
        "type": "OBJECT",
        "properties": {
            "position_id": {
                "type": "INTEGER",
                "description": "The ID of the position to remove liquidity from"
            },
            "percent_to_remove": {
                "type": "NUMBER",
                "description": "Percentage of liquidity to remove (1-100). Default is 100 (remove all)."
            }
        },
        "required": ["position_id"]
    }
)

# Define function for getting positions
get_positions_function = FunctionDeclaration(
    name="get_positions",
    description="Get all Uniswap V3 positions for a wallet on Flare network",
    parameters={
        "type": "OBJECT",
        "properties": {
            "wallet_address": {
                "type": "STRING",
                "description": "The wallet address to get positions for. If not provided, uses the connected wallet."
            }
        },
        "required": []
    }
)

# Define function for getting token balances
get_token_balances_function = FunctionDeclaration(
    name="get_token_balances",
    description="Get token balances for a wallet on Flare network",
    parameters={
        "type": "OBJECT",
        "properties": {
            "wallet_address": {
                "type": "STRING",
                "description": "The wallet address to get balances for. If not provided, uses the connected wallet."
            },
            "tokens": {
                "type": "ARRAY",
                "items": {
                    "type": "STRING"
                },
                "description": "List of token symbols or addresses to check balances for. If not provided, returns balances for common tokens."
            }
        },
        "required": []
    }
)

# Define function for getting pool information
get_pool_info_function = FunctionDeclaration(
    name="get_pool_info",
    description="Get information about a Uniswap V3 pool on Flare network",
    parameters={
        "type": "OBJECT",
        "properties": {
            "token0": {
                "type": "STRING",
                "description": "Name or address of token0"
            },
            "token1": {
                "type": "STRING",
                "description": "Name or address of token1"
            },
            "fee": {
                "type": "INTEGER",
                "description": "Fee tier (3000 = 0.3%, 500 = 0.05%, 10000 = 1%). Default is 3000."
            }
        },
        "required": ["token0", "token1"]
    }
)

# Define function for wrapping FLR to WFLR
wrap_flr_function = FunctionDeclaration(
    name="wrap_flr",
    description="Wrap native FLR to WFLR (Wrapped Flare) on Flare network",
    parameters={
        "type": "OBJECT",
        "properties": {
            "amount_flr": {
                "type": "STRING",
                "description": "Amount of FLR to wrap as a string that can be converted to a float (e.g., '1.0' for 1 FLR)"
            }
        },
        "required": ["amount_flr"]
    }
)

# Define function for unwrapping WFLR to FLR
unwrap_wflr_function = FunctionDeclaration(
    name="unwrap_wflr",
    description="Unwrap WFLR (Wrapped Flare) back to native FLR on Flare network",
    parameters={
        "type": "OBJECT",
        "properties": {
            "amount_wflr": {
                "type": "STRING",
                "description": "Amount of WFLR to unwrap (e.g., '1.0' for 1 WFLR)"
            }
        },
        "required": ["amount_wflr"]
    }
)

# Create tools with the function declarations
def get_swap_tool():
    return Tool(function_declarations=[swap_function])

def get_lending_tool():
    return Tool(function_declarations=[lending_strategy_function])

def get_liquidity_tools():
    return Tool(function_declarations=[
        add_liquidity_function,
        remove_liquidity_function,
        get_positions_function,
        get_token_balances_function,
        get_pool_info_function
    ])

def get_wrap_unwrap_tools():
    return Tool(function_declarations=[wrap_flr_function, unwrap_wflr_function])

def get_all_tools():
    return [get_swap_tool(), get_lending_tool(), get_liquidity_tools(), get_wrap_unwrap_tools()] 