import pytest
from database.connection import Base, engine, SessionLocal
from database.models import DocumentRegistry
from database.seed import seed_database
from services.validation.validator import DocumentValidationService

@pytest.fixture(scope="module")
def db_session():
    Base.metadata.create_all(bind=engine)
    seed_database()
    db = SessionLocal()
    yield db
    db.close()

def test_validate_active_document(db_session):
    res = DocumentValidationService.validate_document(
        doc_number="J82947192",
        holder_name="VIKRAM SHARMA",
        dob_str="1994-08-14",
        expiry_str="2031-11-20",
        db=db_session
    )
    assert res["is_valid"] is True
    assert res["status"] == "VALID"
    assert len(res["flags"]) == 0

def test_validate_expired_document(db_session):
    res = DocumentValidationService.validate_document(
        doc_number="E10293847",
        holder_name="ELENA ROSTOVA",
        dob_str="1988-03-22",
        expiry_str="2021-05-10",
        db=db_session
    )
    assert res["is_valid"] is False
    assert res["status"] == "EXPIRED"
    assert any("expired" in f["detail"].lower() for f in res["flags"])

def test_validate_blacklisted_document(db_session):
    res = DocumentValidationService.validate_document(
        doc_number="X99887766",
        holder_name="MARCUS VANCE",
        dob_str="1975-12-05",
        expiry_str="2029-08-18",
        db=db_session
    )
    assert res["is_valid"] is False
    assert res["status"] == "BLACKLISTED"
    assert any(f["severity"] == "CRITICAL" for f in res["flags"])
