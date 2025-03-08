import streamlit as st
import streamlit.components.v1 as components
from web3 import Web3
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Use the development server
# Note: You need to run the frontend development server separately with:
# cd python_web3_wallet/frontend
# npm run start
wallet_component = components.declare_component("python_web3_wallet", url="http://localhost:3001")

st.set_page_config(
    page_title="Web3 Wallet Connector",
    page_icon="💰",
    layout="centered"  # Changed back to centered for better layout
)

# Custom CSS to remove extra padding and make the component larger
st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    iframe {
        height: 600px !important;
        width: 100% !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for transaction history
if 'transaction_history' not in st.session_state:
    st.session_state.transaction_history = []

# Initialize Web3 connections for different chains
@st.cache_resource
def get_web3_provider(chain_id):
    # Default to Ethereum mainnet if chain_id is not recognized
    rpc_urls = {
        1: os.getenv('ETHEREUM_RPC_URL', 'https://eth.llamarpc.com'),  # Ethereum Mainnet
        8453: os.getenv('BASE_RPC_URL', 'https://mainnet.base.org'),   # Base Chain
        14: os.getenv('FLARE_RPC_URL', 'https://flare-api.flare.network/ext/C/rpc')  # Flare Mainnet
    }
    
    rpc_url = rpc_urls.get(chain_id, rpc_urls[1])  # Default to Ethereum if chain_id not found
    return Web3(Web3.HTTPProvider(rpc_url))

# Function to handle transaction data from MetaMask
def send_transaction(transaction_data):
    try:
        # Extract transaction details
        from_address = transaction_data['from']
        to_address = transaction_data['to']
        value = transaction_data['value']
        chain_id = transaction_data['chainId']
        tx_hash = transaction_data.get('tx_hash')
        
        # Get Web3 provider for the specified chain
        w3 = get_web3_provider(chain_id)
        
        if tx_hash:
            # Transaction was already signed and sent by MetaMask
            # We just need to track it and wait for confirmation
            try:
                # Wait for the transaction receipt
                receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                
                # Add transaction to history
                st.session_state.transaction_history.append({
                    'from': from_address,
                    'to': to_address,
                    'value': value,
                    'chain_id': chain_id,
                    'status': 'Confirmed' if receipt.status == 1 else 'Failed',
                    'tx_hash': tx_hash
                })
                
                return {
                    'success': True,
                    'message': f'Transaction confirmed! Hash: {tx_hash}',
                    'tx_hash': tx_hash
                }
            except Exception as e:
                # If we can't get the receipt yet, still record the transaction
                st.session_state.transaction_history.append({
                    'from': from_address,
                    'to': to_address,
                    'value': value,
                    'chain_id': chain_id,
                    'status': 'Pending',
                    'tx_hash': tx_hash
                })
                
                return {
                    'success': True,
                    'message': f'Transaction sent! Hash: {tx_hash}. Waiting for confirmation...',
                    'tx_hash': tx_hash
                }
        else:
            # No transaction hash provided - this shouldn't happen with the updated frontend
            return {
                'success': False,
                'message': 'No transaction hash provided. The transaction may not have been sent.'
            }
    except Exception as e:
        return {
            'success': False,
            'message': f'Error processing transaction: {str(e)}'
        }

# The wallet_component function requires recipient, amount_in_ether, and data parameters
# We'll set them to default values since we only want to connect the wallet
wallet_status = wallet_component(
    recipient="0x0000000000000000000000000000000000000000",  # Zero address
    amount_in_ether="0",  # No ETH to transfer
    data="0x"  # No data to send
)

# Display connection status and handle transactions
if wallet_status:
    if isinstance(wallet_status, dict):
        if wallet_status.get('type') == 'connection':
            st.success(f"Wallet connected successfully! Address: {wallet_status.get('address')}")
            st.balloons()
        elif wallet_status.get('type') == 'transaction':
            transaction_result = send_transaction(wallet_status.get('transaction', {}))
            if transaction_result['success']:
                st.success(transaction_result['message'])
            else:
                st.error(transaction_result['message'])
    elif isinstance(wallet_status, str) and wallet_status.startswith("0x"):
        st.success(f"Wallet connected successfully! Address: {wallet_status}")
        st.balloons()
    else:
        st.success("Wallet connected successfully!")
        st.balloons()

# Display transaction history
if st.session_state.transaction_history:
    st.subheader("Transaction History")
    for i, tx in enumerate(st.session_state.transaction_history):
        st.write(f"**Transaction {i+1}**")
        st.write(f"From: {tx['from']}")
        st.write(f"To: {tx['to']}")
        st.write(f"Value: {tx['value']} ETH")
        st.write(f"Chain ID: {tx['chain_id']}")
        st.write(f"Status: {tx['status']}")
        if 'tx_hash' in tx:
            st.write(f"Transaction Hash: {tx['tx_hash']}")
        st.write("---") 