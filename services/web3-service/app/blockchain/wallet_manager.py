"""
Wallet Manager
Secure wallet creation and management
"""
from typing import Optional, Dict, Any, Tuple
from uuid import UUID, uuid4
from datetime import datetime
import secrets
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import structlog

from app.config import settings
from app.models.schemas import NetworkType, WalletResponse, WalletBalance, TokenBalance

logger = structlog.get_logger(__name__)


class WalletManager:
    """Secure wallet management"""
    
    def __init__(self):
        self._cipher = self._create_cipher()
        self._wallets: Dict[str, Dict[str, Any]] = {}  # In-memory storage (use DB in production)
    
    def _create_cipher(self) -> Fernet:
        """Create encryption cipher from key"""
        key = settings.WALLET_ENCRYPTION_KEY.encode()
        # Derive a proper key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'efinance_salt',  # In production, use unique salt per wallet
            iterations=100000,
        )
        derived_key = base64.urlsafe_b64encode(kdf.derive(key))
        return Fernet(derived_key)
    
    def _encrypt_private_key(self, private_key: str) -> str:
        """Encrypt private key for storage"""
        encrypted = self._cipher.encrypt(private_key.encode())
        return encrypted.decode()
    
    def _decrypt_private_key(self, encrypted_key: str) -> str:
        """Decrypt private key"""
        decrypted = self._cipher.decrypt(encrypted_key.encode())
        return decrypted.decode()
    
    async def create_wallet(
        self,
        user_id: UUID,
        network: NetworkType,
        label: Optional[str] = None
    ) -> Tuple[WalletResponse, str]:
        """
        Create a new wallet
        Returns wallet info and mnemonic (shown only once)
        """
        wallet_id = uuid4()
        
        if network == NetworkType.ETHEREUM:
            address, private_key, mnemonic = self._create_ethereum_wallet()
        elif network == NetworkType.BITCOIN:
            address, private_key, mnemonic = self._create_bitcoin_wallet()
        else:
            # Default to Ethereum-compatible
            address, private_key, mnemonic = self._create_ethereum_wallet()
        
        # Encrypt and store private key
        encrypted_key = self._encrypt_private_key(private_key)
        
        # Store wallet (in production, use database)
        self._wallets[str(wallet_id)] = {
            "id": wallet_id,
            "user_id": user_id,
            "address": address,
            "network": network,
            "encrypted_key": encrypted_key,
            "label": label,
            "is_active": True,
            "created_at": datetime.utcnow()
        }
        
        logger.info(
            "Wallet created",
            wallet_id=str(wallet_id),
            user_id=str(user_id),
            network=network.value,
            address=address
        )
        
        return WalletResponse(
            id=wallet_id,
            user_id=user_id,
            address=address,
            network=network,
            label=label,
            is_active=True,
            created_at=datetime.utcnow()
        ), mnemonic
    
    def _create_ethereum_wallet(self) -> Tuple[str, str, str]:
        """Create an Ethereum wallet"""
        try:
            from eth_account import Account
            Account.enable_unaudited_hdwallet_features()
            
            # Generate mnemonic
            account, mnemonic = Account.create_with_mnemonic()
            
            return account.address, account.key.hex(), mnemonic
        except ImportError:
            # Fallback for mock mode
            return self._create_mock_wallet()
    
    def _create_bitcoin_wallet(self) -> Tuple[str, str, str]:
        """Create a Bitcoin wallet"""
        # Simplified - in production use proper BIP39/BIP44
        return self._create_mock_wallet()
    
    def _create_mock_wallet(self) -> Tuple[str, str, str]:
        """Create a mock wallet for development"""
        private_key = "0x" + secrets.token_hex(32)
        address = "0x" + secrets.token_hex(20)
        mnemonic = " ".join(["word"] * 12)  # Mock mnemonic
        return address, private_key, mnemonic
    
    async def get_wallet(self, wallet_id: UUID) -> Optional[Dict[str, Any]]:
        """Get wallet by ID"""
        return self._wallets.get(str(wallet_id))
    
    async def get_user_wallets(self, user_id: UUID) -> list:
        """Get all wallets for a user"""
        return [
            WalletResponse(
                id=w["id"],
                user_id=w["user_id"],
                address=w["address"],
                network=w["network"],
                label=w["label"],
                is_active=w["is_active"],
                created_at=w["created_at"]
            )
            for w in self._wallets.values()
            if w["user_id"] == user_id
        ]
    
    async def get_wallet_balance(
        self,
        wallet_id: UUID,
        include_tokens: bool = True
    ) -> Optional[WalletBalance]:
        """Get wallet balance including tokens"""
        wallet = await self.get_wallet(wallet_id)
        if not wallet:
            return None
        
        from app.blockchain.ethereum import ethereum_client
        
        address = wallet["address"]
        network = wallet["network"]
        
        # Get native balance
        if network == NetworkType.ETHEREUM:
            native_balance = ethereum_client.get_balance(address)
            native_symbol = "ETH"
            native_formatted = f"{native_balance / 10**18:.6f}"
        elif network == NetworkType.BSC:
            native_balance = ethereum_client.get_balance(address)
            native_symbol = "BNB"
            native_formatted = f"{native_balance / 10**18:.6f}"
        else:
            native_balance = 0
            native_symbol = "???"
            native_formatted = "0"
        
        # Get token balances
        tokens = []
        if include_tokens and network in [NetworkType.ETHEREUM, NetworkType.BSC]:
            # Check common tokens
            token_addresses = [
                settings.USDT_CONTRACT,
                settings.USDC_CONTRACT,
            ]
            
            for token_addr in token_addresses:
                try:
                    balance = ethereum_client.get_token_balance(address, token_addr)
                    if balance > 0:
                        token_info = ethereum_client.get_token_info(token_addr)
                        tokens.append({
                            "contract_address": token_addr,
                            "symbol": token_info["symbol"],
                            "name": token_info["name"],
                            "decimals": token_info["decimals"],
                            "balance": str(balance),
                            "balance_formatted": f"{balance / 10**token_info['decimals']:.6f}"
                        })
                except Exception:
                    pass
        
        return WalletBalance(
            wallet_id=wallet_id,
            address=address,
            network=network,
            native_balance=str(native_balance),
            native_balance_formatted=native_formatted,
            native_symbol=native_symbol,
            tokens=tokens,
            last_updated=datetime.utcnow()
        )
    
    async def get_private_key(self, wallet_id: UUID) -> Optional[str]:
        """Get decrypted private key (use carefully!)"""
        wallet = await self.get_wallet(wallet_id)
        if not wallet:
            return None
        
        return self._decrypt_private_key(wallet["encrypted_key"])
    
    async def import_wallet(
        self,
        user_id: UUID,
        private_key: str,
        network: NetworkType,
        label: Optional[str] = None
    ) -> Optional[WalletResponse]:
        """Import existing wallet from private key"""
        wallet_id = uuid4()
        
        try:
            if network == NetworkType.ETHEREUM:
                from eth_account import Account
                account = Account.from_key(private_key)
                address = account.address
            else:
                address = "0x" + secrets.token_hex(20)  # Mock
            
            encrypted_key = self._encrypt_private_key(private_key)
            
            self._wallets[str(wallet_id)] = {
                "id": wallet_id,
                "user_id": user_id,
                "address": address,
                "network": network,
                "encrypted_key": encrypted_key,
                "label": label or "Imported Wallet",
                "is_active": True,
                "created_at": datetime.utcnow()
            }
            
            logger.info(
                "Wallet imported",
                wallet_id=str(wallet_id),
                user_id=str(user_id),
                address=address
            )
            
            return WalletResponse(
                id=wallet_id,
                user_id=user_id,
                address=address,
                network=network,
                label=label,
                is_active=True,
                created_at=datetime.utcnow()
            )
        except Exception as e:
            logger.error("Wallet import failed", error=str(e))
            return None
    
    async def deactivate_wallet(self, wallet_id: UUID) -> bool:
        """Deactivate a wallet"""
        wallet = await self.get_wallet(wallet_id)
        if not wallet:
            return False
        
        wallet["is_active"] = False
        logger.info("Wallet deactivated", wallet_id=str(wallet_id))
        return True


# Global wallet manager instance
wallet_manager = WalletManager()

