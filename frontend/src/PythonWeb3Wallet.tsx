import { ConnectButton } from "@rainbow-me/rainbowkit";
import '@rainbow-me/rainbowkit/styles.css';
import React, { ReactElement, useEffect, useMemo, useState } from "react";
import {
  ComponentProps,
  Streamlit,
  withStreamlitConnection,
} from "streamlit-component-lib";
import { useAccount, useChainId, useSignMessage, useWalletClient } from "wagmi";
import { base, mainnet } from "wagmi/chains";
import { parseEther } from "viem";
import { flareWithIcon } from "./chains";

/**
 * This is a React-based component template. The passed props are coming from the 
 * Streamlit library. Your custom args can be accessed via the `args` props.
 */
function PythonWeb3Wallet({ args, disabled, theme }: ComponentProps): ReactElement {
  const { recipient, amountInEther, data } = args;
  const account = useAccount();
  const chainId = useChainId();
  const { data: walletClient } = useWalletClient();

  const [isFocused, setIsFocused] = useState(false);
  const [destinationAddress, setDestinationAddress] = useState("");
  const [amount, setAmount] = useState("");
  const [transactionStatus, setTransactionStatus] = useState("");

  const style: React.CSSProperties = useMemo(() => {
    if (!theme) return {}

    // Use the theme object to style our button border. Alternatively, the
    // theme style is defined in CSS vars.
    const borderStyling = `1px solid ${isFocused ? theme.primaryColor : "gray"}`
    return { border: borderStyling, outline: borderStyling }
  }, [theme, isFocused]);

  // setFrameHeight should be called on first render and evertime the size might change (e.g. due to a DOM update).
  useEffect(() => {
    // Increase height to accommodate the transaction form
    Streamlit.setFrameHeight(400)
  }, [style, theme]);

  // Report back to Streamlit when the wallet is connected
  useEffect(() => {
    if (account.isConnected && account.address) {
      console.log('Wallet connected:', account.address);
      Streamlit.setComponentValue({
        type: 'connection',
        address: account.address
      });
      // Update height again after connection to ensure all content is visible
      Streamlit.setFrameHeight(400)
    }
  }, [account.isConnected, account.address]);

  // Get chain name based on chainId - keeping this for potential future use
  const getChainName = (id: number) => {
    switch(id) {
      case mainnet.id:
        return "Ethereum Mainnet";
      case base.id:
        return "Base Chain";
      case flareWithIcon.id:
        return "Flare Mainnet";
      default:
        return "Unknown Chain";
    }
  };

  const handleSendTransaction = async () => {
    if (!account.isConnected || !account.address || !walletClient) {
      setTransactionStatus("Please connect your wallet first");
      return;
    }

    if (!destinationAddress || !amount) {
      setTransactionStatus("Please enter both destination address and amount");
      return;
    }

    try {
      setTransactionStatus("Preparing transaction...");
      
      // Convert amount to Wei
      const valueInWei = parseEther(amount);
      
      // Sign and send the transaction directly with MetaMask
      setTransactionStatus("Waiting for transaction approval in MetaMask...");
      
      // Request transaction signature from MetaMask
      const hash = await walletClient.sendTransaction({
        to: destinationAddress as `0x${string}`,
        value: valueInWei,
        account: account.address,
      });
      
      // Send the transaction hash to the Python backend for tracking
      setTransactionStatus("Transaction approved! Sending details to backend...");
      Streamlit.setComponentValue({
        type: 'transaction',
        transaction: {
          from: account.address,
          to: destinationAddress,
          value: amount,
          chainId: chainId,
          tx_hash: hash
        }
      });
      
      setTransactionStatus(`Transaction sent! Hash: ${hash}`);
    } catch (error) {
      console.error("Transaction error:", error);
      setTransactionStatus(`Error: ${error instanceof Error ? error.message : String(error)}`);
    }
  };

  return (
    <div style={{ 
      padding: '20px', 
      fontFamily: 'Arial, sans-serif',
      width: '100%',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'flex-start',
      fontSize: '16px'
    }}>
      
      <div style={{ transform: 'scale(1.2)', marginBottom: '30px' }}>
        <ConnectButton />
      </div>

      {account.isConnected && (
        <div style={{ 
          width: '100%', 
          maxWidth: '400px', 
          border: '1px solid #ddd', 
          borderRadius: '8px',
          padding: '20px',
          marginTop: '20px'
        }}>
          <h3 style={{ marginBottom: '15px', fontSize: '18px' }}>Send Transaction</h3>
          
          <div style={{ marginBottom: '15px' }}>
            <label style={{ display: 'block', marginBottom: '5px' }}>Destination Address:</label>
            <input 
              type="text" 
              value={destinationAddress}
              onChange={(e) => setDestinationAddress(e.target.value)}
              placeholder="0x..."
              style={{ 
                width: '100%', 
                padding: '8px', 
                borderRadius: '4px', 
                border: '1px solid #ccc' 
              }}
            />
          </div>
          
          <div style={{ marginBottom: '15px' }}>
            <label style={{ display: 'block', marginBottom: '5px' }}>Amount (ETH):</label>
            <input 
              type="text" 
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="0.01"
              style={{ 
                width: '100%', 
                padding: '8px', 
                borderRadius: '4px', 
                border: '1px solid #ccc' 
              }}
            />
          </div>
          
          <button 
            onClick={handleSendTransaction}
            style={{ 
              backgroundColor: '#3498db', 
              color: 'white', 
              border: 'none', 
              borderRadius: '4px', 
              padding: '10px 15px', 
              cursor: 'pointer',
              width: '100%',
              fontWeight: 'bold'
            }}
          >
            Send Transaction
          </button>
          
          {transactionStatus && (
            <div style={{ 
              marginTop: '15px', 
              padding: '10px', 
              backgroundColor: transactionStatus.includes('Error') ? '#ffebee' : '#e8f5e9',
              borderRadius: '4px',
              color: transactionStatus.includes('Error') ? '#c62828' : '#2e7d32'
            }}>
              {transactionStatus}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default withStreamlitConnection(PythonWeb3Wallet)