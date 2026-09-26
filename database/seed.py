from datetime import datetime
from sqlalchemy.orm import Session
from .connection import Base, engine, SessionLocal
from .models import DocumentRegistry, AuditRecord

def seed_database():
    """
    Seeds mock authority database with genuine, expired, stolen, and blacklisted records.
    """
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # Check if already seeded
        if db.query(DocumentRegistry).count() > 0:
            return

        mock_documents = [
            # 1. Genuine Active Passport
            DocumentRegistry(
                document_number="J82947192",
                holder_name="VIKRAM SHARMA",
                nationality="IND",
                date_of_birth="1994-08-14",
                expiry_date="2031-11-20",
                status="ACTIVE",
                blacklist_reason=None
            ),
            # 2. Expired Passport
            DocumentRegistry(
                document_number="E10293847",
                holder_name="ELENA ROSTOVA",
                nationality="RUS",
                date_of_birth="1988-03-22",
                expiry_date="2021-05-10",
                status="EXPIRED",
                blacklist_reason="Validity period expired."
            ),
            # 3. Blacklisted / Interpol Stolen Record
            DocumentRegistry(
                document_number="X99887766",
                holder_name="MARCUS VANCE",
                nationality="GBR",
                date_of_birth="1975-12-05",
                expiry_date="2029-08-18",
                status="BLACKLISTED",
                blacklist_reason="INTERPOL Red Notice: Wanted for transnational financial fraud."
            ),
            # 4. Stolen Blank / Revoked Document
            DocumentRegistry(
                document_number="S55443322",
                holder_name="UNKNOWN HOLDER",
                nationality="USA",
                date_of_birth="1990-01-01",
                expiry_date="2030-01-01",
                status="STOLEN",
                blacklist_reason="Reported stolen in transit by national passport agency."
            ),
            # 5. Genuine Secondary Traveler
            DocumentRegistry(
                document_number="A12345678",
                holder_name="ANANYA IYER",
                nationality="IND",
                date_of_birth="2001-02-18",
                expiry_date="2032-09-14",
                status="ACTIVE",
                blacklist_reason=None
            )
        ]

        db.add_all(mock_documents)
        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
