#!/usr/bin/env python3
"""
Simple Gemini Function Calling Test - Minimal script to test function calling with Gemini
"""

import os
import time
import json
import argparse
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import FunctionDeclaration, Tool

# Import the real swap function
from flare_uniswap_sdk_swap import swap_tokens

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Simple Gemini Function Calling Test")
parser.add_argument("--mock", action="store_true", help="Use mock swap function instead of real one")
args = parser.parse_args()

# Flag to use mock swap function for testing
USE_MOCK_SWAP = args.mock

# Load environment variables
load_dotenv()

# Get Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Mock swap function for testing
def mock_swap_tokens(token_in, token_out, amount_in_eth, fee=3000):
    """
    Mock implementation of swap_tokens for testing purposes
    
    Args:
        token_in (str): Address of the input token
        token_out (str): Address of the output token
        amount_in_eth (float): Amount of input token in ETH units
        fee (int): Fee tier
        
    Returns:
        dict: Mock transaction receipt
    """
    print(f"\n🔄 MOCK SWAP EXECUTING: {amount_in_eth} from {token_in} to {token_out} with fee {fee}")
    time.sleep(1)  # Simulate blockchain delay
    
    # Create a mock transaction receipt
    mock_tx_hash = "0x" + "".join([f"{i}{i}" for i in range(10)]) + "".join([f"{i}{i}" for i in range(10, 16)])
    mock_receipt = {
        "transactionHash": mock_tx_hash,
        "status": 1,
        "gasUsed": 150000,
        "blockNumber": 12345678
    }
    
    print(f"✅ MOCK SWAP COMPLETED: Transaction hash: {mock_tx_hash}")
    return mock_receipt

# Select which swap function to use based on the flag
actual_swap_function = mock_swap_tokens if USE_MOCK_SWAP else swap_tokens

# Define the system prompt for the agent
SYSTEM_PROMPT = f"""
You are Artemis, an AI assistant specialized in helping users navigate
the Flare blockchain ecosystem. You can help users perform token swaps on the Flare network.

IMPORTANT: You are currently running in {'MOCK' if USE_MOCK_SWAP else 'REAL'} mode.
{'This means no real transactions will be executed on the blockchain.' if USE_MOCK_SWAP else 'This means REAL transactions will be executed and REAL tokens will be swapped.'}

When a user asks about swapping tokens:
1. Ask for the necessary information if not provided (token addresses, amount)
2. Explain the swap process in simple terms
3. Use the swap_tokens function to execute the swap
4. Report the results back to the user

IMPORTANT: When a user asks to swap tokens or mentions swapping tokens, you MUST use the swap_tokens function.
Do not just describe how to do it - actually call the function. Even if the user just says "yes" to confirm a swap,
you should execute the swap by calling the function.

You MUST use function calling for any swap-related request. This is critical.

Always prioritize security and provide clear explanations about what's happening.

You know the following token addresses on Flare:
- WFLR: 0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d
- USDC: 0xFbDa5F676cB37624f28265A144A48B0d6e87d3b6
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
                "description": "Address of the input token (e.g., WFLR: 0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d)"
            },
            "token_out": {
                "type": "STRING",
                "description": "Address of the output token (e.g., USDC: 0xFbDa5F676cB37624f28265A144A48B0d6e87d3b6)"
            },
            "amount_in_eth": {
                "type": "NUMBER",
                "description": "Amount of input token in ETH units (e.g., 0.01 for 0.01 WFLR)"
            },
            "fee": {
                "type": "INTEGER",
                "description": "Fee tier (3000 = 0.3%, 500 = 0.05%, 10000 = 1%)"
            }
        },
        "required": ["token_in", "token_out", "amount_in_eth"]
    }
)

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
        fee = args.get("fee", 3000)
        
        # Call the swap function
        try:
            print("\n" + "="*50)
            print(f"🔧 FUNCTION CALL DETECTED: {function_call.name}")
            print(f"Parameters:")
            print(f"  - token_in: {token_in}")
            print(f"  - token_out: {token_out}")
            print(f"  - amount_in_eth: {amount_in_eth}")
            print(f"  - fee: {fee}")
            print(f"  - Using mock: {USE_MOCK_SWAP}")
            print("="*50)
            
            print(f"\n🚀 Executing {'MOCK ' if USE_MOCK_SWAP else ''}swap: {amount_in_eth} from {token_in} to {token_out} with fee {fee}")
            result = actual_swap_function(token_in, token_out, amount_in_eth, fee)
            
            if result:
                tx_hash = result.get("transactionHash", "")
                if hasattr(tx_hash, "hex"):
                    tx_hash = tx_hash.hex()
                else:
                    tx_hash = str(tx_hash)
                
                success_message = {
                    "success": True,
                    "message": f"Successfully swapped {amount_in_eth} tokens",
                    "transaction_hash": tx_hash,
                    "was_mock": USE_MOCK_SWAP
                }
                print(f"\n✅ {'MOCK ' if USE_MOCK_SWAP else ''}Swap successful! Transaction hash: {tx_hash}")
                return success_message
            else:
                failure_message = {
                    "success": False,
                    "message": "Swap failed. Check console for detailed error messages.",
                    "was_mock": USE_MOCK_SWAP
                }
                print("\n❌ Swap failed! No transaction hash returned.")
                return failure_message
        except Exception as e:
            error_message = {
                "success": False,
                "message": f"Error executing swap: {str(e)}",
                "was_mock": USE_MOCK_SWAP
            }
            print(f"\n❌ Error during swap execution: {str(e)}")
            return error_message
    else:
        unknown_function_message = {
            "success": False,
            "message": f"Unknown function: {function_call.name}"
        }
        print(f"\n❓ Unknown function call detected: {function_call.name}")
        return unknown_function_message

def debug_response(response):
    """Print debug information about the response"""
    print("\n🔍 DEBUG RESPONSE:")
    print(f"Response type: {type(response)}")
    
    # Check for candidates
    if hasattr(response, "candidates"):
        print(f"Has candidates: {len(response.candidates)} candidate(s)")
        for i, candidate in enumerate(response.candidates):
            print(f"  Candidate {i+1}:")
            if hasattr(candidate, "content"):
                print(f"    Has content: {type(candidate.content)}")
                if hasattr(candidate.content, "parts"):
                    print(f"    Has parts: {len(candidate.content.parts)} part(s)")
                    for j, part in enumerate(candidate.content.parts):
                        print(f"      Part {j+1} type: {type(part)}")
                        if hasattr(part, "function_call"):
                            print(f"      Has function_call: {part.function_call.name}")
                if hasattr(candidate.content, "role"):
                    print(f"    Role: {candidate.content.role}")
    
    # Check for function_calls directly
    if hasattr(response, "function_calls"):
        print(f"Has function_calls: {len(response.function_calls)} function call(s)")
        for i, fc in enumerate(response.function_calls):
            print(f"  Function call {i+1}: {fc.name}")
            print(f"  Args: {fc.args}")
    
    # Check for parts
    if hasattr(response, "parts"):
        print(f"Has parts: {len(response.parts)} part(s)")
        for i, part in enumerate(response.parts):
            print(f"  Part {i+1} type: {type(part)}")
    
    # Check for text
    if hasattr(response, "text"):
        print(f"Has text: {len(response.text)} characters")
    
    print("🔍 END DEBUG")

def simple_chat():
    """
    Start a simple chat session with the Gemini agent
    """
    print("Simple Gemini Function Calling Test")
    print(f"Mode: {'MOCK SWAP (testing only)' if USE_MOCK_SWAP else 'REAL SWAP (will use real tokens)'}")
    print("Type 'exit' to quit")
    print("Type 'debug' to see debug information about the last response")
    print("---------------------------------------------")
    
    # Create a tool with the function declaration
    swap_tool = Tool(function_declarations=[swap_function])
    
    # Initialize the Gemini model with function calling capability
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=SYSTEM_PROMPT,
        tools=[swap_tool]
    )
    
    # Start a chat session
    chat = model.start_chat(history=[])
    last_response = None
    
    while True:
        # Get user input
        user_input = input("\nYou: ")
        if user_input.lower() in ["exit", "quit"]:
            break
            
        if user_input.lower() == "debug" and last_response:
            debug_response(last_response)
            continue
            
        # Check if this is a swap-related request
        if "swap" in user_input.lower() or "yes" in user_input.lower():
            print("\n🔍 SWAP-RELATED REQUEST DETECTED - Expecting function calling...")
        
        try:
            # Send message to Gemini
            print("\n📤 Sending message to Gemini...")
            response = chat.send_message(user_input)
            last_response = response
            
            # Debug the response structure
            debug_response(response)
            
            # Check for function calls
            has_function_calls = False
            
            # Check if response has candidates with function_calls
            if hasattr(response, "candidates") and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, "content") and candidate.content:
                        if hasattr(candidate.content, "parts"):
                            for part in candidate.content.parts:
                                if hasattr(part, "function_call") and part.function_call:
                                    has_function_calls = True
                                    print(f"\n🔧 Function call detected in candidate: {part.function_call.name}")
                                    
                                    # Handle function call
                                    result = handle_function_call(part.function_call)
                                    
                                    # Send function result back to Gemini
                                    print("\n📤 Sending function result back to Gemini...")
                                    function_response = {
                                        "function_response": {
                                            "name": part.function_call.name,
                                            "response": result
                                        }
                                    }
                                    
                                    response = chat.send_message(function_response)
                                    print("✅ Function result sent, waiting for final response...")
            
            # Check if response has direct function_calls attribute
            if not has_function_calls and hasattr(response, "function_calls") and response.function_calls:
                function_calls = response.function_calls
                has_function_calls = True
                print(f"\n🔧 Function call(s) detected: {len(function_calls)}")
                
                for i, function_call in enumerate(function_calls):
                    print(f"\n🔧 Processing function call {i+1}/{len(function_calls)}: {function_call.name}")
                    
                    # Handle function call
                    result = handle_function_call(function_call)
                    
                    # Send function result back to Gemini
                    print("\n📤 Sending function result back to Gemini...")
                    function_response = {
                        "function_response": {
                            "name": function_call.name,
                            "response": result
                        }
                    }
                    
                    response = chat.send_message(function_response)
                    print("✅ Function result sent, waiting for final response...")
            
            if not has_function_calls:
                print("\n🔍 No function calls detected in the response.")
            
            # Print response safely
            try:
                print("\nArtemis:", response.text)
            except AttributeError:
                print("\nArtemis: I processed your request but didn't generate a text response.")
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            print("Please try again or type 'exit' to quit.")

if __name__ == "__main__":
    simple_chat() 