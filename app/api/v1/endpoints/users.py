import uuid
from fastapi import APIRouter , Depends , HTTPException
from app.core.database import AsyncSessionLocal
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import CreateUser , UserResponse
from app.services.user.user_service import create_user , get_users , get_user

router = APIRouter()  

@router.post("/" , response_model=UserResponse)
async def create_user_endpoint(user : CreateUser , db : AsyncSessionLocal= Depends(get_db)) :
    return await create_user(user, db)

@router.get("/" , response_model=list[UserResponse])
async def get_users_endpoint(db : AsyncSessionLocal= Depends(get_db)) :
    return await get_users(db)

@router.get("/{user_id}" , response_model=UserResponse)
async def get_user_endpoint(user_id : uuid.UUID , db : AsyncSessionLocal= Depends(get_db)) :
    return await get_user(db , user_id)




