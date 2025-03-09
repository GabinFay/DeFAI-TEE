import React from "react"
import ReactDOM from "react-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { getDefaultConfig, RainbowKitProvider } from "@rainbow-me/rainbowkit";
import { WagmiProvider } from "wagmi";
import { Chain, base, mainnet } from "wagmi/chains";
import PythonWeb3Wallet from "./PythonWeb3Wallet";
import '@rainbow-me/rainbowkit/styles.css';
import { http } from 'viem';
import { flareWithIcon } from "./chains";

const queryClient = new QueryClient();

// for using with forked-Base chain
const baseRemoteAnvil = {
  id: 84531,
  name: 'Base-Fork',
  nativeCurrency: {
    name: 'ETH',
    symbol: 'ETH',
    decimals: 18
  },
  rpcUrls: {
    default: { http: [process.env.REACT_APP_RPC_URL || 'http://localhost:8545'] },
    public: { http: [process.env.REACT_APP_RPC_URL || 'http://localhost:8545'] },
  },
} as const satisfies Chain;

console.log('debug', process.env.REACT_APP_DEBUG_VARIABLE);

// Use a fallback projectId if the environment variable is not set
// For production, you should get your own projectId from https://cloud.walletconnect.com/
const projectId = process.env.REACT_APP_RAINBOW_PROJECT_ID || "c4f79cc821d7b9f37b4ba2e4807f6721";

const config = getDefaultConfig({
  appName: 'Python Web3 Wallet',
  projectId: projectId,
  chains: [
    mainnet,
    base,
    flareWithIcon,
    baseRemoteAnvil
  ],
  transports: {
    // Force using HTTP transport instead of WebSocket
    [mainnet.id]: http(),
    [base.id]: http(),
    [flareWithIcon.id]: http(),
    [baseRemoteAnvil.id]: http(),
  },
});

ReactDOM.render(
  <WagmiProvider config={config}>
    <QueryClientProvider client={queryClient}>
      <RainbowKitProvider>
        <PythonWeb3Wallet />
      </RainbowKitProvider>
    </QueryClientProvider>
  </WagmiProvider>,
  document.getElementById("root")
)