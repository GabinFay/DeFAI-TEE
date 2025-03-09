import google.generativeai as genai
from google.generativeai.types import FunctionDeclaration, Tool

# Flare token addresses
FLARE_TOKENS = {
    'flrETH': '0x26A1faB310bd080542DC864647d05985360B16A5',
    'sFLR': '0x12e605bc104e93B45e1aD99F9e555f659051c2BB',
    'Joule': '0xE6505f92583103AF7ed9974DEC451A7Af4e3A3bE',
    'Usdx': '0xFE2907DFa8DB6e320cDbF45f0aa888F6135ec4f8',
    'USDT': '0x0B38e83B86d491735fEaa0a791F65c2B99535396',
    'USDC': '0xFbDa5F676cB37624f28265A144A48B0d6e87d3b6',
    'XVN': '0xaFBdD875858Dd48EE32A68Ac1349A5017095B161',
    'WFLR': '0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d',
    'cysFLR': '0x19831cfB53A0dbeAD9866C43557C1D48DfF76567',
    'WETH': '0x1502FA4be69d526124D453619276FacCab275d3D',
}

# Kinetic token addresses on Flare
KINETIC_TOKENS = {
    'sFLR': '0x12e605bc104e93B45e1aD99F9e555f659051c2BB',
    'USDC.e': '0xFbDa5F676cB37624f28265A144A48B0d6e87d3b6',
    'USDT': '0x0B38e83B86d491735fEaa0a791F65c2B99535396',
    'wETH': '0x1502FA4be69d526124D453619276FacCab275d3D',
    'flETH': '0x26A1faB310bd080542DC864647d05985360B16A5',
    'kwETH': '0x5C2400019017AE61F811D517D088Df732642DbD0',
    'ksFLR': '0x291487beC339c2fE5D83DD45F0a15EFC9Ac45656',
    'kUSDC.e': '0xDEeBaBe05BDA7e8C1740873abF715f16164C29B8',
    'kUSDT': '0x1e5bBC19E0B17D7d38F318C79401B3D16F2b93bb',
    'rFLR': '0x26d460c3Cf931Fb2014FA436a49e3Af08619810e',
    'kflETH': '0x40eE5dfe1D4a957cA8AC4DD4ADaf8A8fA76b1C16',
}

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

def get_all_tools():
    return [get_swap_tool(), get_lending_tool(), get_liquidity_tools()]

# Export token dictionaries
def get_flare_tokens():
    return FLARE_TOKENS

def get_kinetic_tokens():
    return KINETIC_TOKENS 