from Projet2cp.app.services.auth.token_service import create_token_url
import secrets
from datetime import datetime
from sqlalchemy import select
from Projet2cp.app.core.database import AsyncSessionLocal
from Projet2cp.app.models.password_reset_token import PasswordResetToken
from Projet2cp.app.models.user import User
from app.schemas.user import forget_User , reset_Password
from sqlalchemy.orm import joinedload
from fastapi_mail import FastMail, MessageSchema
from fastapi import BackgroundTasks
from app.core.config import conf

from app.services.auth.hashing import hash_password


from fastapi_mail import ConnectionConfig

conf = ConnectionConfig(
    MAIL_USERNAME="mesterab20@gmail.com",
    MAIL_PASSWORD="ywme wfdf cuai losi",
    MAIL_FROM="mesterab20@gmail.com",
    
    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT=587,
    
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    
    USE_CREDENTIALS=True
)

def send_reset_email(background_tasks: BackgroundTasks, email: str, token: str):
    reset_link = f"http://localhost:3000/reset-password/{token}"
    

    message = MessageSchema(
        subject="Reset Your Password",
        recipients=[email],
        body=f"""
        Click the link to reset your password:
        {reset_link}
        """,
        subtype="plain"
    )

    fm = FastMail(conf)
    background_tasks.add_task(fm.send_message, message)

async def forgot_password(user:forget_User, db: AsyncSessionLocal,background_tasks: BackgroundTasks):
    result= await db.execute(select(User).where(User.email==user.email))
    user=result.scalar_one_or_none()
    if  user:
        token=create_token_url(db,user.id)
        send_reset_email(background_tasks, user.email, token)

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
    