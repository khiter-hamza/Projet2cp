import uuid

from fastapi import APIRouter , Depends , HTTPException, BackgroundTasks
from app.core.database import AsyncSessionLocal
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import CreateUser , UpdateUser, UserResponse
from app.services.user.user_service import create_user , get_users , get_user , update_user, delete_user
from app.core.dependencies import get_current_user



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
async def update_user_endpoint(
    user_id : uuid.UUID, 
    user_data : UpdateUser, 
    db : AsyncSessionLocal= Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a user - only updates non-null fields.
    Preserves existing values for fields not provided.
    """
    if current_user.id == user_id:
        if user_data.is_active is False:
             raise HTTPException(status_code=400, detail="You cannot deactivate your own account")
        if user_data.role and user_data.role != 'super_admin':
             raise HTTPException(status_code=400, detail="You cannot change your own role from Super Admin")

    try:
        return await update_user(user_data, user_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.delete("/{user_id}")
async def delete_user_endpoint(
    user_id : uuid.UUID, 
    db : AsyncSessionLocal= Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")
        
    try:
        await delete_user(user_id, db)
        return {"message": "User deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


