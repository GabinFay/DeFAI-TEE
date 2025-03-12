import streamlit as st
import sys
import time
import traceback
import json
from io import StringIO
from datetime import datetime
from web3 import Web3
from eth_account import Account
from web3.middleware import geth_poa_middleware
import threading  # Add this import
import os

# Import the real swap function
try:
    from flare_uniswap_sdk_swap import swap_tokens
except ImportError:
    raise ImportError("Could not import swap_tokens function. Make sure the flare_uniswap_sdk_swap module is in your Python path.")

# Import token data
from tools import get_flare_tokens, get_kinetic_tokens

# Create a function that will be set from outside
fetch_and_display_balances = lambda: None  # Default no-op function

def set_balance_updater(balance_updater_func):
    """Set the balance updater function from outside"""
    global fetch_and_display_balances
    fetch_and_display_balances = balance_updater_func

# Get token addresses from the tools module
FLARE_TOKENS = get_flare_tokens()
KINETIC_TOKENS = get_kinetic_tokens()

# ERC20 Token ABI (only the necessary parts)
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
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

# WFLR (Wrapped FLR) ABI - includes deposit function for wrapping
WFLR_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
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
    {
        "constant": False,
        "inputs": [],
        "name": "deposit",
        "outputs": [],
        "payable": True,
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [{"name": "wad", "type": "uint256"}],
        "name": "withdraw",
        "outputs": [],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

# WFLR contract address on Flare network
WFLR_ADDRESS = "0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d"

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
            # Use HTML pre tag instead of markdown code block for better formatting
            self.placeholder.markdown(f"<pre>{content}</pre>", unsafe_allow_html=True)
    
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
    


# Add these new handler functions for wrap and unwrap operations
def handle_wrap_flr(args):
    """Handle wrapping native FLR to WFLR"""
    amount_flr = args.get("amount_flr")
    
    if not amount_flr:
        return {
            "success": False,
            "message": "Amount of FLR to wrap is required"
        }
    
    try:
        log_message = f"🔧 FUNCTION CALL: wrap_flr\n"
        log_message += f"Parameters:\n"
        log_message += f"  - amount_flr: {amount_flr} (type: {type(amount_flr)})\n"
        log_message += f"\n🚀 Executing wrap operation: {amount_flr} FLR to WFLR\n"
        
        # Add this log message to the session state
        if "tool_logs" not in st.session_state:
            st.session_state.tool_logs = []
        st.session_state.tool_logs.append(log_message)
        
        # Create a placeholder for real-time stdout display
        if "realtime_output_container" in st.session_state:
            # Clear any previous content
            st.session_state.realtime_output_container.empty()
            
            # Display initial message in the real-time output container
            initial_message = f"Starting wrap operation: {amount_flr} FLR → WFLR\n"
            initial_placeholder = st.session_state.realtime_output_container.empty()
            initial_placeholder.markdown(f"<pre>{initial_message}</pre>", unsafe_allow_html=True)
            
            # Create a new placeholder for function output
            stdout_placeholder = st.session_state.realtime_output_container.empty()
            
            # Set up stdout redirection
            original_stdout = sys.stdout
            stdout_redirector = StreamlitStdoutRedirector(stdout_placeholder)
            sys.stdout = stdout_redirector
            
            try:
                # Import and use the wrap_flare function from wrap_flare.py
                from wrap_flare import wrap_flare
                
                # Check for private key in session state or environment variables
                private_key = None
                if st.session_state.get("private_key"):
                    print("Using private key from session state")
                    private_key = st.session_state.private_key
                else:
                    # Try to get from environment variables
                    env_private_key = os.getenv("PRIVATE_KEY")
                    if env_private_key:
                        print("Using private key from environment variables")
                        private_key = env_private_key
                    else:
                        raise Exception("Private key is not available. Please connect your wallet or set PRIVATE_KEY in .env file.")
                
                # Derive wallet address from private key
                account = Account.from_key(private_key)
                wallet_address = account.address
                print(f"Derived wallet address from private key: {wallet_address}")
                
                # Set environment variables for wrap_flare
                os.environ["FLARE_RPC_URL"] = st.session_state.get("rpc_url", os.getenv("FLARE_RPC_URL"))
                os.environ["WALLET_ADDRESS"] = wallet_address
                os.environ["PRIVATE_KEY"] = private_key
                
                # Validate amount_flr
                try:
                    # Convert amount_flr to float if it's a string
                    if isinstance(amount_flr, str):
                        amount_flr = float(amount_flr)
                    
                    # Ensure amount_flr is a number
                    if not isinstance(amount_flr, (int, float)):
                        raise Exception(f"Amount must be a number, got {type(amount_flr)}")
                    
                    print(f"Validated amount: {amount_flr} FLR")
                except Exception as e:
                    raise Exception(f"Invalid amount: {str(e)}")
                
                # Call the wrap_flare function
                print(f"Calling wrap_flare with amount: {amount_flr}")
                tx_receipt = wrap_flare(amount_flr)
                
                # Check if tx_receipt is None
                if tx_receipt is None:
                    raise Exception("Transaction failed or was rejected. Check the logs for details.")
                
                # Get transaction hash
                try:
                    if hasattr(tx_receipt.transactionHash, 'hex'):
                        tx_hash_hex = tx_receipt.transactionHash.hex()
                    else:
                        # If it's already a string, use it directly
                        tx_hash_hex = str(tx_receipt.transactionHash)
                    
                    # Clean up the hash if it has byte string markers
                    if tx_hash_hex.startswith("b'") and tx_hash_hex.endswith("'"):
                        tx_hash_hex = tx_hash_hex[2:-1]
                    
                    # Remove any backslashes or escape characters
                    tx_hash_hex = tx_hash_hex.replace('\\x', '')
                    
                    print(f"Transaction hash: {tx_hash_hex}")
                except Exception as e:
                    raise Exception(f"Failed to get transaction hash: {str(e)}. Receipt: {tx_receipt}")
                
                # Capture the final stdout content
                stdout_content = stdout_redirector.get_value()
                
                # Add the stdout content to the logs
                if stdout_content:
                    st.session_state.tool_logs.append(stdout_content)
            except Exception as e:
                # Restore original stdout
                sys.stdout = original_stdout
                
                # Re-raise the exception to be caught by the outer try-except
                raise Exception(f"Wrap operation failed: {str(e)}")
            finally:
                # Restore original stdout
                sys.stdout = original_stdout
                
            success_message = {
                "success": True,
                "message": f"Successfully wrapped {amount_flr} FLR to WFLR",
                "transaction_hash": tx_hash_hex,
                "explorer_url": format_tx_hash_as_link(tx_hash_hex)
            }
            
            # Add the result to the logs
            result_log = f"✅ Wrap operation successful!\n"
            result_log += f"Transaction hash: {format_tx_hash_as_link(tx_hash_hex)}\n"
            st.session_state.tool_logs.append(result_log)
            
            # Display success message in the real-time output container
            success_placeholder = st.session_state.realtime_output_container.empty()
            success_placeholder.markdown(f"""<pre>
✅ Wrap operation successful!
</pre>
**Transaction Hash**: {format_tx_hash_as_link(tx_hash_hex)}
""", unsafe_allow_html=True)
            
            # Update token balances after successful wrap
            # fetch_and_display_balances()
            
            return success_message
        else:
            # Import and use the wrap_flare function from wrap_flare.py
            from wrap_flare import wrap_flare
            
            # Check for private key in session state or environment variables
            private_key = None
            if st.session_state.get("private_key"):
                print("Using private key from session state")
                private_key = st.session_state.private_key
            else:
                # Try to get from environment variables
                env_private_key = os.getenv("PRIVATE_KEY")
                if env_private_key:
                    print("Using private key from environment variables")
                    private_key = env_private_key
                else:
                    raise Exception("Private key is not available. Please connect your wallet or set PRIVATE_KEY in .env file.")
            
            # Derive wallet address from private key
            account = Account.from_key(private_key)
            wallet_address = account.address
            print(f"Derived wallet address from private key: {wallet_address}")
            
            # Set environment variables for wrap_flare
            os.environ["FLARE_RPC_URL"] = st.session_state.get("rpc_url", os.getenv("FLARE_RPC_URL"))
            os.environ["WALLET_ADDRESS"] = wallet_address
            os.environ["PRIVATE_KEY"] = private_key
            
            # Validate amount_flr
            try:
                # Convert amount_flr to float if it's a string
                if isinstance(amount_flr, str):
                    amount_flr = float(amount_flr)
                
                # Ensure amount_flr is a number
                if not isinstance(amount_flr, (int, float)):
                    raise Exception(f"Amount must be a number, got {type(amount_flr)}")
                
                print(f"Validated amount: {amount_flr} FLR")
            except Exception as e:
                raise Exception(f"Invalid amount: {str(e)}")
            
            # Call the wrap_flare function
            print(f"Calling wrap_flare with amount: {amount_flr}")
            tx_receipt = wrap_flare(float(amount_flr))
            
            # Check if tx_receipt is None
            if tx_receipt is None:
                raise Exception("Transaction failed or was rejected. Check the logs for details.")
            
            # Get transaction hash
            try:
                if hasattr(tx_receipt.transactionHash, 'hex'):
                    tx_hash_hex = tx_receipt.transactionHash.hex()
                else:
                    # If it's already a string, use it directly
                    tx_hash_hex = str(tx_receipt.transactionHash)
                
                # Clean up the hash if it has byte string markers
                if tx_hash_hex.startswith("b'") and tx_hash_hex.endswith("'"):
                    tx_hash_hex = tx_hash_hex[2:-1]
                
                # Remove any backslashes or escape characters
                tx_hash_hex = tx_hash_hex.replace('\\x', '')
                
                print(f"Transaction hash: {tx_hash_hex}")
            except Exception as e:
                raise Exception(f"Failed to get transaction hash: {str(e)}. Receipt: {tx_receipt}")
            
            success_message = {
                "success": True,
                "message": f"Successfully wrapped {amount_flr} FLR to WFLR",
                "transaction_hash": tx_hash_hex,
                "explorer_url": format_tx_hash_as_link(tx_hash_hex)
            }
            
            # Update token balances after successful wrap
            # fetch_and_display_balances()
            
            return success_message
    except Exception as e:
        # Restore original stdout if exception occurs
        if 'original_stdout' in locals():
            sys.stdout = original_stdout
            
        error_message = {
            "success": False,
            "message": f"Error executing wrap operation: {str(e)}"
        }
        
        # Add the error to the logs
        error_log = f"❌ Error executing wrap operation:\n{str(e)}\n"
        if 'traceback' in sys.modules:
            import traceback
            error_log += traceback.format_exc()
        st.session_state.tool_logs.append(error_log)
        
        # Display error message in the real-time output container if available
        if "realtime_output_container" in st.session_state:
            error_placeholder = st.session_state.realtime_output_container.empty()
            error_placeholder.markdown(f"""<pre>
❌ Error executing wrap operation:
{str(e)}
</pre>""", unsafe_allow_html=True)
        
        return error_message

def handle_unwrap_wflr(args):
    """Handle unwrapping WFLR to native FLR"""
    amount_wflr = args.get("amount_wflr")
    
    if not amount_wflr:
        return {
            "success": False,
            "message": "Amount of WFLR to unwrap is required"
        }
    
    try:
        log_message = f"🔧 FUNCTION CALL: unwrap_wflr\n"
        log_message += f"Parameters:\n"
        log_message += f"  - amount_wflr: {amount_wflr}\n"
        log_message += f"\n🚀 Executing unwrap operation: {amount_wflr} WFLR to FLR\n"
        
        # Add this log message to the session state
        if "tool_logs" not in st.session_state:
            st.session_state.tool_logs = []
        st.session_state.tool_logs.append(log_message)
        
        # Create a placeholder for real-time stdout display
        if "realtime_output_container" in st.session_state:
            # Clear any previous content
            st.session_state.realtime_output_container.empty()
            
            # Display initial message in the real-time output container
            initial_message = f"Starting unwrap operation: {amount_wflr} WFLR → FLR\n"
            initial_placeholder = st.session_state.realtime_output_container.empty()
            initial_placeholder.markdown(f"<pre>{initial_message}</pre>", unsafe_allow_html=True)
            
            # Create a new placeholder for function output
            stdout_placeholder = st.session_state.realtime_output_container.empty()
            
            # Set up stdout redirection
            original_stdout = sys.stdout
            stdout_redirector = StreamlitStdoutRedirector(stdout_placeholder)
            sys.stdout = stdout_redirector
            
            try:
                # Import and use the unwrap_flare function from unwrap_flare.py
                from unwrap_flare import unwrap_flare
                
                # Check for private key in session state or environment variables
                private_key = None
                if st.session_state.get("private_key"):
                    print("Using private key from session state")
                    private_key = st.session_state.private_key
                else:
                    # Try to get from environment variables
                    env_private_key = os.getenv("PRIVATE_KEY")
                    if env_private_key:
                        print("Using private key from environment variables")
                        private_key = env_private_key
                    else:
                        raise Exception("Private key is not available. Please connect your wallet or set PRIVATE_KEY in .env file.")
                
                # Derive wallet address from private key
                account = Account.from_key(private_key)
                wallet_address = account.address
                print(f"Derived wallet address from private key: {wallet_address}")
                
                # Set environment variables for unwrap_flare
                os.environ["FLARE_RPC_URL"] = st.session_state.get("rpc_url", os.getenv("FLARE_RPC_URL"))
                os.environ["WALLET_ADDRESS"] = wallet_address
                os.environ["PRIVATE_KEY"] = private_key
                
                # Validate amount_wflr
                try:
                    # Convert amount_wflr to float if it's a string
                    if isinstance(amount_wflr, str):
                        amount_wflr = float(amount_wflr)
                    
                    # Ensure amount_wflr is a number
                    if not isinstance(amount_wflr, (int, float)):
                        raise Exception(f"Amount must be a number, got {type(amount_wflr)}")
                    
                    print(f"Validated amount: {amount_wflr} WFLR")
                except Exception as e:
                    raise Exception(f"Invalid amount: {str(e)}")
                
                # Call the unwrap_flare function
                print(f"Calling unwrap_flare with amount: {amount_wflr}")
                tx_receipt = unwrap_flare(float(amount_wflr))
                
                if tx_receipt is None:
                    raise Exception("Transaction failed or was rejected. Check the logs for details.")
                
                # Get transaction hash
                try:
                    if hasattr(tx_receipt.transactionHash, 'hex'):
                        tx_hash_hex = tx_receipt.transactionHash.hex()
                    else:
                        # If it's already a string, use it directly
                        tx_hash_hex = str(tx_receipt.transactionHash)
                    
                    # Clean up the hash if it has byte string markers
                    if tx_hash_hex.startswith("b'") and tx_hash_hex.endswith("'"):
                        tx_hash_hex = tx_hash_hex[2:-1]
                    
                    # Remove any backslashes or escape characters
                    tx_hash_hex = tx_hash_hex.replace('\\x', '')
                    
                    print(f"Transaction hash: {tx_hash_hex}")
                except Exception as e:
                    raise Exception(f"Failed to get transaction hash: {str(e)}. Receipt: {tx_receipt}")
                
                # Capture the final stdout content
                stdout_content = stdout_redirector.get_value()
                
                # Add the stdout content to the logs
                if stdout_content:
                    st.session_state.tool_logs.append(stdout_content)
            except Exception as e:
                # Restore original stdout
                sys.stdout = original_stdout
                
                # Re-raise the exception to be caught by the outer try-except
                raise Exception(f"Unwrap operation failed: {str(e)}")
            finally:
                # Restore original stdout
                sys.stdout = original_stdout
                
            success_message = {
                "success": True,
                "message": f"Successfully unwrapped {amount_wflr} WFLR to FLR",
                "transaction_hash": tx_hash_hex,
                "explorer_url": format_tx_hash_as_link(tx_hash_hex)
            }
            
            # Add the result to the logs
            result_log = f"✅ Unwrap operation successful!\n"
            result_log += f"Transaction hash: {format_tx_hash_as_link(tx_hash_hex)}\n"
            st.session_state.tool_logs.append(result_log)
            
            # Display success message in the real-time output container
            success_placeholder = st.session_state.realtime_output_container.empty()
            success_placeholder.markdown(f"""<pre>
✅ Unwrap operation successful!
</pre>
**Transaction Hash**: {format_tx_hash_as_link(tx_hash_hex)}
""", unsafe_allow_html=True)
            
            # Update token balances after successful unwrap
            # fetch_and_display_balances()
            
            return success_message
        else:
            # Import and use the unwrap_flare function from unwrap_flare.py
            from unwrap_flare import unwrap_flare
            
            # Check for private key in session state or environment variables
            private_key = None
            if st.session_state.get("private_key"):
                print("Using private key from session state")
                private_key = st.session_state.private_key
            else:
                # Try to get from environment variables
                env_private_key = os.getenv("PRIVATE_KEY")
                if env_private_key:
                    print("Using private key from environment variables")
                    private_key = env_private_key
                else:
                    raise Exception("Private key is not available. Please connect your wallet or set PRIVATE_KEY in .env file.")
            
            # Derive wallet address from private key
            account = Account.from_key(private_key)
            wallet_address = account.address
            print(f"Derived wallet address from private key: {wallet_address}")
            
            # Set environment variables for unwrap_flare
            os.environ["FLARE_RPC_URL"] = st.session_state.get("rpc_url", os.getenv("FLARE_RPC_URL"))
            os.environ["WALLET_ADDRESS"] = wallet_address
            os.environ["PRIVATE_KEY"] = private_key
            
            # Validate amount_wflr
            try:
                # Convert amount_wflr to float if it's a string
                if isinstance(amount_wflr, str):
                    amount_wflr = float(amount_wflr)
                
                # Ensure amount_wflr is a number
                if not isinstance(amount_wflr, (int, float)):
                    raise Exception(f"Amount must be a number, got {type(amount_wflr)}")
                
                print(f"Validated amount: {amount_wflr} WFLR")
            except Exception as e:
                raise Exception(f"Invalid amount: {str(e)}")
            
            # Call the unwrap_flare function
            print(f"Calling unwrap_flare with amount: {amount_wflr}")
            tx_receipt = unwrap_flare(float(amount_wflr))
            
            if tx_receipt is None:
                raise Exception("Transaction failed or was rejected. Check the logs for details.")
            
            # Get transaction hash
            try:
                if hasattr(tx_receipt.transactionHash, 'hex'):
                    tx_hash_hex = tx_receipt.transactionHash.hex()
                else:
                    # If it's already a string, use it directly
                    tx_hash_hex = str(tx_receipt.transactionHash)
                
                # Clean up the hash if it has byte string markers
                if tx_hash_hex.startswith("b'") and tx_hash_hex.endswith("'"):
                    tx_hash_hex = tx_hash_hex[2:-1]
                
                # Remove any backslashes or escape characters
                tx_hash_hex = tx_hash_hex.replace('\\x', '')
                
                print(f"Transaction hash: {tx_hash_hex}")
            except Exception as e:
                raise Exception(f"Failed to get transaction hash: {str(e)}. Receipt: {tx_receipt}")
            
            success_message = {
                "success": True,
                "message": f"Successfully unwrapped {amount_wflr} WFLR to FLR",
                "transaction_hash": tx_hash_hex,
                "explorer_url": format_tx_hash_as_link(tx_hash_hex)
            }
            
            # Update token balances after successful unwrap
            # fetch_and_display_balances()
            
            return success_message
    except Exception as e:
        # Restore original stdout if exception occurs
        if 'original_stdout' in locals():
            sys.stdout = original_stdout
            
        error_message = {
            "success": False,
            "message": f"Error executing unwrap operation: {str(e)}"
        }
        
        # Add the error to the logs
        error_log = f"❌ Error executing unwrap operation:\n{str(e)}\n"
        if 'traceback' in sys.modules:
            import traceback
            error_log += traceback.format_exc()
        st.session_state.tool_logs.append(error_log)
        
        # Display error message in the real-time output container if available
        if "realtime_output_container" in st.session_state:
            error_placeholder = st.session_state.realtime_output_container.empty()
            error_placeholder.markdown(f"""<pre>
❌ Error executing unwrap operation:
{str(e)}
</pre>""", unsafe_allow_html=True)
        
        return error_message

def handle_lending_strategy(args):
    """Handle lending strategy recommendations"""
    risk_profile = args.get("risk_profile", "").lower()
    experience_level = args.get("experience_level", "").lower()
    investment_amount = args.get("investment_amount", "")
    
    # Load pool data from JSON file
    try:
        with open("flare-bot/pool_data.json", "r") as f:
            pool_data = json.load(f)
    except Exception as e:
        return f"Error loading pool data: {str(e)}"
    
    # Filter pools based on risk profile
    if risk_profile == "low":
        recommended_pools = [pool for pool in pool_data if pool["risk_level"] in ["low"]]
        allocation = "70-80% in low-risk pools, 20-30% in medium-risk pools"
        strategy_type = "Conservative strategy"
    elif risk_profile == "medium":
        recommended_pools = [pool for pool in pool_data if pool["risk_level"] in ["medium", "low-medium"]]
        allocation = "40% in low-risk, 40% in medium-risk, 20% in high-risk pools"
        strategy_type = "Balanced strategy"
    elif risk_profile == "high":
        recommended_pools = [pool for pool in pool_data if pool["risk_level"] in ["high", "medium-high"]]
        allocation = "50-60% in high-risk pools, 40-50% in medium-risk pools"
        strategy_type = "Aggressive strategy"
    else:
        return "Please specify a valid risk profile: low, medium, or high."
    
    # Sort pools by APY (descending)
    recommended_pools = sorted(recommended_pools, key=lambda x: float(x["apy"].strip("+%")), reverse=True)
    
    # Build response
    response = f"## {strategy_type} for {risk_profile.capitalize()} Risk Profile\n\n"
    
    if experience_level:
        if experience_level == "beginner":
            response += "As a beginner, focus on more stable pools with lower risk of impermanent loss.\n\n"
        elif experience_level == "intermediate":
            response += "With some experience, you can balance between stable returns and higher yield opportunities.\n\n"
        elif experience_level == "experienced":
            response += "As an experienced DeFi user, you can optimize for higher yields while managing risks.\n\n"
    
    response += f"**Recommended Allocation:** {allocation}\n\n"
    
    if investment_amount:
        response += f"**Investment Amount:** {investment_amount}\n\n"
    
    response += "**Top Recommended Pools:**\n\n"
    
    for pool in recommended_pools[:3]:
        response += f"- **{pool['pool']}**\n"
        response += f"  - APY: {pool['apy']}\n"
        response += f"  - Liquidity: {pool['liquidity']}\n"
        response += f"  - Fee: {pool['fee']}\n"
        response += f"  - Address: {pool['address']}\n\n"
    
    response += "**Key Considerations:**\n"
    response += "- Higher APY typically comes with higher risk\n"
    response += "- Consider impermanent loss risk for volatile pairs\n"
    response += "- Pools with lower liquidity may have higher slippage\n"
    response += "- Diversify across different asset types for better risk management\n"
    
    return response

def handle_swap(args):
    # Parse arguments
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
            initial_placeholder.markdown(f"<pre>{initial_message}</pre>", unsafe_allow_html=True)
            
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
                success_placeholder.markdown(f"""<pre>
✅ Swap successful!
</pre>
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
                failure_placeholder.markdown(f"""<pre>
❌ Swap failed! No transaction hash returned.
</pre>""", unsafe_allow_html=True)
            
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
            error_placeholder.markdown(f"""<pre>
❌ Error executing swap:
{str(e)}
</pre>""", unsafe_allow_html=True)
        
        return error_message

# Add these missing handler functions
def handle_add_liquidity(args):
    """Handle adding liquidity to a Uniswap V3 pool"""
    return {
        "success": False,
        "message": "Add liquidity functionality is not yet implemented"
    }

def handle_remove_liquidity(args):
    """Handle removing liquidity from a position"""
    return {
        "success": False,
        "message": "Remove liquidity functionality is not yet implemented"
    }

def handle_get_positions(args):
    """Handle getting liquidity positions"""
    return {
        "success": False,
        "message": "Get positions functionality is not yet implemented"
    }

def handle_get_token_balances(args):
    """Handle getting token balances"""
    # This would normally call fetch_and_display_balances
    # But for now, just return a placeholder response
    return {
        "success": True,
        "message": "Token balances retrieved",
        "balances": "Use the 'Refresh Balances' button in the sidebar to see your token balances"
    }

def handle_get_pool_info(args):
    """Handle getting pool information"""
    return {
        "success": False,
        "message": "Get pool info functionality is not yet implemented"
    }