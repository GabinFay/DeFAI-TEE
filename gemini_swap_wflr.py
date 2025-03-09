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

# Load environment variables
load_dotenv()

# Get Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

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
- flrETH: 0x26A1faB310bd080542DC864647d05985360B16A5
- sFLR: 0x12e605bc104e93B45e1aD99F9e555f659051c2BB
- Joule: 0xE6505f92583103AF7ed9974DEC451A7Af4e3A3bE
- Usdx: 0xFE2907DFa8DB6e320cDbF45f0aa888F6135ec4f8
- USDT: 0x0B38e83B86d491735fEaa0a791F65c2B99535396
- USDC: 0xFbDa5F676cB37624f28265A144A48B0d6e87d3b6
- XVN: 0xaFBdD875858Dd48EE32A68Ac1349A5017095B161
- WFLR: 0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d
- cysFLR: 0x19831cfB53A0dbeAD9866C43557C1D48DfF76567
- WETH: 0x1502FA4be69d526124D453619276FacCab275d3D

Kinetic Tokens:
- ksFLR: 0x291487beC339c2fE5D83DD45F0a15EFC9Ac45656
- kUSDC.e: 0xDEeBaBe05BDA7e8C1740873abF715f16164C29B8
- kUSDT: 0x1e5bBC19E0B17D7d38F318C79401B3D16F2b93bb
- kwETH: 0x5C2400019017AE61F811D517D088Df732642DbD0
- kflETH: 0x40eE5dfe1D4a957cA8AC4DD4ADaf8A8fA76b1C16
- rFLR: 0x26d460c3Cf931Fb2014FA436a49e3Af08619810e

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
                print(f"\n⚠️ Warning: Could not resolve token name '{token_in}' to an address")
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
                print(f"\n⚠️ Warning: Could not resolve token name '{token_out}' to an address")
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
            print("\n" + "="*50)
            print(f"🔧 FUNCTION CALL DETECTED: {function_call.name}")
            print(f"Parameters:")
            print(f"  - token_in: {token_in_display} ({token_in})")
            print(f"  - token_out: {token_out_display} ({token_out})")
            print(f"  - amount_in_eth: {amount_in_eth}")
            if fee is not None:
                print(f"  - fee: {fee} ({fee/10000}%)")
            else:
                print(f"  - fee: Auto-select (will find pool with most liquidity)")
            print("="*50)
            
            print(f"\n🚀 Executing swap: {amount_in_eth} {token_in_display} to {token_out_display}")
            if fee is not None:
                print(f"Using fee tier: {fee} ({fee/10000}%)")
            else:
                print("Finding best fee tier based on liquidity...")
                
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
                    "token_in": token_in_display,
                    "token_out": token_out_display
                }
                
                print(f"\n✅ Swap successful! Transaction hash: {tx_hash}")
                return success_message
            else:
                failure_message = {
                    "success": False,
                    "message": f"Swap failed. Check console for detailed error messages.",
                    "token_in": token_in_display,
                    "token_out": token_out_display
                }
                print("\n❌ Swap failed! No transaction hash returned.")
                return failure_message
        except Exception as e:
            error_message = {
                "success": False,
                "message": f"Error executing swap: {str(e)}",
                "token_in": token_in_display,
                "token_out": token_out_display
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
    print("Mode: REAL SWAP (will use real tokens)")
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