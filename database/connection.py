import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# PostgreSQL / SQLite adaptive support
# Render provides DATABASE_URL in postgres:// format, SQLAlchemy 2.0 requires postgresql://
raw_db_url = os.getenv("DATABASE_URL", "sqlite:///./screening_authority.db")
if raw_db_url.startswith("postgres://"):
    raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if "sqlite" in raw_db_url else {}

engine = create_engine(
    raw_db_url,
    connect_args=connect_args,
    pool_pre_ping=True if "postgresql" in raw_db_url else False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
