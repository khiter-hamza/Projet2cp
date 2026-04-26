from fastapi import Depends, HTTPException, status
from app.core import security
from app.core.database import get_db, AsyncSessionLocal
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import decode_token
from app.services.user.user_service import get_user
from uuid import UUID

from starlette.requests import Request

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    token = request.cookies.get("access_token")
    
    # Fallback to Authorization header if cookie is missing
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user ID"
        )
     
    try:
        user_id = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid user ID format")

    db_user = await get_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=401, detail="User not found")
    return db_user

async def get_current_user_id(
    user = Depends(get_current_user)
) -> UUID:
    return user.id
   