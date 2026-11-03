from fastapi import APIRouter

from app.routes import chat, documents, health

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(documents.router)
api_router.include_router(chat.router)
