from typing import Dict, Any, List

class ExplainableRiskEngine:
    """
    Stage 6: Explainable Risk Scoring Engine.
    Fuses MRZ checksum results, Database validation, 4 Forensic Tampering checks,
    and Face Verification into a single transparent score with complete explainability.
    """

    # Transparent weights
    WEIGHT_MRZ = 0.25
    WEIGHT_VALIDATION = 0.30
    WEIGHT_TAMPERING = 0.25
    WEIGHT_FACE = 0.20

    @classmethod
    def calculate_risk(
        cls,
        quality_res: Dict[str, Any],
        ocr_mrz_res: Dict[str, Any],
        validation_res: Dict[str, Any],
        tampering_res: Dict[str, Any],
        face_res: Dict[str, Any]
    ) -> Dict[str, Any]:
        flags: List[Dict[str, Any]] = []

        # 1. MRZ Contribution
        mrz_fields = ocr_mrz_res.get("extracted_fields", {}) or {}
        mrz_failures = mrz_fields.get("checksum_failures", [])
        mrz_valid = mrz_fields.get("is_valid", True)
        
        mrz_penalty = 0.0
        if not mrz_valid or len(mrz_failures) > 0:
            mrz_penalty = 1.0
            for fail in mrz_failures:
                flags.append({
                    "module": "mrz_checksum",
                    "check": "icao_9303_integrity",
                    "triggered": True,
                    "severity": "HIGH",
                    "detail": fail
                })

        # 2. Database / Authority Validation Contribution
        val_status = validation_res.get("status", "VALID")
        val_flags = validation_res.get("flags", [])
        flags.extend(val_flags)

        val_penalty = 0.0
        if val_status in ["BLACKLISTED", "STOLEN", "REVOKED"]:
            val_penalty = 1.0
        elif val_status == "EXPIRED":
            val_penalty = 0.8
        elif not validation_res.get("is_valid", True):
            val_penalty = 0.6

        # 3. Tampering Forensic Contribution
        tamper_flags = tampering_res.get("flags", [])
        flags.extend(tamper_flags)
        tamper_penalty = tampering_res.get("overall_tamper_score", 0.0)

        # 4. Face Verification Contribution
        face_status = face_res.get("status", "MATCH_CONFIRMED")
        face_flags = face_res.get("flags", [])
        flags.extend(face_flags)

        face_sim = face_res.get("similarity_score", 1.0)
        face_penalty = 0.0
        if face_status == "MISMATCH_ALERT":
            face_penalty = 1.0
        elif face_status == "BORDERLINE_REVIEW":
            face_penalty = 0.4
        elif face_status == "LIVE_PHOTO_MISSING":
            face_penalty = 0.2

        # Weighted calculation
        raw_score = (
            (mrz_penalty * cls.WEIGHT_MRZ) +
            (val_penalty * cls.WEIGHT_VALIDATION) +
            (tamper_penalty * cls.WEIGHT_TAMPERING) +
            (face_penalty * cls.WEIGHT_FACE)
        )

        # Critical override: A blacklisted document or failed MRZ checksum forces High Risk
        is_critical = any(f.get("severity") == "CRITICAL" for f in flags)
        if is_critical or val_status in ["BLACKLISTED", "STOLEN"]:
            raw_score = max(raw_score, 0.90)

        final_score = round(min(1.0, max(0.0, raw_score)), 3)

        # Determine Risk Level & Human-in-the-loop action
        if final_score < 0.30 and not is_critical and len(mrz_failures) == 0 and val_status == "ACTIVE":
            risk_level = "Low"
            recommended_action = "auto_clear"
        elif final_score < 0.65:
            risk_level = "Medium"
            recommended_action = "officer_review"
        else:
            risk_level = "High"
            recommended_action = "officer_review"

        return {
            "risk_level": risk_level,
            "risk_score": final_score,
            "recommended_action": recommended_action,
            "flags": flags,
            "weights_used": {
                "mrz": cls.WEIGHT_MRZ,
                "validation": cls.WEIGHT_VALIDATION,
                "tampering": cls.WEIGHT_TAMPERING,
                "face": cls.WEIGHT_FACE
            },
            "score_breakdown": {
                "mrz_contribution": round(mrz_penalty * cls.WEIGHT_MRZ, 3),
                "validation_contribution": round(val_penalty * cls.WEIGHT_VALIDATION, 3),
                "tampering_contribution": round(tamper_penalty * cls.WEIGHT_TAMPERING, 3),
                "face_contribution": round(face_penalty * cls.WEIGHT_FACE, 3)
            },
            "module_results": {
                "quality_gate": quality_res,
                "ocr_mrz": ocr_mrz_res,
                "validation": validation_res,
                "tampering": tampering_res,
                "face_verification": face_res
            }
        }
