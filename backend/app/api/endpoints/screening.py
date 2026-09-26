import uuid
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any

from database.connection import get_db
from backend.app.models.schemas import ScreeningResponse, OfficerDecisionRequest, OfficerDecisionResponse
from services.quality_gate.quality_checker import QualityGateService
from services.ocr_mrz.preprocessor import PreprocessorAndOCR
from services.ocr_mrz.mrz_parser import MRZParser
from services.validation.validator import DocumentValidationService
from services.tampering.tampering_suite import TamperingSuite
from services.face_verification.face_verifier import FaceVerificationService
from services.risk_engine.risk_scorer import ExplainableRiskEngine
from services.audit.audit_service import AuditService

router = APIRouter()

quality_service = QualityGateService()
tampering_suite = TamperingSuite()
face_verifier = FaceVerificationService()

@router.post("/screen", response_model=ScreeningResponse)
async def screen_document(
    document_image: UploadFile = File(...),
    live_selfie: Optional[UploadFile] = File(None),
    manual_mrz: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    End-to-End 7-Stage Screening Gateway Pipeline.
    """
    screening_id = f"SCR-{uuid.uuid4().hex[:8].upper()}"

    # 1. Read Bytes with size validation (< 15MB)
    doc_bytes = await document_image.read()
    if len(doc_bytes) > 15 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Document image exceeds 15MB size limit.")

    selfie_bytes = await live_selfie.read() if live_selfie else None

    # Stage 1: Quality Gate
    doc_quality = quality_service.assess_image(doc_bytes, "document_image")
    selfie_quality = quality_service.assess_image(selfie_bytes, "live_selfie") if selfie_bytes else None

    quality_summary = {
        "document_quality": doc_quality,
        "selfie_quality": selfie_quality,
        "passed": doc_quality.get("passed", False)
    }

    # Stage 2: OCR & MRZ Extraction
    ocr_result = PreprocessorAndOCR.process_and_parse(doc_bytes, manual_mrz=manual_mrz)
    extracted = ocr_result.get("extracted_fields", {}) or {}

    doc_num = extracted.get("document_number")
    holder_name = extracted.get("full_name")
    dob_str = extracted.get("date_of_birth")
    expiry_str = extracted.get("expiry_date")

    # Stage 3: Document & Database Validation
    val_result = DocumentValidationService.validate_document(
        doc_number=doc_num,
        holder_name=holder_name,
        dob_str=dob_str,
        expiry_str=expiry_str,
        db=db
    )

    # Stage 4: Tampering Suite (ELA, Copy-Move, Font, CNN)
    try:
        tamper_result = tampering_suite.run_all(doc_bytes)
    except Exception as e:
        tamper_result = {
            "overall_tamper_score": 0.0,
            "tamper_detected": False,
            "flags": [{
                "module": "tampering_detection",
                "check": "engine_health",
                "triggered": True,
                "severity": "LOW",
                "detail": f"Tampering engine encountered recoverable error: {str(e)}"
            }],
            "components": {}
        }

    # Stage 5: Face Verification
    try:
        face_result = face_verifier.compute_similarity(doc_bytes, selfie_bytes)
    except Exception as e:
        face_result = {
            "verified": False,
            "status": "ENGINE_ERROR",
            "similarity_score": 0.0,
            "flags": [{
                "module": "face_verification",
                "check": "engine_health",
                "triggered": True,
                "severity": "LOW",
                "detail": f"Face verifier encountered recoverable error: {str(e)}"
            }],
            "summary": "Biometrics module error."
        }

    # Stage 6: Explainable Risk Engine Aggregation
    risk_summary = ExplainableRiskEngine.calculate_risk(
        quality_res=quality_summary,
        ocr_mrz_res=ocr_result,
        validation_res=val_result,
        tampering_res=tamper_result,
        face_res=face_result
    )

    # Stage 7: Audit Persistence
    AuditService.record_screening(
        risk_result=risk_summary,
        doc_number=doc_num,
        holder_name=holder_name,
        db=db,
        screening_id=screening_id
    )

    return ScreeningResponse(
        screening_id=screening_id,
        risk_level=risk_summary["risk_level"],
        risk_score=risk_summary["risk_score"],
        recommended_action=risk_summary["recommended_action"],
        flags=risk_summary["flags"],
        weights_used=risk_summary["weights_used"],
        score_breakdown=risk_summary["score_breakdown"],
        module_results=risk_summary["module_results"]
    )

@router.post("/decision", response_model=OfficerDecisionResponse)
def submit_officer_decision(
    req: OfficerDecisionRequest,
    db: Session = Depends(get_db)
):
    """
    Records the final human-in-the-loop checkpoint decision.
    """
    success = AuditService.log_officer_decision(
        screening_id=req.screening_id,
        decision=req.decision,
        notes=req.notes,
        db=db
    )
    if not success:
        raise HTTPException(status_code=404, detail="Screening record not found.")

    return OfficerDecisionResponse(
        success=True,
        screening_id=req.screening_id,
        decision=req.decision,
        message="Officer decision recorded in immutable digital audit log."
    )

@router.get("/audit-trail")
def get_audit_records(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Returns recent screening audit logs for checkpoint inspection.
    """
    return AuditService.get_audit_trail(db=db, limit=limit)
