import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

class Settings:
    PROJECT_NAME: str = "AI-Based Fake Identity & Document Screening System (SIH26188)"
    PROJECT_VERSION: str = "1.0.0"
    TEAM_NAME: str = "Da Vinci Code"
    TEAM_ID: str = "139735"
    PROBLEM_STATEMENT_ID: str = "SIH26188"
    API_V1_STR: str = "/api/v1"
    
    # Render PORT support
    PORT: int = int(os.getenv("PORT", 8000))
    
    # Environment CORS support
    raw_cors = os.getenv("CORS_ORIGINS", "*")
    CORS_ORIGINS: list[str] = [origin.strip() for origin in raw_cors.split(",") if origin.strip()] if raw_cors != "*" else ["*"]
    
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'screening_authority.db')}")

settings = Settings()
