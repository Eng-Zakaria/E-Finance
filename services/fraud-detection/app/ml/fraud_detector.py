"""
Fraud Detection Engine
Combines ML models with rule-based detection
"""
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
from uuid import UUID, uuid4
import numpy as np
import structlog

from app.config import settings
from app.models.schemas import (
    TransactionAnalysisRequest, FraudScore, FraudAlert,
    RiskLevel, AlertType, UserRiskProfile
)
from app.ml.model_manager import model_manager
from app.ml.feature_engineering import feature_engineer, UserProfile

logger = structlog.get_logger(__name__)


class FraudDetector:
    """Main fraud detection engine"""
    
    def __init__(self):
        self.rules = self._load_default_rules()
    
    def _load_default_rules(self) -> List[Dict[str, Any]]:
        """Load default fraud detection rules"""
        return [
            {
                "id": "large_transaction",
                "name": "Large Transaction",
                "condition": lambda tx, _: tx.amount > settings.LARGE_TRANSACTION_THRESHOLD,
                "score_impact": 20,
                "alert_type": AlertType.UNUSUAL_AMOUNT,
                "flag": "large_transaction_amount"
            },
            {
                "id": "night_transaction",
                "name": "Night Transaction",
                "condition": lambda tx, _: tx.created_at.hour < 6 or tx.created_at.hour >= 22,
                "score_impact": 10,
                "alert_type": AlertType.UNUSUAL_TIME,
                "flag": "unusual_time"
            },
            {
                "id": "high_risk_country",
                "name": "High Risk Country",
                "condition": lambda tx, _: tx.location_country in feature_engineer.HIGH_RISK_COUNTRIES or 
                                           tx.counterparty_country in feature_engineer.HIGH_RISK_COUNTRIES,
                "score_impact": 30,
                "alert_type": AlertType.HIGH_RISK_COUNTRY,
                "flag": "high_risk_country"
            },
            {
                "id": "new_device",
                "name": "New Device",
                "condition": lambda tx, profile: tx.device_id and 
                                                  tx.device_id not in (profile.known_devices or []),
                "score_impact": 15,
                "alert_type": AlertType.DEVICE_CHANGE,
                "flag": "new_device"
            },
            {
                "id": "velocity_breach",
                "name": "Velocity Breach",
                "condition": lambda tx, profile: profile.transaction_count_24h > settings.MAX_DAILY_TRANSACTIONS,
                "score_impact": 25,
                "alert_type": AlertType.VELOCITY_BREACH,
                "flag": "velocity_breach"
            },
            {
                "id": "amount_velocity_breach",
                "name": "Amount Velocity Breach",
                "condition": lambda tx, profile: profile.transaction_amount_24h > settings.MAX_DAILY_AMOUNT,
                "score_impact": 25,
                "alert_type": AlertType.VELOCITY_BREACH,
                "flag": "amount_velocity_breach"
            },
            {
                "id": "crypto_large",
                "name": "Large Crypto Transaction",
                "condition": lambda tx, _: "crypto" in tx.transaction_type.lower() and 
                                           tx.amount > 500000,  # $5000
                "score_impact": 20,
                "alert_type": AlertType.UNUSUAL_AMOUNT,
                "flag": "large_crypto_transaction"
            },
            {
                "id": "international_large",
                "name": "Large International Transfer",
                "condition": lambda tx, _: tx.transaction_type == "international_transfer" and 
                                           tx.amount > 1000000,  # $10000
                "score_impact": 25,
                "alert_type": AlertType.MONEY_LAUNDERING,
                "flag": "large_international_transfer"
            },
        ]
    
    async def analyze_transaction(
        self,
        transaction: TransactionAnalysisRequest,
        user_profile: Optional[UserProfile] = None
    ) -> FraudScore:
        """
        Analyze a transaction for fraud
        Combines ML prediction with rule-based checks
        """
        start_time = datetime.utcnow()
        
        if user_profile is None:
            user_profile = UserProfile()
        
        # Extract features
        features = feature_engineer.extract_features(transaction, user_profile)
        
        # ML Model predictions
        fraud_probability = model_manager.predict_fraud(features)[0]
        anomaly_score = model_manager.detect_anomaly(features)[0]
        
        # Combined ML score (0-100)
        ml_score = (fraud_probability * 60 + anomaly_score * 40)
        
        # Apply rules
        rule_score, flags, triggered_rules = self._apply_rules(transaction, user_profile)
        
        # Combine scores (ML: 60%, Rules: 40%)
        final_score = min(ml_score * 0.6 + rule_score * 0.4, 100)
        
        # Determine risk level
        risk_level = self._calculate_risk_level(final_score)
        
        # Determine if suspicious
        is_suspicious = final_score >= settings.FRAUD_SCORE_THRESHOLD * 100
        requires_review = final_score >= settings.HIGH_RISK_THRESHOLD * 100
        
        # Generate reasons
        reasons = self._generate_reasons(
            transaction, fraud_probability, anomaly_score, triggered_rules
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            risk_level, triggered_rules, transaction
        )
        
        logger.info(
            "Transaction analyzed",
            transaction_id=str(transaction.transaction_id),
            risk_score=round(final_score, 2),
            risk_level=risk_level.value,
            is_suspicious=is_suspicious,
            flags=flags
        )
        
        return FraudScore(
            transaction_id=transaction.transaction_id,
            risk_score=round(final_score, 2),
            risk_level=risk_level,
            fraud_probability=round(fraud_probability, 4),
            is_suspicious=is_suspicious,
            requires_review=requires_review,
            flags=flags,
            reasons=reasons,
            recommendations=recommendations,
            model_version=model_manager.model_version,
            analyzed_at=datetime.utcnow()
        )
    
    def _apply_rules(
        self,
        transaction: TransactionAnalysisRequest,
        user_profile: UserProfile
    ) -> Tuple[float, List[str], List[Dict]]:
        """Apply rule-based fraud detection"""
        total_score = 0
        flags = []
        triggered_rules = []
        
        for rule in self.rules:
            try:
                if rule["condition"](transaction, user_profile):
                    total_score += rule["score_impact"]
                    flags.append(rule["flag"])
                    triggered_rules.append(rule)
            except Exception as e:
                logger.warning(
                    "Rule evaluation failed",
                    rule_id=rule["id"],
                    error=str(e)
                )
        
        return min(total_score, 100), flags, triggered_rules
    
    def _calculate_risk_level(self, score: float) -> RiskLevel:
        """Calculate risk level from score"""
        if score >= settings.CRITICAL_RISK_THRESHOLD * 100:
            return RiskLevel.CRITICAL
        elif score >= settings.HIGH_RISK_THRESHOLD * 100:
            return RiskLevel.HIGH
        elif score >= settings.FRAUD_SCORE_THRESHOLD * 100:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _generate_reasons(
        self,
        transaction: TransactionAnalysisRequest,
        fraud_prob: float,
        anomaly_score: float,
        triggered_rules: List[Dict]
    ) -> List[str]:
        """Generate human-readable reasons for the score"""
        reasons = []
        
        if fraud_prob > 0.5:
            reasons.append(f"ML model detected {int(fraud_prob * 100)}% fraud probability")
        
        if anomaly_score > 0.5:
            reasons.append(f"Anomaly detection flagged unusual behavior pattern")
        
        for rule in triggered_rules:
            reasons.append(f"Rule triggered: {rule['name']}")
        
        if transaction.amount > settings.LARGE_TRANSACTION_THRESHOLD:
            reasons.append(f"Transaction amount exceeds reporting threshold")
        
        return reasons
    
    def _generate_recommendations(
        self,
        risk_level: RiskLevel,
        triggered_rules: List[Dict],
        transaction: TransactionAnalysisRequest
    ) -> List[str]:
        """Generate action recommendations"""
        recommendations = []
        
        if risk_level == RiskLevel.CRITICAL:
            recommendations.append("BLOCK transaction immediately")
            recommendations.append("Alert compliance team")
            recommendations.append("Contact customer for verification")
        elif risk_level == RiskLevel.HIGH:
            recommendations.append("Hold transaction for manual review")
            recommendations.append("Request additional verification")
        elif risk_level == RiskLevel.MEDIUM:
            recommendations.append("Flag for monitoring")
            recommendations.append("Consider 2FA verification")
        
        # Rule-specific recommendations
        for rule in triggered_rules:
            if rule["id"] == "high_risk_country":
                recommendations.append("Verify destination/source country legitimacy")
            elif rule["id"] == "velocity_breach":
                recommendations.append("Review recent transaction history")
            elif rule["id"] == "new_device":
                recommendations.append("Verify device with customer")
        
        return list(set(recommendations))  # Remove duplicates
    
    async def create_alert(
        self,
        transaction: TransactionAnalysisRequest,
        fraud_score: FraudScore
    ) -> Optional[FraudAlert]:
        """Create a fraud alert if necessary"""
        if not fraud_score.is_suspicious:
            return None
        
        # Determine primary alert type
        alert_type = AlertType.UNUSUAL_PATTERN
        if "high_risk_country" in fraud_score.flags:
            alert_type = AlertType.HIGH_RISK_COUNTRY
        elif "velocity_breach" in fraud_score.flags:
            alert_type = AlertType.VELOCITY_BREACH
        elif "large_transaction_amount" in fraud_score.flags:
            alert_type = AlertType.UNUSUAL_AMOUNT
        elif "new_device" in fraud_score.flags:
            alert_type = AlertType.DEVICE_CHANGE
        
        alert = FraudAlert(
            id=uuid4(),
            transaction_id=transaction.transaction_id,
            account_id=transaction.account_id,
            user_id=transaction.user_id,
            alert_type=alert_type,
            severity=fraud_score.risk_level,
            title=f"{fraud_score.risk_level.value.upper()} Risk Transaction Detected",
            description="; ".join(fraud_score.reasons[:3]),
            flags=fraud_score.flags,
            risk_score=fraud_score.risk_score,
            status="open",
            created_at=datetime.utcnow(),
            metadata={
                "amount": transaction.amount,
                "currency": transaction.currency,
                "transaction_type": transaction.transaction_type,
                "recommendations": fraud_score.recommendations
            }
        )
        
        logger.warning(
            "Fraud alert created",
            alert_id=str(alert.id),
            transaction_id=str(transaction.transaction_id),
            alert_type=alert_type.value,
            severity=fraud_score.risk_level.value
        )
        
        return alert
    
    async def batch_analyze(
        self,
        transactions: List[TransactionAnalysisRequest]
    ) -> List[FraudScore]:
        """Analyze multiple transactions in batch"""
        results = []
        
        for tx in transactions:
            score = await self.analyze_transaction(tx)
            results.append(score)
        
        return results


# Global fraud detector instance
fraud_detector = FraudDetector()

