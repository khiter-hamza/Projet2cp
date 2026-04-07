from sqlalchemy import select
from app.schemas.user import CreateUser , UserResponse ,UserLogin
from app.core.database import AsyncSessionLocal
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.laboratory import Laboratory
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
    # Resolve laboratory by name or create it
    result = await db.execute(select(Laboratory).where(Laboratory.name == user.laboratory_name))
    lab = result.scalar_one_or_none()
    if not lab:
        lab = Laboratory(name=user.laboratory_name)
        db.add(lab)
        await db.flush()

    new_user = User(
        email=user.email,
        hashed_password=hashed_pwd,
        username=user.username,
        lastname=user.lastname,
        role=user.role if hasattr(user, 'role') else None,
        grade=user.grade if hasattr(user, 'grade') else None,
        # DB column is 'anciente' — populate it from schema's 'ancientee'
        anciente=user.ancientee if hasattr(user, 'ancientee') else 0,
        laboratory_id=lab.id,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return UserResponse.model_validate(new_user)
   


async def login_user(user : UserLogin , db : AsyncSession ) :
    result = await db.execute(select(User).where(User.email == user.email))
    userdb = result.scalar_one_or_none()
    if not userdb:
        raise HTTPException(status_code=400, detail="email doesn't exist")
    
    if not verify_password(user.password, userdb.hashed_password):
        raise HTTPException(status_code=400, detail="incorrect password")
    
    token = create_token({
        "sub": str(userdb.id),
        "role": userdb.role
    })
    return {
        "access_token": token,
        "token_type": "bearer"
    }

    