from sqlalchemy import select
from app.schemas.user import CreateUser , UserResponse ,UserLogin
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import hash_password , decode_token , create_token , verify_password
import uuid
import traceback
from fastapi import HTTPException


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
  try:
    result = await db.execute(select(User).where(User.email == user.email))
    userdb = result.scalar_one_or_none()
    if not userdb:
        raise HTTPException(status_code=400, detail="email doesn't exist")
    
    if not verify_password(user.password, userdb.hashed_password):
        raise HTTPException(status_code=400, detail="incorrect password")
    
    token = create_token(userdb.id)
    return {
        "access_token": token,
        "token_type": "bearer"
    }
  except Exception as e:
    logger.error(f"LOGIN ERROR: {traceback.format_exc()}")
    raise    
