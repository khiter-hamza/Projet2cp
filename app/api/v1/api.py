from fastapi import APIRouter


api_router = APIRouter()

# Example router inclusion:
from app.api.v1.endpoints import users , auth , applications , documents,sessions

api_router.include_router(users.router, prefix="/user", tags=["users"])

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

api_router.include_router(applications.router , prefix="/applications" , tags=["applications"])

api_router.include_router(documents.router, prefix="", tags=["documents"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])

@api_router.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "api_version": "v1"}
