from fastapi import APIRouter


api_router = APIRouter()

# Example router inclusion:
<<<<<<< HEAD
from app.api.v1.endpoints import users , auth , applications , documents,sessions
=======
from app.api.v1.endpoints import users , auth, notifications
from app.api.v1.endpoints import sessions
from app.api.v1.endpoints import documents
from app.api.v1.endpoints import applications
from app.api.v1.endpoints import eligibility
from app.api.v1.endpoints import evaluation
from app.api.v1.endpoints import idemnity


@api_router.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}

>>>>>>> d9580816050b4690075088ffb2e27535030423e3

api_router.include_router(users.router, prefix="/user", tags=["users"])

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

api_router.include_router(applications.router , prefix="/applications" , tags=["applications"])

api_router.include_router(documents.router, prefix="", tags=["documents"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(applications.router, prefix="/applications", tags=["applications"])
api_router.include_router(eligibility.router, prefix="/applications", tags=["eligibility"])
api_router.include_router(evaluation.router, prefix="/evaluation", tags=["scoring"])
api_router.include_router(idemnity.app , prefix="/idemnity" , tags=["budjet and zones"])
