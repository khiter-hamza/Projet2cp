from sqlalchemy import select
from app.schemas.user import CreateUser , UserResponse ,UserLogin
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import hash_password , decode_token , create_token , verify_password
from uuid import UUID
from typing import Annotated
from fastapi import HTTPException , Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def register_user(user : CreateUser , db : AsyncSessionLocal) -> UserResponse :
    result = await db.execute(select(User).where(User.email == user.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=400, detail="email already exists")
    hashed_pwd = hash_password(user.password)
    new_user = User(
        email=user.email, 
        hashed_password=hashed_pwd, 
        username=user.username, 
        lastname=user.lastname
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return UserResponse.model_validate(new_user)
   


async def login_user(user : UserLogin , db : AsyncSessionLocal ) :
    result = await db.execute(select(User).where(User.email == user.email))
    userdb = result.scalar_one_or_none()
    if not userdb:
        raise HTTPException(status_code=400, detail="email doesn't exist")
    
    if not verify_password(user.password, userdb.hashed_password):
        raise HTTPException(status_code=400, detail="incorrect password")
    
    token = create_token(str(userdb.id))
    return {
        "access_token": token,
        "token_type": "bearer"
    }


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UUID:
    try:
        token = credentials.credentials
        payload = decode_token(token)
        return UUID(payload.get("user_id"))
    except (ValueError, AttributeError):
        raise HTTPException(status_code=401, detail="Invalid token")
