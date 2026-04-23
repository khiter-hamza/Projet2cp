from fastapi import APIRouter


api_router = APIRouter()

# Example router inclusion:
from app.api.v1.endpoints import users , auth , applications , documents, sessions, cs, notifications, dashboard, history
from app.api.v1.endpoints import users , auth, notifications
from app.api.v1.endpoints import sessions
from app.api.v1.endpoints import documents
from app.api.v1.endpoints import applications
from app.api.v1.endpoints import eligibility
from app.api.v1.endpoints import idemnity
from app.api.v1.endpoints import cs
from app.api.v1.endpoints import dashboard
from app.api.v1.endpoints import history


@api_router.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}


api_router.include_router(users.router, prefix="/user", tags=["users"])

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# History must come before applications (before /{id} catch-all route)
api_router.include_router(history.router, prefix="/applications", tags=["history"])
api_router.include_router(applications.router , prefix="/applications" , tags=["applications"])

api_router.include_router(documents.router, prefix="", tags=["documents"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(eligibility.router, prefix="/applications", tags=["eligibility"])
api_router.include_router(idemnity.app , prefix="/idemnity" , tags=["budjet and zones"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(cs.router, prefix="/cs", tags=["cs-operations"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
