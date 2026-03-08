from app.core.database import AsyncSessionLocal, get_db
from app.models.session import Session
from app.schemas.session import SessionResponse
from sqlalchemy import select
from fastapi import Depends
import datetime
async def get_current_session(db: AsyncSessionLocal = Depends(get_db)):
    result = await db.execute(
        select(Session).where(Session.is_active == True, Session.end_date >= datetime.date.today())
    )
    session = result.scalar_one_or_none()
    return session