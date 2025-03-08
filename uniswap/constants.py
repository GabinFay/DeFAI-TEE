from typing import Set, cast

from web3.types import RPCEndpoint  # noqa: F401

# look at web3/middleware/cache.py for reference
# RPC methods that will be cached inside _get_eth_simple_cache_middleware
SIMPLE_CACHE_RPC_WHITELIST = cast(
    Set[RPCEndpoint],
    {
        "eth_chainId",
    },
)

ETH_ADDRESS = "0x0000000000000000000000000000000000000000"
WETH9_ADDRESS = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"

# see: https://chainid.network/chains/
_netid_to_name = {
    1: "mainnet",
    3: "ropsten",
    4: "rinkeby",
    5: "görli",
    10: "optimism",
    42: "kovan",
    56: "binance",
    97: "binance_testnet",
    137: "polygon",
    100: "xdai",
    250: "fantom",
    42161: "arbitrum",
    421611: "arbitrum_testnet",
    1666600000: "harmony_mainnet",
    1666700000: "harmony_testnet",
    11155111: "sepolia",
    14: "flare",  # Adding Flare network with chain ID 14
}

_factory_contract_addresses_v1 = {
    "mainnet": "0xc0a47dFe034B400B47bDaD5FecDa2621de6c4d95",
    "ropsten": "0x9c83dCE8CA20E9aAF9D3efc003b2ea62aBC08351",
    "rinkeby": "0xf5D915570BC477f9B8D6C0E980aA81757A3AaC36",
    "kovan": "0xD3E51Ef092B2845f10401a0159B2B96e8B6c3D30",
    "görli": "0x6Ce570d02D73d4c384b46135E87f8C592A8c86dA",
}


# For v2 the address is the same on mainnet, Ropsten, Rinkeby, Görli, and Kovan
# https://uniswap.org/docs/v2/smart-contracts/factory
_factory_contract_addresses_v2 = {
    "mainnet": "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
    "ropsten": "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
    "rinkeby": "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
    "görli": "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
    "xdai": "0xA818b4F111Ccac7AA31D0BCc0806d64F2E0737D7",
    "binance": "0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73",
    "binance_testnet": "0x6725F303b657a9451d8BA641348b6761A6CC7a17",
    # SushiSwap on Harmony
    "harmony_mainnet": "0xc35DADB65012eC5796536bD9864eD8773aBc74C4",
    "harmony_testnet": "0xc35DADB65012eC5796536bD9864eD8773aBc74C4",
    "sepolia": "0x7E0987E5b3a30e3f2828572Bb659A548460a3003",
    # Flare Uniswap V2 Factory
    "flare": "0x16b619B04c961E8f4F06C10B42FDAbb328980A89",
}

_router_contract_addresses_v2 = {
    "mainnet": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
    "ropsten": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
    "rinkeby": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
    "görli": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
    "sepolia": "0xC532a74256D3Db42D0Bf7a0400fEFDbad7694008",
    "xdai": "0x1C232F01118CB8B424793ae03F870aa7D0ac7f77",
    "binance": "0x10ED43C718714eb63d5aA57B78B54704E256024E",
    "binance_testnet": "0xD99D1c33F9fC3444f8101754aBC46c52416550D1",
    # SushiSwap on Harmony
    "harmony_mainnet": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",
    "harmony_testnet": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",
    # Flare Uniswap V2 Router
    "flare": "0x4a1E5A90e9943467FAd1acea1E7F0e5e88472a1e",
}

MAX_UINT_128 = (2**128) - 1

# Source: https://github.com/Uniswap/v3-core/blob/v1.0.0/contracts/libraries/TickMath.sol#L8-L11
MIN_TICK = -887272
MAX_TICK = -MIN_TICK

# Source: https://github.com/Uniswap/v3-core/blob/v1.0.0/contracts/UniswapV3Factory.sol#L26-L31
_tick_spacing = {100: 1, 500: 10, 3_000: 60, 10_000: 200}

# Derived from (MIN_TICK//tick_spacing) >> 8 and (MAX_TICK//tick_spacing) >> 8
_tick_bitmap_range = {
    100: (-3466, 3465),
    500: (-347, 346),
    3_000: (-58, 57),
    10_000: (-18, 17),
}

# Adding Flare V3 Factory address
_factory_contract_addresses_v3 = {
    "mainnet": "0x1F98431c8aD98523631AE4a59f267346ea31F984",
    "görli": "0x1F98431c8aD98523631AE4a59f267346ea31F984",
    "arbitrum": "0x1F98431c8aD98523631AE4a59f267346ea31F984",
    "optimism": "0x1F98431c8aD98523631AE4a59f267346ea31F984",
    "polygon": "0x1F98431c8aD98523631AE4a59f267346ea31F984",
    "flare": "0x8A2578d23d4C532cC9A98FaD91C0523f5efDE652",
}

# Adding Flare V3 Router address
_router_contract_addresses_v3 = {
    "mainnet": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
    "görli": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
    "arbitrum": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
    "optimism": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
    "polygon": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
    "flare": "0x8a1E35F5c98C4E85B36B7B253222eE17773b2781",
}

# Adding Flare NonfungiblePositionManager address
_nonfungible_position_manager_addresses = {
    "mainnet": "0xC36442b4a4522E871399CD717aBDD847Ab11FE88",
    "görli": "0xC36442b4a4522E871399CD717aBDD847Ab11FE88",
    "arbitrum": "0xC36442b4a4522E871399CD717aBDD847Ab11FE88",
    "optimism": "0xC36442b4a4522E871399CD717aBDD847Ab11FE88",
    "polygon": "0xC36442b4a4522E871399CD717aBDD847Ab11FE88",
    "flare": "0xEE5FF5Bc5F852764b5584d92A4d592A53DC527da",
}

# Adding Flare Quoter address
_quoter_contract_addresses = {
    "mainnet": "0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6",
    "görli": "0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6",
    "arbitrum": "0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6",
    "optimism": "0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6",
    "polygon": "0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6",
    "flare": "0x5B5513c55fd06e2658010c121c37b07fC8e8B705",
}
