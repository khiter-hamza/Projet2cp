from contextlib import asynccontextmanager
import asyncio
import logging
import traceback
from datetime import date
from app.models.enums import Status
from sqlalchemy.orm import joinedload
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import select, update

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import init_db, AsyncSessionLocal
from app.models.session import Session

# Configure logging to show errors in terminal
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    """Catches ALL unhandled exceptions and prints the full traceback to the terminal."""
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            logger.error(f"\n{'='*60}")
            logger.error(f"UNHANDLED EXCEPTION on {request.method} {request.url}")
            logger.error(traceback.format_exc())
            logger.error(f"{'='*60}\n")
            return JSONResponse(
                status_code=500,
                content={"detail": str(exc)},
            )


async def close_expired_sessions():
    
    while True:
        try:
            async with AsyncSessionLocal() as db:
                
               res=await db.execute(select(Session).options(
               joinedload(Session.applications)).where(Session.is_active == True, Session.end_date < date.today()))
               result = res.scalar_one_or_none()
               if result:
                   applications=result.applications
                   #for those who are in draft status we will change their status to submitted because the session is closed and they can't edit their application anymore and they can only see it and they can see the status of their application is submitted and they can see the date of submission of their application which is the date of closing of the session and for those who are in submitted status we will keep their status as submitted because they have already submitted their application and they can see the date of submission of their application which is the date of closing of the session and for those who are in accepted or rejected status we will keep their status as it is because they have already received a decision on their application and they can see the date of decision on their application which is the date of closing of the session
                   for app in applications:
                       if app.status==Status.DRAFT:
                        app.status=Status.SUBMITTED

                   result.is_open = False
                   await db.commit()   

               logger.info("Checked for expired sessions")
        except Exception:
            logger.error(f"Error closing expired sessions: {traceback.format_exc()}")
        await asyncio.sleep(10800)  # check every 3 hours


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize things like DB connection pools
    print(f"Starting up {settings.PROJECT_NAME}...")
    await init_db()
    # Start background task to auto-close expired sessions
    task = asyncio.create_task(close_expired_sessions())
    yield
    # Shutdown: Cancel background task and clean up
    task.cancel()
    print(f"Shutting down {settings.PROJECT_NAME}...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
)

# Error logging middleware — must be added FIRST (outermost)
app.add_middleware(ErrorLoggingMiddleware)

# Set up CORS
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include Routers
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "message": "Welcome to Projet 2CP API",
        "docs": "/docs",
        "health_check": f"{settings.API_V1_STR}/health"
    }



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
