from sqlalchemy import select
from app.schemas.user import CreateUser , UserResponse 
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import hash_password
import uuid
from uuid import UUID



async def create_user(user : CreateUser , db : AsyncSessionLocal) -> UserResponse :
    hashed_pwd = hash_password(user.password)
    new_user = User(email=user.email , hashed_password= hashed_pwd , username=user.username , lastname=user.lastname , role = user.role ,grade = user.grade , ancientee = user.ancientee ) 
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return UserResponse.model_validate(new_user)



async def get_users(db : AsyncSessionLocal) -> list[UserResponse] :
    result = await db.execute(select(User))
    users = result.scalars().all()
    return [UserResponse.model_validate(u) for u in users]


async def get_user(db : AsyncSessionLocal , user_id : str):
    from uuid import UUID as _UUID
    uid = _UUID(user_id) if isinstance(user_id, str) else user_id
    result = await db.execute(select(User).where(User.id == uid))
    user = result.scalar_one_or_none()
    return user


async def update_user(new_user : CreateUser , user_id : UUID, db : AsyncSessionLocal) -> UserResponse:
    """
    Update user fields - only updates non-null fields from new_user.
    Preserves existing values for fields that are None in new_user.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise ValueError("User not found")
    
    # Get only the fields that were explicitly set (exclude unset fields)
    update_data = new_user.model_dump(exclude_unset=True)
    
    # Update only non-null fields
    for field, value in update_data.items():
        if value is not None:
            # Hash password if updating password
            if field == "password" and value:
                value = hash_password(value)
                setattr(user, "hashed_password", value)
            else:
                setattr(user, field, value)
    
    try:
        await db.commit()
        await db.refresh(user)
    except Exception as e:
        await db.rollback()
        raise ValueError(f"Failed to update user: {str(e)}")
    
    return UserResponse.model_validate(user)
     
    
