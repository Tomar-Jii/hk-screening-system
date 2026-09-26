from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class QualityCheckResponse(BaseModel):
    passed: bool
    target: str
    blur_score: float
    brightness_score: float
    issues: List[str] = []
    details: str

class FlagDetail(BaseModel):
    module: str
    check: str
    triggered: bool
    severity: Optional[str] = "MEDIUM"
    detail: Optional[str] = None
    similarity: Optional[float] = None
    threshold: Optional[float] = None

class ScreeningResponse(BaseModel):
    screening_id: str
    risk_level: str # Low, Medium, High
    risk_score: float
    recommended_action: str # auto_clear, officer_review
    flags: List[Dict[str, Any]] = []
    weights_used: Dict[str, float]
    score_breakdown: Dict[str, float]
    module_results: Dict[str, Any]

class OfficerDecisionRequest(BaseModel):
    screening_id: str
    decision: str # CLEARED, SECONDARY_REVIEW, REJECTED, ARREST_ISSUED
    notes: Optional[str] = None

class OfficerDecisionResponse(BaseModel):
    success: bool
    screening_id: str
    decision: str
    message: str
