import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from database.models import AuditRecord

class AuditService:
    """
    Stage 7: Audit Service.
    Persists screening events, scores, and human officer decisions into digital audit logs.
    """

    @staticmethod
    def record_screening(
        risk_result: Dict[str, Any],
        doc_number: Optional[str],
        holder_name: Optional[str],
        db: Session,
        screening_id: Optional[str] = None
    ) -> str:
        s_id = screening_id or f"SCR-{uuid.uuid4().hex[:10].upper()}"

        audit_entry = AuditRecord(
            screening_id=s_id,
            timestamp=datetime.utcnow(),
            document_number=doc_number,
            holder_name=holder_name,
            risk_score=risk_result.get("risk_score", 0.0),
            risk_level=risk_result.get("risk_level", "Unknown"),
            recommended_action=risk_result.get("recommended_action", "officer_review"),
            officer_decision="AUTO_CLEARED" if risk_result.get("recommended_action") == "auto_clear" else "PENDING_OFFICER_REVIEW",
            triggered_flags=risk_result.get("flags", []),
            module_summaries=risk_result.get("score_breakdown", {})
        )

        db.add(audit_entry)
        db.commit()
        return s_id

    @staticmethod
    def log_officer_decision(
        screening_id: str,
        decision: str,
        notes: Optional[str],
        db: Session
    ) -> bool:
        record = db.query(AuditRecord).filter(AuditRecord.screening_id == screening_id).first()
        if not record:
            return False

        record.officer_decision = decision
        record.officer_notes = notes
        db.commit()
        return True

    @staticmethod
    def get_audit_trail(db: Session, limit: int = 50) -> List[Dict[str, Any]]:
        records = db.query(AuditRecord).order_by(AuditRecord.timestamp.desc()).limit(limit).all()
        return [
            {
                "screening_id": r.screening_id,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                "document_number": r.document_number or "N/A",
                "holder_name": r.holder_name or "N/A",
                "risk_score": r.risk_score,
                "risk_level": r.risk_level,
                "recommended_action": r.recommended_action,
                "officer_decision": r.officer_decision,
                "officer_notes": r.officer_notes,
                "flags_count": len(r.triggered_flags) if r.triggered_flags else 0
            }
            for r in records
        ]
