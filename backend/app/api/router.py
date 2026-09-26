from fastapi import APIRouter
from backend.app.api.endpoints import screening

api_router = APIRouter()
api_router.include_router(screening.router, prefix="/screening", tags=["screening"])
