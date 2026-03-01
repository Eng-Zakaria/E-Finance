"""
Anti-Money Laundering (AML) Checker
Sanctions screening, PEP checking, and AML compliance
"""
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID, uuid4
import structlog

from app.config import settings
from app.models.schemas import (
    AMLCheckRequest, AMLCheckResult, RiskLevel
)

logger = structlog.get_logger(__name__)


class AMLChecker:
    """Anti-Money Laundering compliance checker"""
    
    # Simplified sanctions list (in production, use actual OFAC, EU, UN lists)
    SANCTIONS_KEYWORDS = [
        "terrorist", "sanctioned", "blocked", "prohibited"
    ]
    
    # High-risk countries for AML
    HIGH_RISK_COUNTRIES = {
        "AF", "BY", "BI", "CF", "CD", "CU", "IR", "IQ", "LB", "LY",
        "KP", "RU", "SO", "SS", "SD", "SY", "VE", "YE", "ZW"
    }
    
    # PEP indicators (simplified)
    PEP_TITLES = [
        "president", "prime minister", "minister", "senator",
        "congressman", "governor", "mayor", "ambassador",
        "general", "admiral", "judge", "director"
    ]
    
    def __init__(self):
        # In production, these would be loaded from external databases
        self.sanctions_list = self._load_sanctions_list()
        self.pep_database = self._load_pep_database()
    
    def _load_sanctions_list(self) -> Dict[str, Any]:
        """Load sanctions database (simplified mock)"""
        return {
            "entities": [],
            "individuals": [],
            "last_updated": datetime.utcnow()
        }
    
    def _load_pep_database(self) -> Dict[str, Any]:
        """Load PEP database (simplified mock)"""
        return {
            "individuals": [],
            "last_updated": datetime.utcnow()
        }
    
    async def check(self, request: AMLCheckRequest) -> AMLCheckResult:
        """
        Perform comprehensive AML check
        """
        check_id = uuid4()
        
        # Sanctions screening
        sanctions_hit, sanctions_matches = await self._screen_sanctions(request)
        
        # PEP screening
        pep_hit, pep_matches = await self._screen_pep(request)
        
        # Adverse media check (simplified)
        adverse_hit, adverse_matches = await self._check_adverse_media(request)
        
        # Calculate risk factors
        risk_factors = self._calculate_risk_factors(
            request, sanctions_hit, pep_hit, adverse_hit
        )
        
        # Determine overall risk
        overall_risk = self._determine_overall_risk(
            sanctions_hit, pep_hit, adverse_hit, risk_factors
        )
        
        # Determine required action
        action_required = sanctions_hit or (pep_hit and overall_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL])
        recommended_action = self._get_recommended_action(
            sanctions_hit, pep_hit, adverse_hit, overall_risk
        )
        
        logger.info(
            "AML check completed",
            user_id=str(request.user_id),
            check_id=str(check_id),
            sanctions_hit=sanctions_hit,
            pep_hit=pep_hit,
            overall_risk=overall_risk.value
        )
        
        return AMLCheckResult(
            user_id=request.user_id,
            check_id=check_id,
            sanctions_hit=sanctions_hit,
            sanctions_matches=sanctions_matches,
            pep_hit=pep_hit,
            pep_matches=pep_matches,
            adverse_media_hit=adverse_hit,
            adverse_media_matches=adverse_matches,
            overall_risk=overall_risk,
            risk_factors=risk_factors,
            action_required=action_required,
            recommended_action=recommended_action,
            checked_at=datetime.utcnow()
        )
    
    async def _screen_sanctions(
        self,
        request: AMLCheckRequest
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """Screen against sanctions lists"""
        matches = []
        
        # In production, would check against:
        # - OFAC SDN List
        # - EU Consolidated List
        # - UN Security Council Sanctions
        # - UK Sanctions List
        # - Country-specific lists
        
        # Simplified check - just check for high-risk country
        if request.nationality and request.nationality in self.HIGH_RISK_COUNTRIES:
            matches.append({
                "list": "high_risk_country",
                "matched_field": "nationality",
                "match_score": 0.9,
                "details": f"Nationality from high-risk jurisdiction: {request.nationality}"
            })
        
        if request.country_of_residence and request.country_of_residence in self.HIGH_RISK_COUNTRIES:
            matches.append({
                "list": "high_risk_country",
                "matched_field": "country_of_residence",
                "match_score": 0.9,
                "details": f"Resides in high-risk jurisdiction: {request.country_of_residence}"
            })
        
        return len(matches) > 0, matches
    
    async def _screen_pep(
        self,
        request: AMLCheckRequest
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """Screen for Politically Exposed Persons"""
        matches = []
        
        # In production, would check against PEP databases
        # Here we do a simplified name-based check
        
        name_lower = request.full_name.lower()
        
        for title in self.PEP_TITLES:
            if title in name_lower:
                matches.append({
                    "category": "potential_pep",
                    "matched_field": "full_name",
                    "match_score": 0.7,
                    "details": f"Name contains PEP indicator: {title}"
                })
                break
        
        return len(matches) > 0, matches
    
    async def _check_adverse_media(
        self,
        request: AMLCheckRequest
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """Check for adverse media coverage"""
        # In production, would integrate with:
        # - News APIs
        # - Adverse media databases
        # - Court records
        
        # Simplified - no adverse media check in demo
        return False, []
    
    def _calculate_risk_factors(
        self,
        request: AMLCheckRequest,
        sanctions_hit: bool,
        pep_hit: bool,
        adverse_hit: bool
    ) -> List[str]:
        """Calculate individual risk factors"""
        risk_factors = []
        
        if sanctions_hit:
            risk_factors.append("Potential sanctions list match")
        
        if pep_hit:
            risk_factors.append("Potential politically exposed person")
        
        if adverse_hit:
            risk_factors.append("Adverse media coverage found")
        
        if request.nationality in self.HIGH_RISK_COUNTRIES:
            risk_factors.append(f"High-risk nationality: {request.nationality}")
        
        if request.country_of_residence in self.HIGH_RISK_COUNTRIES:
            risk_factors.append(f"High-risk country of residence: {request.country_of_residence}")
        
        if request.transaction_amount and request.transaction_amount > settings.LARGE_TRANSACTION_THRESHOLD:
            risk_factors.append("Large transaction amount requires enhanced due diligence")
        
        return risk_factors
    
    def _determine_overall_risk(
        self,
        sanctions_hit: bool,
        pep_hit: bool,
        adverse_hit: bool,
        risk_factors: List[str]
    ) -> RiskLevel:
        """Determine overall AML risk level"""
        if sanctions_hit:
            return RiskLevel.CRITICAL
        
        risk_score = len(risk_factors)
        
        if adverse_hit:
            risk_score += 2
        
        if pep_hit:
            risk_score += 1
        
        if risk_score >= 4:
            return RiskLevel.HIGH
        elif risk_score >= 2:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _get_recommended_action(
        self,
        sanctions_hit: bool,
        pep_hit: bool,
        adverse_hit: bool,
        overall_risk: RiskLevel
    ) -> str:
        """Get recommended action based on check results"""
        if sanctions_hit:
            return "BLOCK - Potential sanctions violation. Escalate to compliance immediately."
        
        if overall_risk == RiskLevel.CRITICAL:
            return "BLOCK - Critical risk. Require enhanced due diligence before proceeding."
        
        if overall_risk == RiskLevel.HIGH:
            return "REVIEW - High risk. Request additional documentation and senior approval."
        
        if pep_hit:
            return "ENHANCED_DUE_DILIGENCE - PEP identified. Apply enhanced monitoring."
        
        if overall_risk == RiskLevel.MEDIUM:
            return "MONITOR - Standard due diligence with enhanced monitoring."
        
        return "APPROVE - Standard risk. Proceed with normal processing."
    
    async def check_transaction(
        self,
        user_id: UUID,
        transaction_amount: int,
        counterparty_name: Optional[str] = None,
        counterparty_country: Optional[str] = None
    ) -> Dict[str, Any]:
        """Quick transaction-level AML check"""
        flags = []
        risk_score = 0
        
        # Large transaction check
        if transaction_amount > settings.LARGE_TRANSACTION_THRESHOLD:
            flags.append("large_transaction")
            risk_score += 30
        
        # High-risk country check
        if counterparty_country and counterparty_country in self.HIGH_RISK_COUNTRIES:
            flags.append("high_risk_country")
            risk_score += 40
        
        # Would check counterparty against sanctions lists
        if counterparty_name:
            # Simplified check
            pass
        
        return {
            "transaction_cleared": risk_score < 50,
            "risk_score": risk_score,
            "flags": flags,
            "requires_review": risk_score >= 50,
            "checked_at": datetime.utcnow().isoformat()
        }


# Global AML checker instance
aml_checker = AMLChecker()

