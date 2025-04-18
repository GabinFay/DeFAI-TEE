# Flare Uniswap SDK Integration

This repository contains scripts for interacting with Uniswap V3 on the Flare network using the uniswap-python SDK.

## Project Structure

The project is organized as follows:

```
flare-bot/
├── tools/                  # All tool implementations
│   ├── uniswap/            # Uniswap V3 tools
│   ├── tokens/             # Token-related tools
│   ├── lending/            # Lending protocol tools
│   └── utils/              # Utility functions
├── abis/                   # Contract ABIs
├── handlers.py             # Function handlers for Gemini AI
├── streamlit_gemini_swap.py # Streamlit UI
└── other files...
```

See the [tools README](tools/README.md) for more details on the tools directory structure.

## Flare Network Addresses

The following addresses are used for Uniswap V3 on Flare:

- V2Factory: 0x16b619B04c961E8f4F06C10B42FDAbb328980A89
- UniswapV2Router02: 0x4a1E5A90e9943467FAd1acea1E7F0e5e88472a1e
- QuoterV2: 0x2DcABbB3a5Fe9DBb1F43edf48449aA7254Ef3a80
- V3Factory: 0x8A2578d23d4C532cC9A98FaD91C0523f5efDE652
- V3Migrator: 0xf2f986C04387570A7C7819fac51bd553bb0814af
- UniversalRouter: 0x0f3D8a38D4c74afBebc2c42695642f0e3acb15D3
- TokenDistributor: 0x30FAA249e1ec3e75e203feBD35eb010b8E7BD22B
- Unsupported: 0x38D411c8bBA193C8C8393DAAcEa67F9d9105EFB7
- QuoterV2: 0x5B5513c55fd06e2658010c121c37b07fC8e8B705
- Permit2: 0xB952578f3520EE8Ea45b7914994dcf4702cEe578
- SwapRouter: 0x8a1E35F5c98C4E85B36B7B253222eE17773b2781
- NonfungiblePositionManager: 0xEE5FF5Bc5F852764b5584d92A4d592A53DC527da
- NonfungibleTokenPositionDescriptor: 0x840777EF3ED0457729354754946D96c07116651e
- OldNftManager: 0x9BD490113a249c81D0beA52d677134f5e87C0d60
- NFTDescriptor: 0x98904715dDd961fb368eF7ea3A419ff1FB664c38
- TickLens: 0xdB5F2Ca65aAeB277E36be69553E0e7aA3585204d
- v2Pair_InitCodeHash: 0x60cc0e9ad39c5fa4ee52571f511012ed76fbaa9bbaffd2f3fafffcb3c47cff6e
- v3Pool_InitCodeHash: 0x209015062f691a965df159762a8d966b688e328361c53ec32da2ad31287e3b72

## Tools

### Uniswap Tools

- **swap_tokens**: Swap tokens on Uniswap V3
- **add_liquidity**: Add liquidity to a Uniswap V3 pool
- **remove_liquidity**: Remove liquidity from a Uniswap V3 position
- **get_positions**: Get all Uniswap V3 positions for a wallet
- **get_pool_info**: Get information about a Uniswap V3 pool

### Token Tools

- **wrap_flare**: Wrap native FLR to WFLR
- **unwrap_flare**: Unwrap WFLR back to native FLR
- **get_token_balances**: Get token balances for a wallet

### Lending Tools

- **borrow**: Borrow assets from lending protocols
- **repay**: Repay borrowed assets
- **supply**: Supply assets to lending protocols

## Scripts

### flare_uniswap_sdk_swap.py

This script demonstrates how to swap tokens on Flare using Uniswap V3.

```bash
python flare_uniswap_sdk_swap.py
```

### flare_uniswap_add_liquidity.py

This script demonstrates how to add liquidity to a Uniswap V3 pool on Flare.

```bash
python flare_uniswap_add_liquidity.py
```

### flare_uniswap_remove_liquidity.py

This script demonstrates how to remove liquidity from a Uniswap V3 position on Flare.

```bash
python flare_uniswap_remove_liquidity.py
```

### flare_uniswap_sdk_test.py

This script provides a comprehensive test suite for Uniswap V3 on Flare.

```bash
# Run all tests
python flare_uniswap_sdk_test.py --all

# Test specific functionality
python flare_uniswap_sdk_test.py --swap
python flare_uniswap_sdk_test.py --pool
python flare_uniswap_sdk_test.py --positions
python flare_uniswap_sdk_test.py --provide
python flare_uniswap_sdk_test.py --remove <position_id> --percent <percentage>
```

### streamlit_gemini_swap.py

This is the main Streamlit application that provides a user interface for interacting with Uniswap on Flare.

```bash
streamlit run streamlit_gemini_swap.py
```

## SDK Modifications

The following modifications were made to the uniswap-python SDK to support Flare network:

1. **constants.py**: Added all Flare network contract addresses and constants
   - Added WFLR_ADDRESS
   - Added _wrapped_native_token dictionary
   - Added all contract addresses for Flare network
   - Added init code hashes for Flare network

2. **uniswap.py**: Modified to use Flare network addresses
   - Updated initialization to use network-specific addresses
   - Added robust error handling for token operations
   - Updated get_weth_address to return WFLR on Flare network
   - Added logging for contract addresses

3. **Position Data Structure**: Adapted to Flare's position data structure
   - Flare's position data structure: [nonce, operator, token0, token1, fee, tickLower, tickUpper, liquidity, ...]
   - Updated position handling in test_get_positions and remove_liquidity

## Usage Notes

- When adding liquidity, ensure that token0 address is less than token1 address (required by Uniswap V3)
- The Flare network has chain ID 14
- WFLR address on Flare: 0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d
- USDC.e address on Flare: 0xFbDa5F676cB37624f28265A144A48B0d6e87d3b6

## Environment Setup

Create a .env file with the following variables:

```
FLARE_RPC_URL=https://flare-api.flare.network/ext/C/rpc
WALLET_ADDRESS=your_wallet_address
PRIVATE_KEY=your_private_key
```

## Dependencies

```
pip install web3 uniswap-python python-dotenv eth-account
```

## Docker Usage

This project can be run as a Docker container. The Docker image is available on GitHub Container Registry.

### Building the Docker Image

You can build the Docker image locally using:

```bash
./build_and_push_image.sh
```

This script will build the image and push it to GitHub Container Registry.

### Running the Docker Container

There are two ways to run the Docker container:

#### Option 1: Mount your .env file (RECOMMENDED)

This is the recommended approach as it keeps your sensitive information out of the Docker image:

```bash
docker run -p 8501:8501 \
  -v /path/to/your/.env:/app/.env \
  ghcr.io/your-username/your-repo:latest
```

Replace `/path/to/your/.env` with the actual path to your .env file.

#### Option 2: Provide environment variables directly

You can also provide environment variables directly to the Docker container:

```bash
docker run -p 8501:8501 \
  -e GEMINI_API_KEY=your_api_key \
  -e FLARE_RPC_URL=your_rpc_url \
  -e WALLET_ADDRESS=your_wallet_address \
  -e PRIVATE_KEY=your_private_key \
  ghcr.io/your-username/your-repo:latest
```

### Security Considerations

When using Docker with blockchain applications, always be mindful of security:

1. **NEVER include private keys or API keys in your Docker image**
2. **ALWAYS use .env files or environment variables to pass sensitive information**
3. **Verify your .dockerignore file excludes sensitive files**
4. **Consider using Docker secrets for production deployments**

## TEE Attestation

This application supports Trusted Execution Environment (TEE) attestation when deployed on Google Cloud Confidential VMs. The attestation feature allows you to verify that the application is running in a secure TEE environment.

### How to Use Attestation

1. Deploy the application on a Google Cloud Confidential VM
2. Set `SIMULATE_ATTESTATION=false` in your environment variables
3. In the Streamlit UI, click the "Generate Attestation" button in the sidebar
4. The application will automatically generate and verify the attestation token
5. If verification is successful, you'll see attestation details including issuer, issuance time, and expiration time

### Attestation Verification

The application automatically verifies the attestation token after generation by:
- Validating the token structure and signature algorithm
- Checking that the token contains the expected nonce (preventing replay attacks)
- Verifying the token issuer and expiration time
- For simulated tokens, a simplified verification process is used

### Environment Variables

- `SIMULATE_ATTESTATION`: Set to "false" to use real attestation (default) or "true" to use simulated attestation for testing 