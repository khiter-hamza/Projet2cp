import uuid

from fastapi import APIRouter , Depends , HTTPException, BackgroundTasks
from app.core.database import AsyncSessionLocal
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import CreateUser , UpdateUser, UserResponse
from app.services.user.user_service import create_user , get_users , get_user , update_user



router = APIRouter()  

@router.post("/" , response_model=UserResponse)
async def create_user_endpoint(user : CreateUser , db : AsyncSessionLocal= Depends(get_db)) :
    try:
        return await create_user(user, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/" , response_model=list[UserResponse])
async def get_users_endpoint(db : AsyncSessionLocal= Depends(get_db)) :
    return await get_users(db)

@router.get("/{user_id}" , response_model=UserResponse)
async def get_user_endpoint(user_id : uuid.UUID , db : AsyncSessionLocal= Depends(get_db)) :
    return await get_user(db , user_id)

@router.put("/{user_id}", response_model=UserResponse)
async def update_user_endpoint(user_id : uuid.UUID, user_data : UpdateUser, db : AsyncSessionLocal= Depends(get_db)):
    """
    Update a user - only updates non-null fields.
    Preserves existing values for fields not provided.
    """
    try:
        return await update_user(user_data, user_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


