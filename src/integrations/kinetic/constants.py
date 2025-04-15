"""
Constants for the Kinetic Python SDK.
"""

# Kinetic contract addresses on Flare
KINETIC_ADDRESSES = {
    'Deployer': '0x38DD5f83556825A2c23a65bd4c3bB10aBa33C221',
    'Admin': '0xd8575Ff9eBEDC5becaa6DaCE50B7fdbFa1276352',
    'JOULE': '0xE6505f92583103AF7ed9974DEC451A7Af4e3A3bE',
    'JOULE_Proxy_Admin': '0x12d5c8B8C0e9708E92342d7Ab6394Ca62B6c04D0',
    'JOULE_Implementation': '0x6C8fF0Ee51aF014c8B12D1D5F040A13f73B633fe',
    'JOULE_ImplementationV2': '0xEE15da0edB70FC6D98D03651F949FcCc2C4e1E80',
    'Kii': '0xd38220CFF996A73E9110aacA64e02d581B83A0CD',
    'Kii_Implementation': '0xDFa53C46bBB84aB0Fb580BDE6F576970F3482E03',
    'Kii_ImplementationV2': '0xEA056C4Fbd622fee1338ec01E223bF63E4531FC6',
    'Rebates_Off_Chain_Wallet': '0x403b2e427DE4D62DD42082f525b59D838aD5300C',
    'Kii_Staking_Rewards_Off_Chain_Wallet': '0x4c88B927b574635D3efe5C589f8C11e53b28Dc01',
    'Univ2OracleAddress': '0x67f6506eda989b1ad6ae7706F5D1E75dec219C7f',
    'RedeemBurnRateCalculator': '0x9747AAA69ea860FBC39c0f73199B5769FAaBCC2A',
    'Unitroller': '0x8041680Fb73E1Fe5F851e76233DCDfA0f2D2D7c8',
    'Comptroller': '0xeC7e541375D70c37262f619162502dB9131d6db5',
    'LiquidatorWhiteList': '0x5fa1B6Cdc8E46BfFEed066E1ECd92F90C663e8CC',
    'ProtocolFTSOV2Oracle': '0x952fc67C5930776fe890A812dcd23919559eE6b2',
    'Lending_Rebates_Rewards': '0xb52aB55F9325B4522c3bdAc692D4F21b0CbA05Ee',
    'Borrow_Rebates_Rewards': '0x5896c198e445E269021B04D7c84FA46dc2cEdcd8',
    'Kii_Staking_Rewards': '0x1218b178e170E8cfb3Ba5ADa853aaF4579845347',
    'Lens': '0x120f76169dd938361cE917bDF773979FB21b7d19',
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

# Token decimals
TOKEN_DECIMALS = {
    'sFLR': 18,
    'USDC.e': 6,
    'USDT': 6,
    'wETH': 18,
    'flETH': 18,
    'rFLR': 18,
}

# ERC20 ABI
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [{"name": "guy", "type": "address"}, {"name": "wad", "type": "uint256"}],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [{"name": "src", "type": "address"}, {"name": "dst", "type": "address"}, {"name": "wad", "type": "uint256"}],
        "name": "transferFrom",
        "outputs": [{"name": "", "type": "bool"}],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [{"name": "dst", "type": "address"}, {"name": "wad", "type": "uint256"}],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "", "type": "address"}, {"name": "", "type": "address"}],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]

# CErc20 ABI
CERC20_ABI = [
    {
        "constant": False,
        "inputs": [{"name": "mintAmount", "type": "uint256"}],
        "name": "mint",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "comptroller",
        "outputs": [{"name": "", "type": "address"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "underlying",
        "outputs": [{"name": "", "type": "address"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "exchangeRateStored",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [],
        "name": "accrueInterest",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [{"name": "redeemTokens", "type": "uint256"}],
        "name": "redeem",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [{"name": "redeemAmount", "type": "uint256"}],
        "name": "redeemUnderlying",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [{"name": "borrowAmount", "type": "uint256"}],
        "name": "borrow",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [{"name": "repayAmount", "type": "uint256"}],
        "name": "repayBorrow",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [{"name": "borrower", "type": "address"}, {"name": "repayAmount", "type": "uint256"}],
        "name": "repayBorrowBehalf",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

# Comptroller ABI
COMPTROLLER_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "", "type": "address"}],
        "name": "markets",
        "outputs": [
            {"name": "isListed", "type": "bool"},
            {"name": "collateralFactorMantissa", "type": "uint256"},
            {"name": "isComped", "type": "bool"}
        ],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "", "type": "address"}],
        "name": "mintGuardianPaused",
        "outputs": [{"name": "", "type": "bool"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [{"name": "cToken", "type": "address"}, {"name": "minter", "type": "address"}, {"name": "mintAmount", "type": "uint256"}],
        "name": "mintAllowed",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "getAllMarkets",
        "outputs": [{"name": "", "type": "address[]"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "account", "type": "address"}],
        "name": "getAccountLiquidity",
        "outputs": [
            {"name": "", "type": "uint256"},
            {"name": "", "type": "uint256"},
            {"name": "", "type": "uint256"}
        ],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [{"name": "cTokens", "type": "address[]"}],
        "name": "enterMarkets",
        "outputs": [{"name": "", "type": "uint256[]"}],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [{"name": "cTokenAddress", "type": "address"}],
        "name": "exitMarket",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

# Error codes
ERROR_CODES = {
    "0": "NO_ERROR",
    "1": "UNAUTHORIZED",
    "2": "COMPTROLLER_MISMATCH",
    "3": "INSUFFICIENT_LIQUIDITY",
    "4": "INSUFFICIENT_BALANCE",
    "5": "COMPTROLLER_REJECTION",
    "6": "COMPTROLLER_CALCULATION_ERROR",
    "7": "INTEREST_RATE_MODEL_ERROR",
    "8": "INVALID_ACCOUNT_PAIR",
    "9": "INVALID_CLOSE_AMOUNT_REQUESTED",
    "10": "INVALID_COLLATERAL_FACTOR",
    "11": "MATH_ERROR",
    "12": "MARKET_NOT_FRESH",
    "13": "MARKET_NOT_LISTED",
    "14": "TOKEN_INSUFFICIENT_ALLOWANCE",
    "15": "TOKEN_INSUFFICIENT_BALANCE",
    "16": "TOKEN_INSUFFICIENT_CASH",
    "17": "TOKEN_TRANSFER_IN_FAILED",
    "18": "TOKEN_TRANSFER_OUT_FAILED"
} 