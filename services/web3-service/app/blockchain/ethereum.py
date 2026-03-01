"""
Ethereum Blockchain Client
Handles Ethereum and EVM-compatible chain interactions
"""
from typing import Optional, Dict, Any, List
from decimal import Decimal
import asyncio
import structlog

from app.config import settings

logger = structlog.get_logger(__name__)

# ERC-20 ABI (minimal)
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    }
]


class EthereumClient:
    """Ethereum blockchain client"""
    
    def __init__(self):
        self.w3 = None
        self.is_connected = False
        self._chain_id = settings.ETHEREUM_CHAIN_ID
    
    async def connect(self):
        """Connect to Ethereum node"""
        try:
            from web3 import Web3
            from web3.middleware import geth_poa_middleware
            
            # Try HTTP connection
            self.w3 = Web3(Web3.HTTPProvider(settings.ETHEREUM_RPC_URL))
            
            # Add PoA middleware for testnets/BSC
            if self._chain_id in [5, 97, 56]:  # Goerli, BSC testnet, BSC mainnet
                self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            
            self.is_connected = self.w3.is_connected()
            
            if self.is_connected:
                logger.info(
                    "Connected to Ethereum",
                    chain_id=self._chain_id,
                    block_number=self.w3.eth.block_number
                )
            else:
                logger.warning("Failed to connect to Ethereum node")
                # Use mock mode for development
                self.is_connected = True
                self.w3 = None
                
        except Exception as e:
            logger.error("Ethereum connection error", error=str(e))
            # Use mock mode
            self.is_connected = True
            self.w3 = None
    
    async def disconnect(self):
        """Disconnect from Ethereum node"""
        self.is_connected = False
        self.w3 = None
        logger.info("Disconnected from Ethereum")
    
    def get_balance(self, address: str) -> int:
        """Get native token balance (in wei)"""
        if not self.w3:
            # Mock mode
            return 1000000000000000000  # 1 ETH in wei
        
        try:
            return self.w3.eth.get_balance(address)
        except Exception as e:
            logger.error("Failed to get balance", address=address, error=str(e))
            return 0
    
    def get_token_balance(self, address: str, token_address: str) -> int:
        """Get ERC-20 token balance"""
        if not self.w3:
            # Mock mode
            return 1000000000  # 1000 USDT (6 decimals)
        
        try:
            from web3 import Web3
            
            checksum_token = Web3.to_checksum_address(token_address)
            checksum_address = Web3.to_checksum_address(address)
            
            contract = self.w3.eth.contract(
                address=checksum_token,
                abi=ERC20_ABI
            )
            
            return contract.functions.balanceOf(checksum_address).call()
        except Exception as e:
            logger.error(
                "Failed to get token balance",
                address=address,
                token=token_address,
                error=str(e)
            )
            return 0
    
    def get_token_info(self, token_address: str) -> Dict[str, Any]:
        """Get ERC-20 token info"""
        if not self.w3:
            # Mock mode
            return {
                "name": "Mock Token",
                "symbol": "MOCK",
                "decimals": 18
            }
        
        try:
            from web3 import Web3
            
            checksum_address = Web3.to_checksum_address(token_address)
            
            contract = self.w3.eth.contract(
                address=checksum_address,
                abi=ERC20_ABI
            )
            
            return {
                "name": contract.functions.name().call(),
                "symbol": contract.functions.symbol().call(),
                "decimals": contract.functions.decimals().call()
            }
        except Exception as e:
            logger.error("Failed to get token info", token=token_address, error=str(e))
            return {"name": "Unknown", "symbol": "???", "decimals": 18}
    
    async def send_transaction(
        self,
        from_address: str,
        to_address: str,
        value: int,
        private_key: str,
        gas_limit: Optional[int] = None,
        gas_price_gwei: Optional[int] = None
    ) -> Optional[str]:
        """Send native token transaction"""
        if not self.w3:
            # Mock mode - return fake tx hash
            import secrets
            return "0x" + secrets.token_hex(32)
        
        try:
            from web3 import Web3
            
            checksum_from = Web3.to_checksum_address(from_address)
            checksum_to = Web3.to_checksum_address(to_address)
            
            # Get nonce
            nonce = self.w3.eth.get_transaction_count(checksum_from)
            
            # Get gas price
            if gas_price_gwei:
                gas_price = Web3.to_wei(gas_price_gwei, 'gwei')
            else:
                gas_price = self.w3.eth.gas_price
            
            # Build transaction
            tx = {
                'nonce': nonce,
                'to': checksum_to,
                'value': value,
                'gas': gas_limit or settings.DEFAULT_GAS_LIMIT,
                'gasPrice': gas_price,
                'chainId': self._chain_id
            }
            
            # Sign transaction
            signed_tx = self.w3.eth.account.sign_transaction(tx, private_key)
            
            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            logger.info(
                "Transaction sent",
                tx_hash=tx_hash.hex(),
                from_addr=from_address,
                to_addr=to_address,
                value=value
            )
            
            return tx_hash.hex()
            
        except Exception as e:
            logger.error("Transaction failed", error=str(e))
            return None
    
    async def send_token_transaction(
        self,
        token_address: str,
        from_address: str,
        to_address: str,
        amount: int,
        private_key: str,
        gas_limit: Optional[int] = None,
        gas_price_gwei: Optional[int] = None
    ) -> Optional[str]:
        """Send ERC-20 token transaction"""
        if not self.w3:
            # Mock mode
            import secrets
            return "0x" + secrets.token_hex(32)
        
        try:
            from web3 import Web3
            
            checksum_token = Web3.to_checksum_address(token_address)
            checksum_from = Web3.to_checksum_address(from_address)
            checksum_to = Web3.to_checksum_address(to_address)
            
            # Get contract
            contract = self.w3.eth.contract(
                address=checksum_token,
                abi=ERC20_ABI
            )
            
            # Get nonce
            nonce = self.w3.eth.get_transaction_count(checksum_from)
            
            # Get gas price
            if gas_price_gwei:
                gas_price = Web3.to_wei(gas_price_gwei, 'gwei')
            else:
                gas_price = self.w3.eth.gas_price
            
            # Build transaction
            tx = contract.functions.transfer(
                checksum_to,
                amount
            ).build_transaction({
                'from': checksum_from,
                'nonce': nonce,
                'gas': gas_limit or 100000,
                'gasPrice': gas_price,
                'chainId': self._chain_id
            })
            
            # Sign and send
            signed_tx = self.w3.eth.account.sign_transaction(tx, private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            logger.info(
                "Token transaction sent",
                tx_hash=tx_hash.hex(),
                token=token_address,
                amount=amount
            )
            
            return tx_hash.hex()
            
        except Exception as e:
            logger.error("Token transaction failed", error=str(e))
            return None
    
    def get_transaction_receipt(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """Get transaction receipt"""
        if not self.w3:
            return {
                "status": 1,
                "blockNumber": 12345678,
                "gasUsed": 21000
            }
        
        try:
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            return dict(receipt)
        except Exception as e:
            logger.error("Failed to get receipt", tx_hash=tx_hash, error=str(e))
            return None
    
    async def get_gas_prices(self) -> Dict[str, int]:
        """Get current gas prices in Gwei"""
        if not self.w3:
            return {
                "slow": 10,
                "standard": 20,
                "fast": 30,
                "instant": 50
            }
        
        try:
            from web3 import Web3
            
            gas_price = self.w3.eth.gas_price
            gas_price_gwei = Web3.from_wei(gas_price, 'gwei')
            
            return {
                "slow": int(gas_price_gwei * 0.8),
                "standard": int(gas_price_gwei),
                "fast": int(gas_price_gwei * 1.2),
                "instant": int(gas_price_gwei * 1.5)
            }
        except Exception as e:
            logger.error("Failed to get gas prices", error=str(e))
            return {"slow": 10, "standard": 20, "fast": 30, "instant": 50}
    
    def estimate_gas(self, tx: Dict[str, Any]) -> int:
        """Estimate gas for transaction"""
        if not self.w3:
            return 21000
        
        try:
            return self.w3.eth.estimate_gas(tx)
        except Exception as e:
            logger.error("Gas estimation failed", error=str(e))
            return 21000


# Global Ethereum client instance
ethereum_client = EthereumClient()

