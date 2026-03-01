"""
Feature Engineering for Fraud Detection
Transforms raw transaction data into ML features
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import numpy as np
from dataclasses import dataclass

from app.models.schemas import TransactionAnalysisRequest


@dataclass
class UserProfile:
    """User behavioral profile for feature calculation"""
    avg_transaction_amount: float = 0.0
    std_transaction_amount: float = 0.0
    max_transaction_amount: float = 0.0
    transaction_count_24h: int = 0
    transaction_amount_24h: float = 0.0
    typical_hours: List[int] = None
    typical_countries: List[str] = None
    known_devices: List[str] = None
    account_age_days: int = 0
    
    def __post_init__(self):
        if self.typical_hours is None:
            self.typical_hours = list(range(8, 22))  # Default business hours
        if self.typical_countries is None:
            self.typical_countries = ["US"]
        if self.known_devices is None:
            self.known_devices = []


class FeatureEngineer:
    """Feature engineering for transaction fraud detection"""
    
    # High-risk countries for AML
    HIGH_RISK_COUNTRIES = {
        "IR", "KP", "SY", "CU", "VE", "MM", "BY", "RU", "AF", "IQ",
        "LB", "LY", "SD", "SO", "SS", "YE", "ZW"
    }
    
    # Features for the ML model
    FEATURE_NAMES = [
        "amount_normalized",
        "amount_zscore",
        "hour_of_day",
        "day_of_week",
        "is_weekend",
        "is_night_transaction",
        "velocity_24h_count",
        "velocity_24h_amount",
        "is_new_device",
        "is_new_location",
        "is_high_risk_country",
        "amount_to_avg_ratio",
        "is_round_amount",
        "transaction_type_risk",
        "channel_risk"
    ]
    
    # Transaction type risk scores
    TRANSACTION_TYPE_RISK = {
        "deposit": 0.1,
        "withdrawal": 0.3,
        "transfer_in": 0.1,
        "transfer_out": 0.4,
        "payment": 0.3,
        "international_transfer": 0.6,
        "crypto_buy": 0.5,
        "crypto_sell": 0.5,
        "crypto_transfer": 0.7,
        "atm_withdrawal": 0.4,
        "card_purchase": 0.3,
    }
    
    # Channel risk scores
    CHANNEL_RISK = {
        "web": 0.3,
        "mobile": 0.3,
        "api": 0.4,
        "atm": 0.4,
        "pos": 0.2,
        "branch": 0.1,
        "automated": 0.2,
    }
    
    def __init__(self):
        self.user_profiles: Dict[str, UserProfile] = {}
    
    def extract_features(
        self,
        transaction: TransactionAnalysisRequest,
        user_profile: Optional[UserProfile] = None
    ) -> np.ndarray:
        """Extract features from a transaction"""
        
        if user_profile is None:
            user_profile = UserProfile()
        
        features = []
        
        # 1. Amount normalized (assuming max reasonable amount of $100,000)
        amount_normalized = min(transaction.amount / 10000000, 1.0)
        features.append(amount_normalized)
        
        # 2. Amount z-score relative to user's history
        if user_profile.std_transaction_amount > 0:
            amount_zscore = (transaction.amount - user_profile.avg_transaction_amount) / user_profile.std_transaction_amount
            amount_zscore = min(max(amount_zscore / 10, -1), 1)  # Normalize to [-1, 1]
        else:
            amount_zscore = 0.0
        features.append(amount_zscore)
        
        # 3. Hour of day (normalized to 0-1)
        hour = transaction.created_at.hour
        features.append(hour / 24)
        
        # 4. Day of week (normalized to 0-1)
        day_of_week = transaction.created_at.weekday()
        features.append(day_of_week / 6)
        
        # 5. Is weekend
        features.append(1.0 if day_of_week >= 5 else 0.0)
        
        # 6. Is night transaction (10 PM - 6 AM)
        is_night = 1.0 if hour < 6 or hour >= 22 else 0.0
        features.append(is_night)
        
        # 7. Velocity - transaction count in 24h (normalized)
        velocity_count = min(user_profile.transaction_count_24h / 50, 1.0)
        features.append(velocity_count)
        
        # 8. Velocity - amount in 24h (normalized)
        velocity_amount = min(user_profile.transaction_amount_24h / 10000000, 1.0)
        features.append(velocity_amount)
        
        # 9. Is new device
        is_new_device = 0.0
        if transaction.device_id and user_profile.known_devices:
            is_new_device = 0.0 if transaction.device_id in user_profile.known_devices else 1.0
        features.append(is_new_device)
        
        # 10. Is new location
        is_new_location = 0.0
        if transaction.location_country and user_profile.typical_countries:
            is_new_location = 0.0 if transaction.location_country in user_profile.typical_countries else 1.0
        features.append(is_new_location)
        
        # 11. Is high-risk country
        is_high_risk = 0.0
        if transaction.location_country:
            is_high_risk = 1.0 if transaction.location_country in self.HIGH_RISK_COUNTRIES else 0.0
        if transaction.counterparty_country:
            if transaction.counterparty_country in self.HIGH_RISK_COUNTRIES:
                is_high_risk = 1.0
        features.append(is_high_risk)
        
        # 12. Amount to average ratio
        if user_profile.avg_transaction_amount > 0:
            amount_ratio = min(transaction.amount / user_profile.avg_transaction_amount / 10, 1.0)
        else:
            amount_ratio = 0.5
        features.append(amount_ratio)
        
        # 13. Is round amount (often indicates money laundering)
        is_round = self._is_round_amount(transaction.amount)
        features.append(is_round)
        
        # 14. Transaction type risk
        tx_type_risk = self.TRANSACTION_TYPE_RISK.get(transaction.transaction_type.lower(), 0.5)
        features.append(tx_type_risk)
        
        # 15. Channel risk
        channel_risk = self.CHANNEL_RISK.get(transaction.channel.lower(), 0.5)
        features.append(channel_risk)
        
        return np.array(features).reshape(1, -1)
    
    def _is_round_amount(self, amount: int) -> float:
        """Check if amount is suspiciously round (potential structuring)"""
        # Convert to dollars
        dollars = amount / 100
        
        # Check for round thousands
        if dollars >= 1000 and dollars % 1000 == 0:
            return 1.0
        
        # Check for round hundreds
        if dollars >= 100 and dollars % 100 == 0:
            return 0.7
        
        # Check for round tens
        if dollars >= 10 and dollars % 10 == 0:
            return 0.3
        
        return 0.0
    
    def calculate_velocity_score(
        self,
        transaction_count_24h: int,
        transaction_amount_24h: int,
        max_count: int = 50,
        max_amount: int = 5000000  # $50,000
    ) -> float:
        """Calculate velocity-based risk score"""
        count_score = min(transaction_count_24h / max_count, 1.0)
        amount_score = min(transaction_amount_24h / max_amount, 1.0)
        
        return (count_score + amount_score) / 2
    
    def detect_structuring(
        self,
        recent_transactions: List[Dict[str, Any]],
        threshold: int = 950000  # Just under $10,000
    ) -> bool:
        """
        Detect potential structuring (breaking up transactions to avoid reporting)
        """
        if len(recent_transactions) < 2:
            return False
        
        # Check for multiple transactions just under threshold
        near_threshold_count = sum(
            1 for tx in recent_transactions
            if threshold * 0.8 <= tx['amount'] <= threshold
        )
        
        if near_threshold_count >= 2:
            return True
        
        # Check if sum of recent transactions exceeds threshold
        total_amount = sum(tx['amount'] for tx in recent_transactions)
        if total_amount > threshold * 1.5 and len(recent_transactions) >= 3:
            # Check if individual transactions are smaller
            avg_amount = total_amount / len(recent_transactions)
            if avg_amount < threshold:
                return True
        
        return False
    
    def calculate_time_pattern_score(
        self,
        transaction_hour: int,
        typical_hours: List[int]
    ) -> float:
        """Calculate score based on time pattern deviation"""
        if transaction_hour in typical_hours:
            return 0.0
        
        # Calculate distance to nearest typical hour
        min_distance = min(
            abs(transaction_hour - h) for h in typical_hours
        ) if typical_hours else 12
        
        # Normalize: further = higher risk
        return min(min_distance / 12, 1.0)
    
    def calculate_location_risk(
        self,
        current_country: Optional[str],
        typical_countries: List[str],
        geolocation: Optional[str] = None
    ) -> Dict[str, float]:
        """Calculate location-based risk factors"""
        risk = {
            "new_country": 0.0,
            "high_risk_country": 0.0,
            "impossible_travel": 0.0
        }
        
        if not current_country:
            return risk
        
        # New country
        if current_country not in typical_countries:
            risk["new_country"] = 0.7
        
        # High-risk country
        if current_country in self.HIGH_RISK_COUNTRIES:
            risk["high_risk_country"] = 0.9
        
        # Impossible travel detection would require previous transaction location
        # and time comparison - simplified here
        
        return risk


# Global feature engineer instance
feature_engineer = FeatureEngineer()

