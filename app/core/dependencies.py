from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from app.core.database import get_db, AsyncSessionLocal
from app.core.security import decode_token
from app.services.user.user_service import get_user
import jose.jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSessionLocal = Depends(get_db)):
    payload = decode_token(token) 
    user_id = payload.get("user_id") 
    user = await get_user(db , user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found") 
    return user