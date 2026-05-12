"""
Scoring Service - Evaluation Criteria

Hybrid Scoring Logic:
1. Counts COMPLETED/CLOSED applications from the system database.
2. Combines them with manual "External History" fields (optional).
3. Calculates total score based on Experience and Recency.
"""

from datetime import datetime
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.application import Application
from app.models.enums import Status

async def calculate_score(db: AsyncSession, application: Application) -> float:
    """
    Calculate application score based on a mix of manual history and system history.
    """
    user_id = application.user_id
    
    # 1. Fetch System History (COMPLETED or CLOSED applications in DB)
    result = await db.execute(
        select(func.count(Application.id))
        .where(
            Application.user_id == user_id,
            Application.status.in_([Status.COMPLETED, Status.CLOSED]),
            Application.id != application.id  # Exclude current application
        )
    )
    system_completed_count = result.scalar() or 0
    
    # 2. Get most recent date from System History
    result = await db.execute(
        select(func.max(Application.end_date))
        .where(
            Application.user_id == user_id,
            Application.status.in_([Status.COMPLETED, Status.CLOSED]),
            Application.id != application.id
        )
    )
    system_last_date = result.scalar()
    
    # 3. Combine with Manual History
    manual_completed_count = application.prev_completed_count or 0
    manual_last_date = application.last_stay_date
    
    total_completed = system_completed_count + manual_completed_count
    
    # Determine the most recent date between Manual and System
    final_last_date = system_last_date
    if manual_last_date:
        if not final_last_date or manual_last_date > final_last_date:
            final_last_date = manual_last_date
            
    # 4. Calculate Scores
    experience_score = total_completed * 10
    
    recency_score = 0
    if final_last_date:
        # Support both date and datetime types
        last_date_obj = final_last_date
        if hasattr(last_date_obj, 'date'):
            last_date_obj = last_date_obj.date()
            
        days_since = (datetime.utcnow().date() - last_date_obj).days
        years_since = days_since / 365.25
        
        if years_since < 1:
            recency_score = 10
        elif years_since < 2:
            recency_score = 5
        else:
            recency_score = 2
            
    return float(experience_score + recency_score)