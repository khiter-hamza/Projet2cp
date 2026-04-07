from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from app.core import security
from app.core.database import get_db, AsyncSessionLocal
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import decode_token
from app.services.user.user_service import get_user
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security= HTTPBearer()

async def get_token_payload(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    return payload

async def get_current_user(
    payload: dict = Depends(get_token_payload),
    db: AsyncSession = Depends(get_db)
):
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
   