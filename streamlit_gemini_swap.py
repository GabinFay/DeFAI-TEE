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

# Initialize session state variables
if 'attestation_status' not in st.session_state:
    st.session_state.attestation_status = None
if 'attestation_message' not in st.session_state:
    st.session_state.attestation_message = None
if 'attestation_token' not in st.session_state:
    st.session_state.attestation_token = None
if 'attestation_claims' not in st.session_state:
    st.session_state.attestation_claims = None

# Custom stdout redirector for real-time display in Streamlit
class StreamlitStdoutRedirector:
    def __init__(self, placeholder):
        self.placeholder = placeholder
        self.buffer = StringIO()
        self.lock = threading.Lock()
        self.original_stdout = sys.stdout
        self.last_update_time = time.time()
        self.update_interval = 0.1  # Update UI every 0.1 seconds to avoid overwhelming Streamlit
    
    def write(self, text):
        # Write to the original stdout for terminal display
        self.original_stdout.write(text)
        self.original_stdout.flush()
        
        # Also capture for Streamlit display
        with self.lock:
            self.buffer.write(text)
            
            # Update the Streamlit component with the current buffer content
            # but not too frequently to avoid overwhelming the UI
            current_time = time.time()
            if current_time - self.last_update_time > self.update_interval:
                self.update_ui()
                self.last_update_time = current_time
    
    def update_ui(self):
        # Create a styled display for the output
        content = self.buffer.getvalue()
        if content:
            # Use markdown with code block for better formatting
            self.placeholder.markdown(f"```\n{content}\n```")
    
    def flush(self):
        self.original_stdout.flush()
        # Force an update when flush is called
        self.update_ui()
    
    def reset(self):
        with self.lock:
            self.buffer = StringIO()
            self.placeholder.empty()
    
    def get_value(self):
        with self.lock:
            return self.buffer.getvalue()

# Import the real swap function
try:
    from flare_uniswap_sdk_swap import swap_tokens
except ImportError:
    raise ImportError("Could not import swap_tokens function. Make sure the flare_bot2 module is in your Python path.")

# Load environment variables from .env file
load_dotenv()

# Retrieve Gemini API key from .env
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

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
the Flare blockchain ecosystem. You can help users perform token swaps on the Flare network.

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
"""

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
                "type": "NUMBER",
                "description": "Amount of input token in ETH units (e.g., 0.01 for 0.01 WFLR)"
            },
            "fee": {
                "type": "INTEGER",
                "description": "Fee tier (3000 = 0.3%, 500 = 0.05%, 10000 = 1%, 100 = 0.01%). If not provided, the system will automatically select the pool with the most liquidity."
            }
        },
        "required": ["token_in", "token_out", "amount_in_eth"]
    }
)

def format_tx_hash_as_link(tx_hash, html=False):
    """
    Format a transaction hash as a clickable link to the Flare Explorer
    
    Args:
        tx_hash: The transaction hash
        html: Whether to return HTML format (for UI elements) or Markdown format (for chat messages)
        
    Returns:
        str: Formatted link
    """
    explorer_url = f"https://flare-explorer.flare.network/tx/{tx_hash}"
    if html:
        return f"<a href='{explorer_url}' target='_blank'>View on Flare Explorer</a>"
    else:
        return f"[View on Flare Explorer]({explorer_url})"

def handle_function_call(function_call):
    """
    Handle function calls from Gemini
    
    Args:
        function_call: The function call object from Gemini
        
    Returns:
        dict: Result of the function call
    """
    if function_call.name == "swap_tokens":
        # Parse arguments
        args = function_call.args
        token_in = args.get("token_in")
        token_out = args.get("token_out")
        amount_in_eth = args.get("amount_in_eth")
        fee = args.get("fee")  # This can be None, which will trigger automatic fee selection
        
        # Store original token names/addresses for display
        original_token_in = token_in
        original_token_out = token_out
        
        # Resolve token names to addresses if needed
        token_in_symbol = None
        token_out_symbol = None
        
        # Check if token_in is a name rather than an address
        if token_in and not token_in.startswith('0x'):
            token_in_symbol = token_in  # Store the symbol
            # Try to find in FLARE_TOKENS first
            if token_in in FLARE_TOKENS:
                token_in = FLARE_TOKENS[token_in]
            # Then try KINETIC_TOKENS
            elif token_in in KINETIC_TOKENS:
                token_in = KINETIC_TOKENS[token_in]
            else:
                return {
                    "success": False,
                    "message": f"Could not resolve token name '{token_in}' to an address",
                    "token_in": token_in,
                    "token_out": token_out
                }
        else:
            # Find token symbol by address
            for name, address in {**FLARE_TOKENS, **KINETIC_TOKENS}.items():
                if address.lower() == token_in.lower():
                    token_in_symbol = name
                    break
        
        # Check if token_out is a name rather than an address
        if token_out and not token_out.startswith('0x'):
            token_out_symbol = token_out  # Store the symbol
            # Try to find in FLARE_TOKENS first
            if token_out in FLARE_TOKENS:
                token_out = FLARE_TOKENS[token_out]
            # Then try KINETIC_TOKENS
            elif token_out in KINETIC_TOKENS:
                token_out = KINETIC_TOKENS[token_out]
            else:
                return {
                    "success": False,
                    "message": f"Could not resolve token name '{token_out}' to an address",
                    "token_in": token_in_symbol if token_in_symbol else token_in,
                    "token_out": token_out
                }
        else:
            # Find token symbol by address
            for name, address in {**FLARE_TOKENS, **KINETIC_TOKENS}.items():
                if address.lower() == token_out.lower():
                    token_out_symbol = name
                    break
        
        # Display names for logging
        token_in_display = token_in_symbol if token_in_symbol else token_in
        token_out_display = token_out_symbol if token_out_symbol else token_out
        
        # Call the swap function
        try:
            log_message = f"🔧 FUNCTION CALL: swap_tokens\n"
            log_message += f"Parameters:\n"
            log_message += f"  - token_in: {token_in_display} ({token_in})\n"
            log_message += f"  - token_out: {token_out_display} ({token_out})\n"
            log_message += f"  - amount_in_eth: {amount_in_eth}\n"
            
            if fee is not None:
                log_message += f"  - fee: {fee} ({fee/10000}%)\n"
            else:
                log_message += f"  - fee: Auto-select (will find pool with most liquidity)\n"
            
            log_message += f"\n🚀 Executing swap on blockchain: {amount_in_eth} {token_in_display} to {token_out_display}\n"
            
            # Add this log message to the session state
            if "tool_logs" not in st.session_state:
                st.session_state.tool_logs = []
            st.session_state.tool_logs.append(log_message)
            
            # Create a placeholder for real-time stdout display
            if "realtime_output_container" in st.session_state:
                # Clear any previous content
                st.session_state.realtime_output_container.empty()
                
                # Display initial message in the real-time output container
                initial_message = f"Starting swap: {amount_in_eth} {token_in_display} → {token_out_display}\n"
                if fee is not None:
                    initial_message += f"Using fee tier: {fee/10000}%\n"
                else:
                    initial_message += f"Auto-selecting fee tier based on liquidity\n"
                
                initial_placeholder = st.session_state.realtime_output_container.empty()
                initial_placeholder.markdown(f"```\n{initial_message}\n```")
                
                # Create a new placeholder for function output
                stdout_placeholder = st.session_state.realtime_output_container.empty()
                
                # Set up stdout redirection
                original_stdout = sys.stdout
                stdout_redirector = StreamlitStdoutRedirector(stdout_placeholder)
                sys.stdout = stdout_redirector
                
                try:
                    # Execute the swap with redirected stdout
                    result = swap_tokens(token_in, token_out, amount_in_eth, fee)
                    
                    # Capture the final stdout content
                    stdout_content = stdout_redirector.get_value()
                    
                    # Add the stdout content to the logs (but don't display in UI)
                    if stdout_content:
                        st.session_state.tool_logs.append(stdout_content)
                finally:
                    # Restore original stdout
                    sys.stdout = original_stdout
            else:
                # Fallback if realtime_output_container is not available
                result = swap_tokens(token_in, token_out, amount_in_eth, fee)
            
            if result:
                tx_hash = result.get("transactionHash", "")
                if hasattr(tx_hash, "hex"):
                    tx_hash = tx_hash.hex()
                else:
                    tx_hash = str(tx_hash)
                
                success_message = {
                    "success": True,
                    "message": f"Successfully swapped {amount_in_eth} {token_in_display} for {token_out_display}",
                    "transaction_hash": tx_hash,
                    "explorer_url": format_tx_hash_as_link(tx_hash),
                    "token_in": token_in_display,
                    "token_out": token_out_display
                }
                
                # Add the result to the logs
                result_log = f"✅ Swap successful!\n"
                result_log += f"Transaction hash: {format_tx_hash_as_link(tx_hash)}\n"
                st.session_state.tool_logs.append(result_log)
                
                # Display success message in the real-time output container if available
                if "realtime_output_container" in st.session_state:
                    success_placeholder = st.session_state.realtime_output_container.empty()
                    success_placeholder.markdown(f"""```
✅ Swap successful!
```
**Transaction Hash**: {format_tx_hash_as_link(tx_hash)}
""", unsafe_allow_html=True)
                
                return success_message
            else:
                failure_message = {
                    "success": False,
                    "message": f"Swap failed. Check logs for detailed error messages.",
                    "token_in": token_in_display,
                    "token_out": token_out_display
                }
                
                # Add the failure to the logs
                failure_log = f"❌ Swap failed! No transaction hash returned.\n"
                st.session_state.tool_logs.append(failure_log)
                
                # Display failure message in the real-time output container if available
                if "realtime_output_container" in st.session_state:
                    failure_placeholder = st.session_state.realtime_output_container.empty()
                    failure_placeholder.markdown(f"""```
❌ Swap failed! No transaction hash returned.
```""")
                
                return failure_message
        except Exception as e:
            # Restore original stdout if exception occurs
            if 'original_stdout' in locals():
                sys.stdout = original_stdout
                
            error_message = {
                "success": False,
                "message": f"Error executing swap: {str(e)}",
                "token_in": token_in_display,
                "token_out": token_out_display
            }
            
            # Add the error to the logs
            error_log = f"❌ Error executing swap:\n{str(e)}\n"
            error_log += traceback.format_exc()
            st.session_state.tool_logs.append(error_log)
            
            # Display error message in the real-time output container if available
            if "realtime_output_container" in st.session_state:
                error_placeholder = st.session_state.realtime_output_container.empty()
                error_placeholder.markdown(f"""```
❌ Error executing swap:
{str(e)}
```""")
            
            return error_message
    else:
        # Unknown function
        unknown_function_message = {
            "success": False,
            "message": f"Unknown function: {function_call.name}"
        }
        
        # Add the error to the logs
        unknown_log = f"❓ Unknown function call detected: {function_call.name}\n"
        st.session_state.tool_logs.append(unknown_log)
        
        return unknown_function_message

def generate_response(prompt, model_name="models/gemini-2.0-flash"):
    """Generate a response from Gemini with function calling capabilities"""
    if not GEMINI_API_KEY:
        yield "Error: Gemini API key is missing. Please add it to your .env file as GEMINI_API_KEY=your_api_key_here"
        return
    
    try:
        # Create a tool with the function declaration
        swap_tool = Tool(function_declarations=[swap_function])
        
        # Initialize the Gemini model with function calling capability
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=SYSTEM_PROMPT,
            tools=[swap_tool]
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
                                    final_response = chat.send_message(function_response, stream=False)
                                    
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
                                    final_text = final_response.text
                                    
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
                final_response = chat.send_message(function_response, stream=False)
                
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
                final_text = final_response.text
                
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

# Initialize session state for storing messages and settings
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize tool logs
if "tool_logs" not in st.session_state:
    st.session_state.tool_logs = []

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
    
    # Add TEE Attestation section
    st.subheader("TEE Attestation")
    
    # Initialize attestation state if not exists
    if "attestation_token" not in st.session_state:
        st.session_state.attestation_token = None
        st.session_state.attestation_status = None
        st.session_state.attestation_message = None
        st.session_state.attestation_claims = None
        st.session_state.attestation_debug = None
    
    # Display simulation status
    with st.expander("TEE Attestation", expanded=False):
        is_simulated = os.environ.get("SIMULATE_ATTESTATION", "false").lower() == "true"
        if is_simulated:
            st.info("⚠️ Running in simulation mode (SIMULATE_ATTESTATION=true)")
        else:
            st.info("🔒 Running in real TEE attestation mode (SIMULATE_ATTESTATION=false)")
        
        # Check if we're running in a TEE environment
        in_tee = is_running_in_tee()
        
        if not in_tee and not is_simulated:
            st.warning("⚠️ Not running in a TEE environment. TEE socket not found.")
            st.markdown("""
            To run in a TEE environment:
            1. Make sure you're running in a Confidential VM with TEE support
            2. Make sure the container has access to the TEE socket
            3. Or set SIMULATE_ATTESTATION=true for testing
            """)
        
        # Add Generate Attestation button
        if st.button("Generate Attestation"):
            with st.spinner("Generating and verifying TEE attestation..."):
                success, message, token, claims = generate_and_verify_attestation()
                st.session_state.attestation_status = success
                st.session_state.attestation_message = message
                st.session_state.attestation_token = token
                st.session_state.attestation_claims = claims
                
                # Store debug information
                debug_info = {
                    "simulation_mode": is_simulated,
                    "in_tee_environment": in_tee,
                    "token_length": len(token) if token else 0,
                    "has_claims": claims is not None,
                    "claims_keys": list(claims.keys()) if claims else []
                }
                
                # Display the result
                if success:
                    st.success(message)
                    
                    # Display token information
                    st.subheader("Attestation Token Information")
                    
                    # Display issuer
                    issuer = claims.get("iss", "Unknown")
                    st.write(f"**Issuer:** {issuer}")
                    
                    # Display audience
                    audience = claims.get("aud", "Unknown")
                    st.write(f"**Audience:** {audience}")
                    
                    # Display timestamps
                    iat = claims.get("iat")
                    if iat:
                        iat_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(iat))
                        st.write(f"**Issued at:** {iat_time}")
                    
                    exp = claims.get("exp")
                    if exp:
                        exp_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(exp))
                        st.write(f"**Expires at:** {exp_time}")
                    
                    # Display nonces if present
                    nonces = claims.get("nonces", [])
                    if nonces:
                        st.write("**Nonces in token:**")
                        for nonce in nonces:
                            st.code(nonce)
                        
                        # Check if message indicates nonce verification failed
                        if "nonce verification failed" in message:
                            st.warning("⚠️ The attestation token was generated successfully, but the nonce verification failed. This means the token is valid but might not have been generated specifically for this request.")
                    else:
                        st.warning("⚠️ No nonces found in the attestation token. This is unusual but the token is still valid for basic attestation purposes.")
                    
                    # Display full claims in an expander
                    with st.expander("View Full Claims"):
                        st.json(claims)
                    
                    # Display token in an expander
                    with st.expander("View Raw Token"):
                        st.code(token)
                        
                    # Add Debug Token button
                    if st.button("Debug Token Structure"):
                        try:
                            # Split the token into its parts
                            token_parts = token.split('.')
                            if len(token_parts) == 3:
                                header_b64, payload_b64, signature_b64 = token_parts
                                
                                # Decode header
                                # Add padding if needed
                                header_b64 += '=' * ((4 - len(header_b64) % 4) % 4)
                                header_json = base64.urlsafe_b64decode(header_b64).decode('utf-8')
                                header = json.loads(header_json)
                                
                                # Decode payload
                                # Add padding if needed
                                payload_b64 += '=' * ((4 - len(payload_b64) % 4) % 4)
                                payload_json = base64.urlsafe_b64decode(payload_b64).decode('utf-8')
                                payload = json.loads(payload_json)
                                
                                # Display decoded parts
                                st.subheader("Token Structure")
                                
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.write("**Header:**")
                                    st.json(header)
                                
                                with col2:
                                    st.write("**Signature (first 20 chars):**")
                                    st.code(signature_b64[:20] + "...")
                                
                                st.write("**Payload (Decoded Claims):**")
                                st.json(payload)
                                
                                # Display any additional fields that might be of interest
                                if "tee" in payload:
                                    st.subheader("TEE-Specific Claims")
                                    st.json(payload["tee"])
                                
                                # Check for any nested structures and display them
                                for key, value in payload.items():
                                    if isinstance(value, dict) and key != "tee":
                                        st.subheader(f"{key.capitalize()} Details")
                                        st.json(value)
                            else:
                                st.error("Invalid token format. Expected 3 parts (header.payload.signature)")
                        except Exception as e:
                            st.error(f"Error decoding token: {str(e)}")
                            st.code(traceback.format_exc())
                else:
                    st.error(message)
                    
                    # Show more detailed debug information
                    with st.expander("Debug Information"):
                        st.write("**Token (first 100 chars):**", token[:100] if token else "None")
                        
                        if claims:
                            st.write("**Claims:**")
                            st.json(claims)
                        
                        st.write("**Debug Info:**")
                        st.json(debug_info)
                        
                        # Provide troubleshooting guidance
                        st.markdown("""
                        ### Troubleshooting Tips:
                        
                        1. **Check if you're running in a real TEE environment**
                           - Make sure you're running in a Confidential VM with TEE support
                           - Verify that the container has access to the TEE socket
                        
                        2. **Check environment variables**
                           - Ensure SIMULATE_ATTESTATION is set correctly
                        
                        3. **Check socket path**
                           - The default socket path is `/run/container_launcher/teeserver.sock`
                           - Make sure this path exists and is accessible
                           
                        4. **Try simulation mode**
                           - Set SIMULATE_ATTESTATION=true to test in simulation mode
                        """)
    
    # Chat Statistics
    st.subheader("Chat Statistics")
    st.write(f"Messages: {len(st.session_state.messages)}")
    
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.experimental_rerun()

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