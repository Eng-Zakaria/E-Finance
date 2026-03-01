"""
Pydantic Schemas for Fraud Detection
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID
from enum import Enum


class RiskLevel(str, Enum):
    """Risk level classification"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(str, Enum):
    """Fraud alert types"""
    UNUSUAL_AMOUNT = "unusual_amount"
    UNUSUAL_LOCATION = "unusual_location"
    UNUSUAL_TIME = "unusual_time"
    VELOCITY_BREACH = "velocity_breach"
    DEVICE_CHANGE = "device_change"
    ACCOUNT_TAKEOVER = "account_takeover"
    MONEY_LAUNDERING = "money_laundering"
    STRUCTURING = "structuring"
    HIGH_RISK_COUNTRY = "high_risk_country"
    SANCTIONS_HIT = "sanctions_hit"
    PEP_MATCH = "pep_match"
    UNUSUAL_PATTERN = "unusual_pattern"


class TransactionAnalysisRequest(BaseModel):
    """Request to analyze a transaction"""
    transaction_id: UUID
    account_id: UUID
    user_id: UUID
    amount: int = Field(..., description="Amount in cents")
    currency: str
    transaction_type: str
    channel: str
    
    # Optional context
    counterparty_account: Optional[str] = None
    counterparty_name: Optional[str] = None
    counterparty_country: Optional[str] = None
    
    # Device/Location info
    ip_address: Optional[str] = None
    device_id: Optional[str] = None
    device_type: Optional[str] = None
    location_country: Optional[str] = None
    location_city: Optional[str] = None
    geolocation: Optional[str] = None
    
    # Timestamps
    created_at: datetime


class FraudScore(BaseModel):
    """Fraud score response"""
    transaction_id: UUID
    risk_score: float = Field(..., ge=0, le=100)
    risk_level: RiskLevel
    fraud_probability: float = Field(..., ge=0, le=1)
    is_suspicious: bool
    requires_review: bool
    flags: List[str] = []
    reasons: List[str] = []
    recommendations: List[str] = []
    model_version: str
    analyzed_at: datetime


class FraudAlert(BaseModel):
    """Fraud alert"""
    id: UUID
    transaction_id: UUID
    account_id: UUID
    user_id: UUID
    alert_type: AlertType
    severity: RiskLevel
    title: str
    description: str
    flags: List[str]
    risk_score: float
    status: str = "open"
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None


class AMLCheckRequest(BaseModel):
    """AML check request"""
    user_id: UUID
    full_name: str
    date_of_birth: Optional[datetime] = None
    nationality: Optional[str] = None
    country_of_residence: Optional[str] = None
    id_type: Optional[str] = None
    id_number: Optional[str] = None
    
    # Transaction context
    transaction_id: Optional[UUID] = None
    transaction_amount: Optional[int] = None


class AMLCheckResult(BaseModel):
    """AML check result"""
    user_id: UUID
    check_id: UUID
    
    # Screening results
    sanctions_hit: bool
    sanctions_matches: List[Dict[str, Any]] = []
    
    pep_hit: bool
    pep_matches: List[Dict[str, Any]] = []
    
    adverse_media_hit: bool
    adverse_media_matches: List[Dict[str, Any]] = []
    
    # Risk assessment
    overall_risk: RiskLevel
    risk_factors: List[str] = []
    
    # Recommendations
    action_required: bool
    recommended_action: str
    
    checked_at: datetime


class UserRiskProfile(BaseModel):
    """User risk profile"""
    user_id: UUID
    
    # Overall risk
    risk_score: float
    risk_level: RiskLevel
    
    # Behavioral metrics
    avg_transaction_amount: float
    max_transaction_amount: int
    transaction_frequency: float  # per day
    typical_transaction_hours: List[int]
    typical_locations: List[str]
    typical_devices: List[str]
    
    # Anomaly indicators
    unusual_activity_count: int
    flagged_transactions_count: int
    false_positive_rate: float
    
    # Profile metadata
    profile_age_days: int
    last_updated: datetime
    transactions_analyzed: int


class RuleConfig(BaseModel):
    """Fraud detection rule configuration"""
    rule_id: str
    name: str
    description: str
    enabled: bool = True
    
    # Conditions
    conditions: Dict[str, Any]
    
    # Actions
    risk_score_impact: float
    alert_type: AlertType
    severity: RiskLevel
    
    # Metadata
    created_at: datetime
    updated_at: datetime


class BatchAnalysisRequest(BaseModel):
    """Batch transaction analysis request"""
    transactions: List[TransactionAnalysisRequest]


class BatchAnalysisResponse(BaseModel):
    """Batch analysis response"""
    total_analyzed: int
    suspicious_count: int
    results: List[FraudScore]
    processing_time_ms: float

