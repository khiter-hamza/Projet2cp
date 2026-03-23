from fastapi import APIRouter , HTTPException , Depends 
import uuid
from app.core.database import AsyncSessionLocal , get_db
from app.models.user import User
from app.schemas.user import CreateUser , UserResponse ,UserLogin 
from app.services.auth.auth_service import login_user , register_user 



router = APIRouter()



@router.post("/register" , response_model  = UserResponse)
async def register(user : CreateUser, db : AsyncSessionLocal = Depends(get_db)) :
    return await register_user(user,db)


@router.post("/login")
async def login(user : UserLogin , db : AsyncSessionLocal = Depends(get_db)) :
    return await login_user(user, db)









