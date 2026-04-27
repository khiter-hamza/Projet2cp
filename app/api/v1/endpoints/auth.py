import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.core.database import AsyncSessionLocal, get_db
from app.core.oauth import oauth
from app.core.security import ACCESS_TOKEN_EXPIRE_MINUTES, decode_token
from app.models.user import User
from app.schemas.user import (
    CreateUser,
    UserResponse,
    UserLogin,
    CurrentUserResponse,
    forget_User,
    reset_Password,
)
from app.services.auth.auth_service import google_callbackk, login_user, register_user
from app.services.auth.password_service import forgot_password, reset_password, verify_token_url

router = APIRouter()


@router.post('/register', response_model=UserResponse)
async def register(user: CreateUser, db: AsyncSession = Depends(get_db)):
    return await register_user(user, db)


@router.post('/login')
async def login(
    user: UserLogin,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    auth_data = await login_user(user, db)
    response.set_cookie(
        key='access_token',
        value=auth_data['access_token'],
        httponly=True,
        samesite='lax',
        secure=False,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path='/',
    )
    return { "message" : "login suuceful"}


@router.post('/logout')
async def logout(response: Response):
    response.delete_cookie(key='access_token')
    return {'message': 'Logout successful'}


from app.core.dependencies import get_current_user

@router.get('/me', response_model=CurrentUserResponse)
async def get_me(
    user: User = Depends(get_current_user),
):
    """
    Get the current authenticated user.
    """
    return user


@router.get('/google')
async def login_google(request: Request):
    redirect_uri = request.url_for('google_callback')
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get('/google/callback', name='google_callback')
async def auth_google_callback(request: Request, db: AsyncSessionLocal = Depends(get_db)):
    return await google_callbackk(request, db)


@router.post('/forget-password')
async def forgot_password_endpoint(
    user: forget_User,
    background_tasks: BackgroundTasks,
    db: AsyncSessionLocal = Depends(get_db),
):
    return await forgot_password(user, db, background_tasks)


@router.post('/reset-password/{token}')
async def reset_password_endpoint(
    token: str,
    new_password: reset_Password,
    db: AsyncSessionLocal = Depends(get_db),
):
    return await reset_password(token, new_password.new_password, db)


@router.get('/reset-password/{token}')
async def verify_reset_token_endpoint(token: str, db: AsyncSessionLocal = Depends(get_db)):
    return await verify_token_url(token, db)
