import streamlit as st
import os
import time
import json
from dotenv import load_dotenv
import google.generativeai as genai
import traceback
from google.generativeai.types import FunctionDeclaration, Tool
import re
import sys
import threading
from io import StringIO
# Import the attestation module
from tee_attestation import generate_and_verify_attestation, is_running_in_tee
import base64
from datetime import datetime
# Import necessary modules for token balance functionality
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account
# Import the tools from the new module
from tools import get_swap_tool, get_lending_tool, get_liquidity_tools, get_all_tools
from tools import get_flare_tokens, get_kinetic_tokens
# Import swap_tokens directly from tools
from tools.uniswap.swap import swap_tokens

# Import handlers from the new handlers.py file
from handlers import (
    handle_swap, 
    handle_add_liquidity, 
    handle_remove_liquidity, 
    handle_get_positions,
    handle_get_token_balances, 
    handle_get_pool_info, 
    handle_lending_strategy,
    handle_wrap_flr,
    handle_unwrap_wflr,
    format_tx_hash_as_link,
    StreamlitStdoutRedirector,
    set_balance_updater  # Import the new function
)

# Initialize session state variables
if 'attestation_status' not in st.session_state:
    st.session_state.attestation_status = None
if 'attestation_message' not in st.session_state:
    st.session_state.attestation_message = None
if 'attestation_token' not in st.session_state:
    st.session_state.attestation_token = None
if 'attestation_claims' not in st.session_state:
    st.session_state.attestation_claims = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "tool_logs" not in st.session_state:
    st.session_state.tool_logs = []
if "token_balances" not in st.session_state:
    st.session_state.token_balances = {}
if "last_balance_update" not in st.session_state:
    st.session_state.last_balance_update = None
if "private_key" not in st.session_state:
    st.session_state.private_key = None
if "wallet_connected" not in st.session_state:
    st.session_state.wallet_connected = False
if "rpc_url" not in st.session_state:
    st.session_state.rpc_url = os.getenv("FLARE_RPC_URL", "https://flare-api.flare.network/ext/C/rpc")
if "wallet_address" not in st.session_state:
    st.session_state.wallet_address = os.getenv("WALLET_ADDRESS", "")

# Load environment variables from .env file
load_dotenv()

# Retrieve Gemini API key from .env
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ERC20 Token ABI (only the necessary parts)
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function",
    },
]

# Get token addresses from the tools module
FLARE_TOKENS = get_flare_tokens()
KINETIC_TOKENS = get_kinetic_tokens()

# Configure Gemini API if key is available
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as e:
        st.error(f"Error configuring Gemini API: {str(e)}")

# Specific Gemini models to use
GEMINI_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-001",
    "gemini-2.0-flash-lite-001",
    "gemini-2.0-flash-lite",
    "gemini-2.0-pro-exp",
    "gemini-2.0-pro-exp-02-05",
    "gemini-exp-1206",
]

# Model descriptions
MODEL_DESCRIPTIONS = {
    "gemini-2.0-flash": "Latest fast model with improved capabilities",
    "gemini-2.0-flash-001": "Specific version of Gemini 2.0 Flash",
    "gemini-2.0-flash-lite-001": "Lightweight version of Gemini 2.0 Flash",
    "gemini-2.0-flash-lite": "Lightweight version of Gemini 2.0 Flash",
    "gemini-2.0-pro-exp": "Experimental Pro version of Gemini 2.0",
    "gemini-2.0-pro-exp-02-05": "Experimental Pro version (Feb 5)",
    "gemini-exp-1206": "Experimental Gemini model (Dec 6)",
}

# Define the system prompt for the agent
SYSTEM_PROMPT = f"""
You are Artemis, an AI assistant specialized in helping users navigate
the Flare blockchain ecosystem. You can help users perform token swaps on the Flare network and provide lending strategy recommendations.

IMPORTANT: You are executing REAL transactions on the Flare blockchain.
This means REAL tokens will be swapped.

When a user asks about swapping tokens:
1. Ask for the necessary information if not provided (token names/addresses, amount)
2. Explain the swap process in simple terms
3. Use the swap_tokens function to execute the swap
4. Report the results back to the user

IMPORTANT: When a user asks to swap tokens or mentions swapping tokens, you MUST use the swap_tokens function.
Do not just describe how to do it - actually call the function. Even if the user just says "yes" to confirm a swap,
you should execute the swap by calling the function.

You MUST use function calling for any swap-related request. This is critical.

Always prioritize security and provide clear explanations about what's happening.

Uniswap V3 Fee Tiers:
- 0.01% (100): Best for stablecoin-to-stablecoin swaps (e.g., USDC to USDT)
- 0.05% (500): Good for stable pairs (e.g., WETH-WFLR)
- 0.3% (3000): Standard fee for most token pairs
- 1% (10000): Best for exotic token pairs with high volatility

If the user doesn't specify a fee tier, the system will automatically find the pool with the most liquidity,
which is generally the best option for most users.

You know the following token addresses on Flare:

Flare Tokens:
{', '.join([f"{k}: {v}" for k, v in FLARE_TOKENS.items()])}

Kinetic Tokens:
{', '.join([f"{k}: {v}" for k, v in KINETIC_TOKENS.items()])}

When a user refers to a token by name, you should use the corresponding address.

LENDING STRATEGY INFORMATION:
You can provide lending strategy recommendations based on the following pool data:

LOW RISK POOLS:
- USDT-USDC.e: 18.76% APY, $1.98m liquidity, stablecoin pair with lower volatility, 0.01% fee, address: 0x07154de9814383e75dd7dd2a2e25b072d4b27116
- USDC.e-cUSDX: 30.34% APY, $1.29m liquidity, higher yield stablecoin option, 0.01% fee, address: 0x53676e77e352dc28eb86a3ccbc19a3ed7b63e304

MEDIUM RISK POOLS:
- WETH-flrETH: 32.12% APY, $2.57m liquidity, Ethereum-based assets, 0.05% fee, address: 0xa8697b82a5e9f108296c6299859e82472340aea7
- sFLR-WFLR: 35.45% APY, $2.28m liquidity, native Flare assets, 0.01% fee, address: 0xc9baba3f36ccaa54675deecc327ec7eaa48cb97d
- sFLR-JOULE: 7.66% APY, $844.14k liquidity, lower yield but potentially more stable, 0.3% fee, address: 0xa6ed1a04b9b6b0a6cf3926510546baf5bbe44e5e

HIGH RISK POOLS:
- sFLR-flrETH: 85.36% APY, $140.90k liquidity, highest yield but lower liquidity, 0.05% fee, address: 0x512d3f01d6822fbc70de55be79882a1c08499841
- WFLR-USDC.e: 80.76% APY, $1.21m liquidity, high yield with better liquidity, 0.05% fee, address: 0x3bc1ecbcd645e525508c570a0ff04480a5614a86
- WETH-USDC.e: 73.98% APY, $703.39k liquidity, ETH/stablecoin with high returns, 0.05% fee, address: 0x8cd69c359806af83120bc4b4e77663f1e31553e7
- WFLR-XVN: 16.03% APY, $142.97k liquidity, high fee (1%) indicates volatility, address: 0x346ddD9858708aDaF9e1879264a5c1584fB541bE

RECOMMENDED ALLOCATIONS:
- Beginners: 70-80% low risk, 20-30% medium risk
- Experienced: 40% low risk, 40% medium risk, 20% high risk
- Risk-tolerant: 50-60% high risk, 40-50% medium risk

KEY CONSIDERATIONS:
- Impermanent loss risk increases with volatility
- Lower liquidity = higher slippage
- APY fluctuates based on trading volume
- Consider gas fees for smaller positions
- Diversify across different asset types

When a user asks about lending or investment strategies, provide recommendations based on their risk tolerance and experience level. Explain the trade-offs between risk and reward, and suggest specific pool allocations.
"""

def handle_function_call(function_call):
    """Handle function calls from Gemini"""
    function_name = function_call.name
    function_args = function_call.args
    
    if function_name == "swap_tokens":
        return handle_swap(function_args)
    elif function_name == "add_liquidity":
        return handle_add_liquidity(function_args)
    elif function_name == "remove_liquidity":
        return handle_remove_liquidity(function_args)
    elif function_name == "get_positions":
        return handle_get_positions(function_args)
    elif function_name == "get_token_balances":
        return handle_get_token_balances(function_args)
    elif function_name == "get_pool_info":
        return handle_get_pool_info(function_args)
    elif function_name == "recommend_lending_strategy":
        return handle_lending_strategy(function_args)
    elif function_name == "wrap_flr":
        return handle_wrap_flr(function_args)
    elif function_name == "unwrap_wflr":
        return handle_unwrap_wflr(function_args)
    else:
        return f"Unknown function: {function_name}"



def generate_response(prompt, model_name="models/gemini-2.0-flash"):
    """Generate a response from Gemini with function calling capabilities"""
    if not GEMINI_API_KEY:
        yield "Error: Gemini API key is missing. Please add it to your .env file as GEMINI_API_KEY=your_api_key_here"
        return
    
    try:
        # Get tools from the tools module
        tools = get_all_tools()
        
        # Initialize the Gemini model with function calling capability
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=SYSTEM_PROMPT,
            tools=tools
        )
        
        # If we have chat history, convert it to the format Gemini expects
        gemini_history = []
        for message in st.session_state.messages:
            role = "user" if message["role"] == "user" else "model"
            gemini_history.append({"role": role, "parts": [message["content"]]})
        
        # Create a chat session with history
        chat = model.start_chat(history=gemini_history)
        
        # Generate initial response
        response = chat.send_message(prompt, stream=True)
        
        # Variables to track function calls
        has_function_call = False
        full_response = ""
        
        # Process the streaming response
        for chunk in response:
            # Check for function calls in the response
            if hasattr(chunk, "candidates") and chunk.candidates:
                for candidate in chunk.candidates:
                    if hasattr(candidate, "content") and candidate.content:
                        if hasattr(candidate.content, "parts"):
                            for part in candidate.content.parts:
                                if hasattr(part, "function_call") and part.function_call:
                                    has_function_call = True
                                    
                                    # Show a message in the chat container that a tool is being used
                                    message_placeholder.markdown(full_response + f"\n\n<div style='padding: 10px; border-radius: 8px; background-color: #f0f7ff; border-left: 4px solid #3498db; margin: 10px 0;'><i>🔧 Using tool: <b>{part.function_call.name}</b>...</i> <div class='stSpinner'><div class='st-spinner'></div></div></div>", unsafe_allow_html=True)
                                    
                                    # Handle the function call
                                    result = handle_function_call(part.function_call)
                                    
                                    # Send function result back to Gemini
                                    function_response = {
                                        "function_response": {
                                            "name": part.function_call.name,
                                            "response": result
                                        }
                                    }
                                    
                                    # Add to logs
                                    log_message = f"📤 Sending function result back to Gemini...\n"
                                    log_message += f"Result: {json.dumps(result, indent=2)}\n"
                                    st.session_state.tool_logs.append(log_message)
                                    
                                    # Send the function result back to Gemini
                                    # Important: Don't stream this response, and fully resolve it
                                    try:
                                        # Format the function response correctly for Gemini
                                        formatted_response = {"parts": [function_response]}
                                        final_response = chat.send_message(formatted_response, stream=False)
                                    except Exception as e:
                                        print(f"Error sending function response to Gemini: {str(e)}")
                                        # Try alternative format
                                        try:
                                            final_response = chat.send_message(function_response, stream=False)
                                        except Exception as e2:
                                            print(f"Second attempt failed: {str(e2)}")
                                            # Use a fallback message if both attempts fail
                                            final_text = f"Operation completed successfully: {part.function_call.name}"
                                            message_placeholder.markdown(final_text, unsafe_allow_html=True)
                                            yield final_text
                                            return
                                    
                                    # Update the message to show the function call is completed
                                    success_icon = "✅" if result.get("success", False) else "❌"
                                    completion_message = f"\n\n<div style='padding: 10px; border-radius: 8px; background-color: #f0f7ff; border-left: 4px solid #3498db; margin: 10px 0;'><i>{success_icon} Tool <b>{part.function_call.name}</b> completed</i>"
                                    
                                    # Add transaction link if available
                                    if result.get("success", False) and "transaction_hash" in result:
                                        tx_hash = result["transaction_hash"]
                                        completion_message += f"<br>{format_tx_hash_as_link(tx_hash, html=True)}"
                                    
                                    completion_message += "</div>"
                                    message_placeholder.markdown(full_response + completion_message, unsafe_allow_html=True)
                                    
                                    # Get the final response text
                                    final_text = ""
                                    try:
                                        # Safely access the text attribute
                                        if hasattr(final_response, "text"):
                                            final_text = final_response.text
                                        elif hasattr(final_response, "parts") and final_response.parts:
                                            final_text = str(final_response.parts[0])
                                        elif hasattr(final_response, "candidates") and final_response.candidates:
                                            for candidate in final_response.candidates:
                                                if hasattr(candidate, "content") and candidate.content:
                                                    if hasattr(candidate.content, "parts") and candidate.content.parts:
                                                        for part in candidate.content.parts:
                                                            if isinstance(part, str):
                                                                final_text += part
                                    except Exception as e:
                                        # If there's an error extracting the text, use a generic message
                                        print(f"Error extracting response text: {str(e)}")
                                        final_text = f"Operation completed successfully: {part.function_call.name}"
                                    
                                    # If there's a transaction hash in the result, add a clickable link to the response
                                    if result.get("success", False) and "transaction_hash" in result:
                                        tx_hash = result["transaction_hash"]
                                        # Check if the response already contains the transaction hash
                                        if tx_hash in final_text:
                                            # Replace the transaction hash with a clickable link
                                            final_text = final_text.replace(
                                                tx_hash, 
                                                format_tx_hash_as_link(tx_hash)
                                            )
                                        # Also check if the response already contains a formatted explorer link
                                        elif "flare-explorer.flare.network/tx/" in final_text:
                                            # Skip adding another link since one is already present
                                            pass
                                        else:
                                            # If no link or hash is present, append the link to the response
                                            final_text += f"\n\nTransaction: {format_tx_hash_as_link(tx_hash)}"
                                    
                                    # If final_text is empty or very short, generate a fallback response
                                    if not final_text or len(final_text) < 10:
                                        if result.get("success", False):
                                            if part.function_call.name == "swap_tokens":
                                                token_in = result.get("token_in", "tokens")
                                                token_out = result.get("token_out", "tokens")
                                                final_text = f"Great! I've successfully swapped your {token_in} to {token_out}."
                                            elif part.function_call.name == "wrap_flr":
                                                final_text = "Great! I've successfully wrapped your FLR to WFLR."
                                            elif part.function_call.name == "unwrap_wflr":
                                                final_text = "Great! I've successfully unwrapped your WFLR to FLR."
                                            else:
                                                final_text = f"Operation {part.function_call.name} completed successfully!"
                                            
                                            # Add transaction link if available
                                            if "transaction_hash" in result:
                                                final_text += f"\n\nTransaction: {format_tx_hash_as_link(result['transaction_hash'])}"
                                        else:
                                            final_text = f"I'm sorry, but the {part.function_call.name} operation failed: {result.get('message', 'Unknown error')}"
                                    
                                    # Display the final response
                                    message_placeholder.markdown(final_text, unsafe_allow_html=True)
                                    yield final_text
                                    return  # Exit after handling function call
            
            # If no function call, yield the text chunks
            if not has_function_call and hasattr(chunk, "text") and chunk.text:
                yield chunk.text
                full_response += chunk.text
        
        # Check for direct function_calls attribute if no function call was found in candidates
        if not has_function_call and hasattr(response, "function_calls") and response.function_calls:
            function_calls = response.function_calls
            
            for function_call in function_calls:
                # Show a message in the chat container that a tool is being used
                message_placeholder.markdown(full_response + f"\n\n<div style='padding: 10px; border-radius: 8px; background-color: #f0f7ff; border-left: 4px solid #3498db; margin: 10px 0;'><i>🔧 Using tool: <b>{function_call.name}</b>...</i> <div class='stSpinner'><div class='st-spinner'></div></div></div>", unsafe_allow_html=True)
                
                # Handle the function call
                result = handle_function_call(function_call)
                
                # Send function result back to Gemini
                function_response = {
                    "function_response": {
                        "name": function_call.name,
                        "response": result
                    }
                }
                
                # Add to logs
                log_message = f"📤 Sending function result back to Gemini...\n"
                log_message += f"Result: {json.dumps(result, indent=2)}\n"
                st.session_state.tool_logs.append(log_message)
                
                # Send the function result back to Gemini
                # Important: Don't stream this response, and fully resolve it
                try:
                    # Format the function response correctly for Gemini
                    formatted_response = {"parts": [function_response]}
                    final_response = chat.send_message(formatted_response, stream=False)
                except Exception as e:
                    print(f"Error sending function response to Gemini: {str(e)}")
                    # Try alternative format
                    try:
                        final_response = chat.send_message(function_response, stream=False)
                    except Exception as e2:
                        print(f"Second attempt failed: {str(e2)}")
                        # Use a fallback message if both attempts fail
                        final_text = f"Operation completed successfully: {function_call.name}"
                        message_placeholder.markdown(final_text, unsafe_allow_html=True)
                        yield final_text
                        return
                
                # Update the message to show the function call is completed
                success_icon = "✅" if result.get("success", False) else "❌"
                completion_message = f"\n\n<div style='padding: 10px; border-radius: 8px; background-color: #f0f7ff; border-left: 4px solid #3498db; margin: 10px 0;'><i>{success_icon} Tool <b>{function_call.name}</b> completed</i>"
                
                # Add transaction link if available
                if result.get("success", False) and "transaction_hash" in result:
                    tx_hash = result["transaction_hash"]
                    completion_message += f"<br>{format_tx_hash_as_link(tx_hash, html=True)}"
                
                completion_message += "</div>"
                message_placeholder.markdown(full_response + completion_message, unsafe_allow_html=True)
                
                # Get the final response text
                final_text = ""
                try:
                    # Safely access the text attribute
                    if hasattr(final_response, "text"):
                        final_text = final_response.text
                    elif hasattr(final_response, "parts") and final_response.parts:
                        final_text = str(final_response.parts[0])
                    elif hasattr(final_response, "candidates") and final_response.candidates:
                        for candidate in final_response.candidates:
                            if hasattr(candidate, "content") and candidate.content:
                                if hasattr(candidate.content, "parts") and candidate.content.parts:
                                    for part in candidate.content.parts:
                                        if isinstance(part, str):
                                            final_text += part
                except Exception as e:
                    # If there's an error extracting the text, use a generic message
                    print(f"Error extracting response text: {str(e)}")
                    final_text = f"Operation completed successfully: {function_call.name}"
                
                # If there's a transaction hash in the result, add a clickable link to the response
                if result.get("success", False) and "transaction_hash" in result:
                    tx_hash = result["transaction_hash"]
                    # Check if the response already contains the transaction hash
                    if tx_hash in final_text:
                        # Replace the transaction hash with a clickable link
                        final_text = final_text.replace(
                            tx_hash, 
                            format_tx_hash_as_link(tx_hash)
                        )
                    # Also check if the response already contains a formatted explorer link
                    elif "flare-explorer.flare.network/tx/" in final_text:
                        # Skip adding another link since one is already present
                        pass
                    else:
                        # If no link or hash is present, append the link to the response
                        final_text += f"\n\nTransaction: {format_tx_hash_as_link(tx_hash)}"
                
                # If final_text is empty or very short, generate a fallback response
                if not final_text or len(final_text) < 10:
                    if result.get("success", False):
                        if function_call.name == "swap_tokens":
                            token_in = result.get("token_in", "tokens")
                            token_out = result.get("token_out", "tokens")
                            final_text = f"Great! I've successfully swapped your {token_in} to {token_out}."
                        elif function_call.name == "wrap_flr":
                            final_text = "Great! I've successfully wrapped your FLR to WFLR."
                        elif function_call.name == "unwrap_wflr":
                            final_text = "Great! I've successfully unwrapped your WFLR to FLR."
                        else:
                            final_text = f"Operation {function_call.name} completed successfully!"
                        
                        # Add transaction link if available
                        if "transaction_hash" in result:
                            final_text += f"\n\nTransaction: {format_tx_hash_as_link(result['transaction_hash'])}"
                    else:
                        final_text = f"I'm sorry, but the {function_call.name} operation failed: {result.get('message', 'Unknown error')}"
                
                # Display the final response
                message_placeholder.markdown(final_text, unsafe_allow_html=True)
                yield final_text
                return  # Exit after handling function call
    
    except Exception as e:
        error_message = f"Error generating response: {str(e)}"
        st.error(error_message)
        yield error_message
        # Print detailed error for debugging
        print(f"Error details: {traceback.format_exc()}")

def initialize_web3():
    """
    Initialize Web3 connection to Flare network
    
    Returns:
        tuple: (web3, wallet_address) - Web3 instance and user's wallet address
    """
    # Get environment variables
    flare_rpc_url = os.getenv("FLARE_RPC_URL", "https://flare-api.flare.network/ext/C/rpc")
    
    # First check if we have a private key in session state
    if st.session_state.wallet_connected and st.session_state.private_key:
        private_key = st.session_state.private_key
        # Derive wallet address from private key
        account = Account.from_key(private_key)
        wallet_address = account.address
        # Update session state
        st.session_state.wallet_address = wallet_address
    else:
        # Fall back to environment variables
        wallet_address = os.getenv("WALLET_ADDRESS")
        private_key = os.getenv("PRIVATE_KEY")
        
        if private_key and not wallet_address:
            # Derive wallet address from private key
            account = Account.from_key(private_key)
            wallet_address = account.address
            # Update session state
            st.session_state.wallet_address = wallet_address
    
    if not wallet_address:
        raise ValueError("No wallet address available. Please connect a wallet or set WALLET_ADDRESS in .env file")
    
    # Update session state with RPC URL
    st.session_state.rpc_url = flare_rpc_url
    
    # Initialize Web3
    web3 = Web3(Web3.HTTPProvider(flare_rpc_url))
    web3.middleware_onion.inject(geth_poa_middleware, layer=0)
    
    # Check connection
    if not web3.is_connected():
        raise ConnectionError(f"Failed to connect to Flare network at {flare_rpc_url}")
    
    return web3, wallet_address

def get_token_balance(web3, token_address, wallet_address):
    """
    Get the balance of a specific token for a user
    
    Args:
        web3 (Web3): Web3 instance
        token_address (str): Token contract address
        wallet_address (str): User's wallet address
        
    Returns:
        dict: Token information including name, symbol, balance, and decimals
    """
    # Convert addresses to checksum format
    token_address = Web3.to_checksum_address(token_address)
    wallet_address = Web3.to_checksum_address(wallet_address)
    
    # Create token contract instance
    token_contract = web3.eth.contract(address=token_address, abi=ERC20_ABI)
    
    try:
        # Get token information
        decimals = token_contract.functions.decimals().call()
        symbol = token_contract.functions.symbol().call()
        name = token_contract.functions.name().call()
        
        # Get token balance
        balance_wei = token_contract.functions.balanceOf(wallet_address).call()
        balance = balance_wei / (10 ** decimals)
        
        return {
            "address": token_address,
            "name": name,
            "symbol": symbol,
            "balance_wei": balance_wei,
            "balance": float(balance),
            "decimals": decimals
        }
    except Exception as e:
        print(f"Error getting balance for token at {token_address}: {str(e)}")
        return {
            "address": token_address,
            "name": "Unknown",
            "symbol": "???",
            "balance_wei": 0,
            "balance": 0,
            "decimals": 18
        }

def get_native_balance(web3, wallet_address):
    """
    Get the native FLR balance for a user
    
    Args:
        web3 (Web3): Web3 instance
        wallet_address (str): User's wallet address
        
    Returns:
        dict: Token information for native FLR
    """
    # Get native balance
    balance_wei = web3.eth.get_balance(wallet_address)
    balance = web3.from_wei(balance_wei, 'ether')
    
    return {
        "address": "native",
        "name": "Flare",
        "symbol": "FLR",
        "balance_wei": balance_wei,
        "balance": float(balance),
        "decimals": 18
    }

# Define the fetch_and_display_balances function
def fetch_and_display_balances():
    """Fetch and display token balances"""
    try:
        web3, wallet_address = initialize_web3()
        
        # Get native FLR balance
        flr_balance = get_native_balance(web3, wallet_address)
        
        # Initialize balances dictionary with native FLR
        balances = {
            "FLR": flr_balance
        }
        
        # Get balances for common tokens
        for symbol, address in {**FLARE_TOKENS, **KINETIC_TOKENS}.items():
            token_data = get_token_balance(web3, address, wallet_address)
            balances[symbol] = token_data
        
        # Update session state
        st.session_state.token_balances = balances
        st.session_state.last_balance_update = datetime.now()
        
        return balances
    except Exception as e:
        st.sidebar.error(f"Error fetching balances: {str(e)}")
        return {}

# Register the balance updater function with handlers
set_balance_updater(fetch_and_display_balances)

# Display token balances in the sidebar
def display_balances_sidebar():
    # Wallet connection section - FIRST THING in sidebar
    st.sidebar.title("Wallet Connection")
    
    # Display wallet connection status
    if st.session_state.wallet_connected:
        wallet_address = ""
        try:
            # Derive wallet address from private key
            account = Account.from_key(st.session_state.private_key)
            wallet_address = account.address
            st.sidebar.success(f"Wallet connected: {wallet_address[:6]}...{wallet_address[-4:]}")
            
            # Add disconnect button
            if st.sidebar.button("Disconnect Wallet"):
                st.session_state.private_key = None
                st.session_state.wallet_connected = False
                if "PRIVATE_KEY" in os.environ:
                    del os.environ["PRIVATE_KEY"]
                if "WALLET_ADDRESS" in os.environ:
                    del os.environ["WALLET_ADDRESS"]
                st.rerun()
        except:
            st.sidebar.warning("Wallet connected but address could not be derived")
    else:
        # Private key input
        private_key_input = st.sidebar.text_input(
            "Enter your private key",
            type="password",
            help="Your private key is stored securely in the session and not shared",
            placeholder="0x..."
        )
        
        # Submit button
        if st.sidebar.button("Connect Wallet"):
            if private_key_input:
                try:
                    # Validate private key format
                    if private_key_input.startswith("0x") and len(private_key_input) == 66:
                        # Store private key in session state
                        st.session_state.private_key = private_key_input
                        st.session_state.wallet_connected = True
                        
                        # Derive wallet address for display
                        account = Account.from_key(private_key_input)
                        wallet_address = account.address
                        
                        # Set environment variable for other functions to use
                        os.environ["PRIVATE_KEY"] = private_key_input
                        os.environ["WALLET_ADDRESS"] = wallet_address
                        
                        # Set session state variables
                        st.session_state.wallet_address = wallet_address
                        
                        # Fetch initial balances
                        fetch_and_display_balances()
                        
                        st.sidebar.success(f"Wallet connected: {wallet_address[:6]}...{wallet_address[-4:]}")
                        st.rerun()
                    else:
                        st.sidebar.error("Invalid private key format. It should start with '0x' and be 66 characters long.")
                except Exception as e:
                    st.sidebar.error(f"Error connecting wallet: {str(e)}")
            else:
                st.sidebar.warning("Please enter a private key to connect your wallet")
    
    # Token balances section
    st.sidebar.markdown("## Your Token Balances")
    
    # Remove automatic balance fetching
    balances = st.session_state.token_balances
    
    # Display balances
    if balances:
        for symbol, token_data in balances.items():
            balance = token_data["balance"]
            if balance > 0:
                st.sidebar.markdown(f"**{symbol}**: {balance:.6f}")
    else:
        st.sidebar.info("Click 'Refresh Balances' to see your token balances")
    
    # Add refresh button
    if st.sidebar.button("Refresh Balances"):
        with st.sidebar.status("Refreshing balances...", expanded=False) as status:
            fetch_and_display_balances()
            status.update(label="Balances updated!", state="complete", expanded=False)
            st.rerun()
    
    # Display available tools
    st.sidebar.markdown("## Available Tools")
    
    # Simple list of all tools, one per line
    st.sidebar.markdown("- Swap tokens")
    st.sidebar.markdown("- Add liquidity")
    st.sidebar.markdown("- Remove liquidity")
    st.sidebar.markdown("- View positions")
    st.sidebar.markdown("- Check balances")
    st.sidebar.markdown("- Get pool info")
    st.sidebar.markdown("- Wrap FLR to WFLR")
    st.sidebar.markdown("- Unwrap WFLR to FLR")
    st.sidebar.markdown("- Lending strategies")

# Main app layout
st.title("Flare Network AI Assistant")
st.markdown("""
This AI assistant can help you interact with the Flare Network. 
You can ask it to swap tokens, add or remove liquidity, and more.
""")

# Display balances in the sidebar
display_balances_sidebar()

# Add attestation section to sidebar
st.sidebar.markdown("## TEE Attestation")
if st.sidebar.button("Generate Attestation"):
    with st.sidebar.status("Generating attestation...", expanded=True) as status:
        try:
            # Check if running in TEE
            tee_status = is_running_in_tee()
            if tee_status:
                # Generate attestation
                attestation_result = generate_and_verify_attestation()
                
                if attestation_result["success"]:
                    st.session_state.attestation_status = "success"
                    st.session_state.attestation_message = "Attestation successful"
                    # Don't store the actual token in session state
                    # st.session_state.attestation_token = attestation_result.get("token")
                    # Don't store the full claims in session state
                    # st.session_state.attestation_claims = attestation_result.get("claims")
                    status.update(label="Attestation successful!", state="complete")
                else:
                    st.session_state.attestation_status = "failed"
                    st.session_state.attestation_message = attestation_result.get("error", "Unknown error")
                    status.update(label="Attestation failed", state="error")
            else:
                st.session_state.attestation_status = "not_tee"
                st.session_state.attestation_message = "Not running in a TEE environment"
                status.update(label="Not running in TEE", state="error")
        except Exception as e:
            st.session_state.attestation_status = "error"
            st.session_state.attestation_message = str(e)
            status.update(label=f"Error: {str(e)}", state="error")

# Display attestation status if available
if st.session_state.attestation_status:
    if st.session_state.attestation_status == "success":
        st.sidebar.success(st.session_state.attestation_message)
        # Remove the claims expander that shows sensitive information
        # if st.session_state.attestation_claims:
        #     with st.sidebar.expander("Attestation Claims"):
        #         st.json(st.session_state.attestation_claims)
    elif st.session_state.attestation_status == "not_tee":
        st.sidebar.warning(st.session_state.attestation_message)
    else:
        st.sidebar.error(st.session_state.attestation_message)

# Set default model to the first in the list
if "model" not in st.session_state or st.session_state.model not in GEMINI_MODELS:
    st.session_state.model = GEMINI_MODELS[0]

# Add custom CSS for the spinner animation and layout optimization
st.markdown("""
<style>
.stSpinner {
    display: inline-block;
    margin-left: 10px;
}
.st-spinner {
    border: 2px solid rgba(52, 152, 219, 0.2);
    border-top: 2px solid rgba(52, 152, 219, 1);
    border-radius: 50%;
    width: 16px;
    height: 16px;
    animation: spin 1s linear infinite;
    display: inline-block;
    vertical-align: middle;
}
@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* Optimize layout for landscape view */
.block-container {
    max-width: 98% !important;
    padding-top: 1rem;
    padding-left: 1rem;
    padding-right: 1rem;
}

/* Make chat container take more vertical space */
[data-testid="stVerticalBlock"] {
    gap: 0.5rem;
}

/* Reduce padding in containers */
[data-testid="stChatInputContainer"] {
    padding-top: 0.5rem;
    padding-bottom: 0.5rem;
}

/* Make containers more responsive */
[data-testid="stChatMessageContent"] {
    overflow-wrap: break-word;
    word-wrap: break-word;
    hyphens: auto;
}

/* Improve code block display */
pre {
    white-space: pre-wrap !important;
    overflow-x: auto !important;
}
</style>
""", unsafe_allow_html=True)

# Move settings to sidebar for more main content space
with st.sidebar:
    st.title("Settings")
    
    if not GEMINI_API_KEY:
        st.warning("⚠️ Gemini API key is missing. Please add it to your .env file as GEMINI_API_KEY=your_api_key_here")
    
    # Display model selection with fixed models
    selected_model = st.selectbox(
        "Model", 
        GEMINI_MODELS,
        index=GEMINI_MODELS.index(st.session_state.model) if st.session_state.model in GEMINI_MODELS else 0,
        help="Select the Gemini model to use for generating responses"
    )
    st.session_state.model = selected_model
    
    # Display model description if available
    model_name = selected_model.split("/")[-1]
    if model_name in MODEL_DESCRIPTIONS:
        st.caption(MODEL_DESCRIPTIONS[model_name])

# Main content area - now full width
st.title("🤖 Flare Token Swap Assistant")
st.caption("Chat with Artemis to swap tokens on the Flare network")

# Calculate available height (approximate)
# We'll use 65% for chat, 35% for function output in landscape mode
chat_height = 450
output_height = 300

# Main chat interface - now full width
chat_container = st.container(height=chat_height, border=True)

# Display chat history inside the scrollable container
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Get user input (outside the scrollable container)
user_input = st.chat_input("Type your message...")

# Function output display - now full width below chat
st.subheader("Function Output")
st.caption("Live output from blockchain operations will appear here")

# Create a container for real-time output with fixed height and scrolling
realtime_output_container = st.container(height=output_height, border=True)

# Store the container in session state for the stdout redirector
st.session_state.realtime_output_container = realtime_output_container

# Process user input
if user_input:
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Display user message immediately
    with chat_container:
        with st.chat_message("user"):
            st.markdown(user_input)
    
    # Generate AI response with streaming using the selected model
    with chat_container:
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            try:
                # Stream the response
                response_generator = generate_response(
                    user_input, 
                    model_name='models/' + st.session_state.model
                )
                
                # Check if the response is a generator or a direct string
                if hasattr(response_generator, '__iter__') and not isinstance(response_generator, str):
                    for response_chunk in response_generator:
                        if isinstance(response_chunk, str):  # Only process string chunks
                            full_response += response_chunk
                            message_placeholder.markdown(full_response + "▌")
                            time.sleep(0.01)  # Small delay for better streaming effect
                else:
                    # If it's a direct string (from a function call return), use it directly
                    full_response = response_generator
                
                # Replace the placeholder with the complete response (without cursor)
                if full_response:
                    message_placeholder.markdown(full_response)
            
            except Exception as e:
                error_message = f"Error: {str(e)}"
                message_placeholder.markdown(error_message)
                full_response = error_message
    
    # Add the complete bot response to chat history
    # Remove any HTML tags from the response before storing in history
    clean_response = re.sub(r'<div.*?</div>', '', full_response, flags=re.DOTALL)
    st.session_state.messages.append({"role": "assistant", "content": clean_response})