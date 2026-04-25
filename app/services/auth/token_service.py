import uuid
from datetime import datetime
import secrets

from app.core.database import AsyncSessionLocal
from app.models.password_reset_token import PasswordResetToken


async def create_token_url(db: AsyncSessionLocal, user_id: uuid.UUID) -> str:
    
    token = secrets.token_urlsafe(16)
    
    duration = 15 * 60  # 15 minutes in seconds
   
    db_token = PasswordResetToken(
        token=token,
        duration=duration,
        already_used=False,
        created_at=datetime.utcnow(),
        user_id=user_id
     )
    db.add(db_token)
    await db.commit()
    await db.refresh(db_token)
     
    return token