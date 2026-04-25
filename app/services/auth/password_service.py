from app.services.auth.token_service import create_token_url
import logging
import secrets
from datetime import datetime
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User
from app.schemas.user import forget_User , reset_Password
from sqlalchemy.orm import joinedload
from fastapi_mail import FastMail, MessageSchema
from fastapi import BackgroundTasks
from app.core.env import (
    MAIL_USERNAME,
    MAIL_PASSWORD,
    MAIL_FROM,
    MAIL_SERVER,
    MAIL_PORT,
    MAIL_USE_TLS,
)


from app.core.security import hash_password


from fastapi_mail import ConnectionConfig

logger = logging.getLogger(__name__)


def _build_mail_config() -> ConnectionConfig:
    if not MAIL_USERNAME or not MAIL_PASSWORD or not MAIL_FROM:
        raise ValueError("MAIL_USERNAME, MAIL_PASSWORD and MAIL_FROM must be set")

    return ConnectionConfig(
        MAIL_USERNAME=MAIL_USERNAME,
        MAIL_PASSWORD=MAIL_PASSWORD,
        MAIL_FROM=MAIL_FROM,
        MAIL_SERVER=MAIL_SERVER,
        MAIL_PORT=MAIL_PORT,
        MAIL_STARTTLS=not MAIL_USE_TLS,
        MAIL_SSL_TLS=MAIL_USE_TLS,
        USE_CREDENTIALS=True,
    )

def send_reset_email(background_tasks: BackgroundTasks, email: str, token: str):
    reset_link = f"http://localhost:8000/auth/reset-password/{token}"
    

    message = MessageSchema(
        subject="Reset Your Password",
        recipients=[email],
        body=f"""
        Click the link to reset your password:
        {reset_link}
        """,
        subtype="plain"
    )

    conf = _build_mail_config()
    fm = FastMail(conf)
    background_tasks.add_task(fm.send_message, message)

async def forgot_password(user:forget_User, db: AsyncSessionLocal,background_tasks: BackgroundTasks):
    result= await db.execute(select(User).where(User.email==user.email))
    user=result.scalar_one_or_none()
    if  user:
        token=await create_token_url(db,user.id)
        try:
            send_reset_email(background_tasks, user.email, token)
        except Exception as exc:
            logger.exception("Failed to queue reset email: %s", exc)

    return {"detail":"If an account with that email exists, a password reset link has been sent."}   


async def verify_token_url(token:str,db:AsyncSessionLocal):
    result=await db.execute(select(PasswordResetToken).where(PasswordResetToken.token==token))
    db_token=result.scalar_one_or_none()
    if not db_token or db_token.isvalid()==False:
        raise {"valid": False, "detail": "Invalid or expired token"}
    
    return {"valid": True, "detail": "Token is valid"}
    
async def reset_password(token: str, new_password: str, db: AsyncSessionLocal):
    result=await db.execute(select(PasswordResetToken).options(joinedload(PasswordResetToken.user)).where(PasswordResetToken.token==token))
    db_token=result.scalar_one_or_none()
    if not db_token or db_token.isvalid()==False:
        raise { "detail": "Invalid or expired token"}
    db_token.already_used=True
    db_token.user.hashed_password=hash_password(new_password)
    await db.commit()
    return{"detail":"Password reset successfulDone"}
    