from sqlalchemy import select
from app.schemas.user import CreateUser , UserResponse 
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import hash_password
import uuid



async def create_user(user : CreateUser , db : AsyncSessionLocal) -> UserResponse :
    hashed_pwd = hash_password(user.password)
    new_user = User(email=user.email , hashed_password= hashed_pwd , username=user.username , lastname=user.lastname)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return UserResponse.model_validate(new_user)



async def get_users(db : AsyncSessionLocal) -> list[UserResponse] :
    result = await db.execute(select(User))
    users = result.scalars().all()
    return [UserResponse.model_validate(u) for u in users]


async def get_user(db : AsyncSessionLocal , user_id : int) -> UserResponse :
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user:
        return UserResponse.model_validate(user)
    return None
    
