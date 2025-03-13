"""
Constants used throughout the Flare Bot application.
This file contains token addresses, ABIs, and other constants.
"""

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

# Default RPC URL for Flare network
DEFAULT_FLARE_RPC_URL = "https://flare-api.flare.network/ext/C/rpc" 