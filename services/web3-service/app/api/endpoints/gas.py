"""
Gas Price Endpoints
"""
from datetime import datetime
from fastapi import APIRouter

from app.models.schemas import GasPrice, NetworkType
from app.blockchain.ethereum import ethereum_client

router = APIRouter()


@router.get("/prices", response_model=GasPrice)
async def get_gas_prices(network: NetworkType = NetworkType.ETHEREUM):
    """
    Get current gas prices for a network.
    """
    prices = await ethereum_client.get_gas_prices()
    
    return GasPrice(
        network=network,
        slow=prices["slow"],
        standard=prices["standard"],
        fast=prices["fast"],
        instant=prices["instant"],
        base_fee=None,  # Would get from EIP-1559 base fee
        last_updated=datetime.utcnow()
    )


@router.get("/estimate", response_model=dict)
async def estimate_transaction_cost(
    network: NetworkType = NetworkType.ETHEREUM,
    gas_limit: int = 21000
):
    """
    Estimate transaction cost in native token.
    """
    prices = await ethereum_client.get_gas_prices()
    
    # Calculate costs in wei and ETH
    costs = {}
    for speed, gwei in prices.items():
        wei = gwei * 1_000_000_000 * gas_limit
        eth = wei / 10**18
        costs[speed] = {
            "gas_price_gwei": gwei,
            "gas_limit": gas_limit,
            "cost_wei": str(wei),
            "cost_eth": f"{eth:.6f}"
        }
    
    return {
        "network": network.value,
        "estimates": costs,
        "timestamp": datetime.utcnow().isoformat()
    }

