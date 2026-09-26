from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from database.models import DocumentRegistry

class DocumentValidationService:
    """
    Stage 3: Cross-validates extracted document fields against standard business rules,
    date sanity, and mock authority blacklists.
    """

    @classmethod
    def validate_document(
        cls,
        doc_number: Optional[str],
        holder_name: Optional[str],
        dob_str: Optional[str],
        expiry_str: Optional[str],
        db: Session
    ) -> Dict[str, Any]:
        """
        Validates the document against rules & mock registry.
        """
        flags: List[Dict[str, Any]] = []
        is_valid = True
        status_category = "VALID"

        # 1. Check Document Number Presence
        if not doc_number or len(doc_number.strip()) < 5:
            flags.append({
                "module": "validation",
                "check": "doc_number_presence",
                "triggered": True,
                "severity": "HIGH",
                "detail": "Document number is missing, empty, or unreadable."
            })
            return {
                "is_valid": False,
                "status": "UNREADABLE",
                "flags": flags,
                "registry_record": None
            }

        cleaned_doc_num = doc_number.strip().upper()

        # 2. Expiration Date Sanity Check
        if expiry_str:
            try:
                exp_date = datetime.strptime(expiry_str, "%Y-%m-%d").date()
                today = datetime.utcnow().date()
                if exp_date < today:
                    is_valid = False
                    status_category = "EXPIRED"
                    flags.append({
                        "module": "validation",
                        "check": "expiration_check",
                        "triggered": True,
                        "severity": "HIGH",
                        "detail": f"Document expired on {expiry_str} (current system date: {today.isoformat()})."
                    })
            except ValueError:
                flags.append({
                    "module": "validation",
                    "check": "expiration_format",
                    "triggered": True,
                    "severity": "MEDIUM",
                    "detail": f"Unrecognized expiration date format: {expiry_str}"
                })

        # 3. Date of Birth Sanity Check
        if dob_str:
            try:
                dob_date = datetime.strptime(dob_str, "%Y-%m-%d").date()
                today = datetime.utcnow().date()
                if dob_date > today:
                    is_valid = False
                    flags.append({
                        "module": "validation",
                        "check": "dob_future_check",
                        "triggered": True,
                        "severity": "HIGH",
                        "detail": f"Date of birth is in the future ({dob_str})."
                    })
                age = (today - dob_date).days // 365
                if age < 0 or age > 120:
                    flags.append({
                        "module": "validation",
                        "check": "dob_age_plausibility",
                        "triggered": True,
                        "severity": "MEDIUM",
                        "detail": f"Holder calculated age ({age} years) is outside plausible human travel range."
                    })
            except ValueError:
                pass

        # 4. Mock Database / Authority Registry Lookup
        record = db.query(DocumentRegistry).filter(DocumentRegistry.document_number == cleaned_doc_num).first()

        registry_info = None
        if record:
            registry_info = {
                "document_number": record.document_number,
                "registered_name": record.holder_name,
                "registered_nationality": record.nationality,
                "status": record.status,
                "blacklist_reason": record.blacklist_reason
            }

            if record.status in ["BLACKLISTED", "STOLEN", "REVOKED"]:
                is_valid = False
                status_category = record.status
                flags.append({
                    "module": "validation",
                    "check": "registry_blacklist_hit",
                    "triggered": True,
                    "severity": "CRITICAL",
                    "detail": f"CRITICAL: Document {cleaned_doc_num} is flagged as {record.status}. Reason: {record.blacklist_reason or 'Authority alert.'}"
                })
            elif record.status == "EXPIRED":
                is_valid = False
                status_category = "EXPIRED"
                flags.append({
                    "module": "validation",
                    "check": "registry_expired_hit",
                    "triggered": True,
                    "severity": "HIGH",
                    "detail": f"Document {cleaned_doc_num} marked as expired in central registry."
                })

            # Cross-verify name if available
            if holder_name and record.holder_name:
                cleaned_scanned_name = "".join(filter(str.isalnum, holder_name.upper()))
                cleaned_reg_name = "".join(filter(str.isalnum, record.holder_name.upper()))
                if cleaned_scanned_name and cleaned_reg_name and (cleaned_scanned_name not in cleaned_reg_name and cleaned_reg_name not in cleaned_scanned_name):
                    flags.append({
                        "module": "validation",
                        "check": "registry_name_mismatch",
                        "triggered": True,
                        "severity": "HIGH",
                        "detail": f"Holder name '{holder_name}' does not match registered name '{record.holder_name}' for document {cleaned_doc_num}."
                    })
        else:
            # Document not found in local mock cache
            registry_info = {
                "document_number": cleaned_doc_num,
                "status": "NOT_FOUND_IN_CACHE",
                "detail": "Document not pre-cached in local mock registry (normal for unfamiliar foreign passports)."
            }

        return {
            "is_valid": is_valid,
            "status": status_category,
            "flags": flags,
            "registry_record": registry_info
        }
