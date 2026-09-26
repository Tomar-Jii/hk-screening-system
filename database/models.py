import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON
from .connection import Base

class DocumentRegistry(Base):
    """
    Mock Government Authority Document Registry.
    Contains valid, expired, stolen, and blacklisted documents.
    """
    __tablename__ = "document_registry"

    id = Column(Integer, primary_key=True, index=True)
    document_number = Column(String(50), unique=True, index=True, nullable=False)
    holder_name = Column(String(100), nullable=False)
    nationality = Column(String(3), nullable=False)
    date_of_birth = Column(String(10), nullable=False) # YYYY-MM-DD
    expiry_date = Column(String(10), nullable=False)   # YYYY-MM-DD
    status = Column(String(30), default="ACTIVE")      # ACTIVE, EXPIRED, STOLEN, BLACKLISTED, REVOKED
    blacklist_reason = Column(String(255), nullable=True)
    issuing_authority = Column(String(50), default="ICAO_MOCK_AUTHORITY")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class AuditRecord(Base):
    """
    Immutable Digital Audit Log for Checkpoint Screening Events.
    """
    __tablename__ = "audit_records"

    id = Column(Integer, primary_key=True, index=True)
    screening_id = Column(String(64), unique=True, index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    document_number = Column(String(50), index=True, nullable=True)
    holder_name = Column(String(100), nullable=True)
    risk_score = Column(Float, nullable=False)
    risk_level = Column(String(20), nullable=False) # Low, Medium, High
    recommended_action = Column(String(50), nullable=False)
    officer_decision = Column(String(50), default="PENDING") # CLEARED, SECONDARY_REVIEW, REJECTED, ARREST_ISSUED
    officer_notes = Column(Text, nullable=True)
    triggered_flags = Column(JSON, default=list)
    module_summaries = Column(JSON, default=dict)
