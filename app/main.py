from contextlib import asynccontextmanager
import logging
import traceback
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import init_db

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize things like DB connection pools
    print(f"Starting up {settings.PROJECT_NAME}...")
    await init_db()
    yield
    # Shutdown: Clean up resources
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
