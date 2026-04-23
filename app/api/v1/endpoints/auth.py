from app.services.auth.password_service import reset_password, verify_token_url
from fastapi import APIRouter , HTTPException , Depends 
import uuid
from app.core.database import AsyncSessionLocal , get_db
from app.models.user import User
from app.schemas.user import CreateUser , UserResponse ,UserLogin 
from app.services.auth.auth_service import google_callbackk, login_user , register_user 
from starlette.requests import Request
from app.core.oauth import oauth
from app.services.auth.password_service import forgot_password, reset_password, verify_token_url
from app.schemas.user import forget_User, reset_Password
from fastapi import BackgroundTasks

router = APIRouter()



@router.post("/register" , response_model  = UserResponse)
async def register(user : CreateUser, db : AsyncSessionLocal = Depends(get_db)) :
    return await register_user(user,db)


@router.post("/login")
async def login(user : UserLogin , db : AsyncSessionLocal = Depends(get_db)) :
    return await login_user(user, db)

@router.get("/google") #  for opening the  onglet of the Outh with google
async def login_google(request: Request):
    redirect_uri = request.url_for("google_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/google/callback", name="google_callback") #called by google services 
async def auth_google_callback(request: Request,db:AsyncSessionLocal = Depends(get_db)):
    return await google_callbackk(request,db)
    
@router.post("/forget-password")
async def forgot_password_endpoint(user: forget_User, background_tasks: BackgroundTasks, db: AsyncSessionLocal = Depends(get_db) ):
    return await forgot_password(user, db, background_tasks)
@router.post("/reset-password/{token}")
async def reset_password_endpoint(token:str,new_password: str, db: AsyncSessionLocal = Depends(get_db)):
    return await reset_password(token, new_password, db)
@router.get("/reset-password/{token}")
async def verify_reset_token_endpoint(token: str, db: AsyncSessionLocal = Depends(get_db)):
    return await verify_token_url(token, db)    







