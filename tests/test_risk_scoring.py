import pytest
from services.risk_engine.risk_scorer import ExplainableRiskEngine

def test_risk_scoring_low_risk_auto_clear():
    quality_res = {"passed": True}
    ocr_mrz_res = {"extracted_fields": {"is_valid": True, "checksum_failures": []}}
    validation_res = {"is_valid": True, "status": "ACTIVE", "flags": []}
    tampering_res = {"overall_tamper_score": 0.05, "flags": []}
    face_res = {"status": "MATCH_CONFIRMED", "similarity_score": 0.92, "flags": []}

    risk = ExplainableRiskEngine.calculate_risk(
        quality_res, ocr_mrz_res, validation_res, tampering_res, face_res
    )

    assert risk["risk_level"] == "Low"
    assert risk["recommended_action"] == "auto_clear"
    assert risk["risk_score"] < 0.30
    assert len(risk["flags"]) == 0

def test_risk_scoring_blacklisted_document():
    quality_res = {"passed": True}
    ocr_mrz_res = {"extracted_fields": {"is_valid": True, "checksum_failures": []}}
    validation_res = {
        "is_valid": False,
        "status": "BLACKLISTED",
        "flags": [{"module": "validation", "check": "registry_blacklist_hit", "severity": "CRITICAL", "detail": "Interpol red notice."}]
    }
    tampering_res = {"overall_tamper_score": 0.1, "flags": []}
    face_res = {"status": "MATCH_CONFIRMED", "similarity_score": 0.88, "flags": []}

    risk = ExplainableRiskEngine.calculate_risk(
        quality_res, ocr_mrz_res, validation_res, tampering_res, face_res
    )

    assert risk["risk_level"] == "High"
    assert risk["recommended_action"] == "officer_review"
    assert risk["risk_score"] >= 0.90
    assert any(f["check"] == "registry_blacklist_hit" for f in risk["flags"])
