# Flare Uniswap SDK Integration

This repository contains scripts for interacting with Uniswap V3 on the Flare network using the uniswap-python SDK.

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

## Scripts

### flare_uniswap_sdk_swap.py

This script demonstrates how to swap tokens on Flare using Uniswap V3.

### flare_uniswap_add_liquidity.py

This script demonstrates how to add liquidity to a Uniswap V3 pool on Flare.

## Recent Fixes

The following issues were fixed to make the SDK work correctly with Flare:

1. Updated the constants.py file to include all the correct Flare network addresses
2. Modified the uniswap.py file to use the correct position manager address from the _nonfungible_position_manager_addresses dictionary
3. Added better error handling and debugging information to the add_liquidity script
4. Used a narrower tick range for position creation
5. Properly estimated gas for transactions

## Usage

1. Install the required dependencies:
```
pip install web3 uniswap-python
```

2. Set up your environment variables in a .env file:
```
FLARE_RPC_URL=https://flare-api.flare.network/ext/C/rpc
WALLET_ADDRESS=your_wallet_address
PRIVATE_KEY=your_private_key
```

3. Run the scripts:
```
python flare_uniswap_sdk_swap.py
python flare_uniswap_add_liquidity.py
```

## Notes

- When adding liquidity, ensure that token0 address is less than token1 address (required by Uniswap V3)
- The Flare network has chain ID 14
- WFLR address on Flare: 0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d
- USDC.e address on Flare: 0xFbDa5F676cB37624f28265A144A48B0d6e87d3b6 