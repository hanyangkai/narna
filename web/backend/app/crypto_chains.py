from __future__ import annotations

import os
from dataclasses import dataclass


TRANSFER_TOPIC = (
    "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
)


@dataclass(frozen=True)
class TokenConfig:
    address: str
    decimals: int


@dataclass(frozen=True)
class ChainConfig:
    id: str
    name: str
    chain_id: int
    rpc_env: str
    tokens: dict[str, TokenConfig]


CHAINS: dict[str, ChainConfig] = {
    "ethereum": ChainConfig(
        id="ethereum",
        name="Ethereum",
        chain_id=1,
        rpc_env="UAP_ETH_RPC_URL",
        tokens={
            "usdc": TokenConfig("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", 6),
            "usdt": TokenConfig("0xdAC17F958D2ee523a2206206994597C13D831ec7", 6),
        },
    ),
    "polygon": ChainConfig(
        id="polygon",
        name="Polygon",
        chain_id=137,
        rpc_env="UAP_POLYGON_RPC_URL",
        tokens={
            "usdc": TokenConfig("0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359", 6),
            "usdt": TokenConfig("0xc2132D05D31c914a87C6611C10748AEb04B58e8F", 6),
        },
    ),
    "base": ChainConfig(
        id="base",
        name="Base",
        chain_id=8453,
        rpc_env="UAP_BASE_RPC_URL",
        tokens={
            "usdc": TokenConfig("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", 6),
            "usdt": TokenConfig("0xfde4C96c8593536E31F229EA8f37b2ADa2699bb2", 6),
        },
    ),
    "arbitrum": ChainConfig(
        id="arbitrum",
        name="Arbitrum One",
        chain_id=42161,
        rpc_env="UAP_ARBITRUM_RPC_URL",
        tokens={
            "usdc": TokenConfig("0xaf88d065e77c8cC2239327C5EDb3A432268e5831", 6),
            "usdt": TokenConfig("0xFd086bC7CD5C481DCC9CE238F8eDfAe86496D1C17", 6),
        },
    ),
    "bsc": ChainConfig(
        id="bsc",
        name="BNB Smart Chain",
        chain_id=56,
        rpc_env="UAP_BSC_RPC_URL",
        tokens={
            "usdc": TokenConfig("0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d", 18),
            "usdt": TokenConfig("0x55d398326f99059fF775485246999027B3197955", 18),
        },
    ),
}


def list_supported_networks() -> list[dict]:
    out: list[dict] = []
    for chain in CHAINS.values():
        out.append(
            {
                "id": chain.id,
                "name": chain.name,
                "chainId": chain.chain_id,
                "assets": sorted(chain.tokens.keys()),
                "rpcConfigured": bool(get_rpc_url(chain.id)),
            }
        )
    return out


def get_chain(network: str) -> ChainConfig | None:
    return CHAINS.get(str(network).lower())


def get_rpc_url(network: str) -> str:
    chain = get_chain(network)
    if chain is None:
        return ""
    return os.environ.get(chain.rpc_env, "").strip()


def get_token(network: str, asset: str) -> TokenConfig | None:
    chain = get_chain(network)
    if chain is None:
        return None
    return chain.tokens.get(str(asset).lower())


def validate_crypto_payment(*, network: str, asset: str) -> tuple[ChainConfig, TokenConfig]:
    chain = get_chain(network)
    if chain is None:
        supported = ", ".join(sorted(CHAINS.keys()))
        raise ValueError(f"unsupported network: {network} (supported: {supported})")
    token = chain.tokens.get(str(asset).lower())
    if token is None:
        supported_assets = ", ".join(sorted(chain.tokens.keys()))
        raise ValueError(
            f"unsupported asset {asset} on {network} (supported: {supported_assets})"
        )
    return chain, token


def build_pay_uri(
    *,
    network: str,
    receiver_wallet: str,
    token: TokenConfig,
    asset: str,
    amount: str,
    invoice_id: str,
) -> str:
    # EIP-681 style URI for wallet apps; chain id helps multi-chain wallets.
    chain = get_chain(network)
    chain_id = chain.chain_id if chain else 1
    return (
        f"ethereum:{token.address}@{chain_id}/transfer"
        f"?address={receiver_wallet}&uint256={amount.replace('.', '')}"
        f"&token={asset.upper()}&invoice={invoice_id}"
    )
