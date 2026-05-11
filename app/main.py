from contextlib import asynccontextmanager
import os
import asyncio
import logging
import traceback
from datetime import date

# Allow insecure transport for local development (Google OAuth over HTTP)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

from sqlalchemy.orm import joinedload
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy import select

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import init_db, AsyncSessionLocal
from app.models.session import Session
from app.models.enums import Status

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def close_expired_sessions():
    while True:
        try:
            async with AsyncSessionLocal() as db:
                res = await db.execute(
                    select(Session).options(joinedload(Session.applications))
                    .where(Session.is_active == True, Session.end_date < date.today())
                )
                result = res.unique().scalar_one_or_none()
                if result:
                    applications = result.applications
                    for app in applications:
                        if app.status == Status.DRAFT:
                            app.status = Status.SUBMITTED
                    result.is_open = False
                    await db.commit()   
                logger.info("Checked for expired sessions")
        except Exception:
            logger.error(f"Error closing expired sessions: {traceback.format_exc()}")
        await asyncio.sleep(10800)  # check every 3 hours

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"Starting up {settings.PROJECT_NAME}...")
    await init_db()
    task = asyncio.create_task(close_expired_sessions())
    yield
    task.cancel()
    print(f"Shutting down {settings.PROJECT_NAME}...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
)

# Set up CORS
allowed_origins = [str(origin).rstrip("/") for origin in settings.CORS_ORIGINS] if settings.CORS_ORIGINS else ["*"]
allow_credentials = False if "*" in allowed_origins else True

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

# SessionMiddleware MUST be added LAST so it is outermost.
# In Starlette, the last middleware added wraps all others.
# This ensures the session cookie is available during every request/response.
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    same_site="lax",
    https_only=False,
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catches ALL unhandled exceptions and prints the full traceback to the terminal."""
    logger.error(f"\n{'='*60}")
    logger.error(f"UNHANDLED EXCEPTION on {request.method} {request.url}")
    logger.error(traceback.format_exc())
    logger.error(f"{'='*60}\n")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
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
