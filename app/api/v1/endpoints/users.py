import uuid
from Projet2cp.app.services.auth.password_service import forgot_password, reset_password, verify_token_url
from fastapi import APIRouter , Depends , HTTPException, BackgroundTasks
from app.core.database import AsyncSessionLocal
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import CreateUser , UserResponse, forget_User, reset_Password
from app.services.user.user_service import create_user , get_users , get_user , update_user,google_callbackk


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

@router.put("/{user_id}", response_model=UserResponse)
async def update_user_endpoint(user_id : uuid.UUID, user_data : CreateUser, db : AsyncSessionLocal= Depends(get_db)):
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
    
@router.post("/forget-password")
async def forgot_password_endpoint(user: forget_User, db: AsyncSessionLocal = Depends(get_db), background_tasks: BackgroundTasks = Depends()):
    return await forgot_password(user, db, background_tasks)
@router.post("/reset-password/{token}")
async def reset_password_endpoint(token:str,new_password: str, db: AsyncSessionLocal = Depends(get_db)):
    return await reset_password(token, new_password, db)
@router.get("/reset-password/{token}")
async def verify_reset_token_endpoint(token: str, db: AsyncSessionLocal = Depends(get_db)):
    return await verify_token_url(token, db)

@app.get("/auth/google") #  for opening the  onglet of the Outh with google
async def login_google(request: Request):
    redirect_uri = request.url_for("google_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get("/auth/google/callback") #called by google services 
async def auth_google_callback(request: Request,db:AsyncSessionLocal = Depends(get_db),name="google_callback"):
    return await google_callbackk(request,db)
    