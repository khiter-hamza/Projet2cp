from fastapi import APIRouter

api_router = APIRouter()

# Example router inclusion:
from app.api.v1.endpoints import users , auth, notifications

api_router.include_router(users.router, prefix="/user", tags=["users"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

@api_router.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "api_version": "v1"}
