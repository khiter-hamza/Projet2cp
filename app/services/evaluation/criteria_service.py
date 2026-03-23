"""
Scoring Service - Evaluation Criteria

Based on teacher requirements, scoring is calculated using:
1. Number of completed applications (higher = better priority)
2. Total number of all applications (higher = better priority)

This is used to rank applications for CS decision-making.
"""

from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.application import Application
from app.models.enums import Status
from app.schemas.evaluation import ScoreResponse


async def calculate_score(db: AsyncSession, user_id: UUID) -> ScoreResponse:
    """
    Calculate application score based on user's history.
    
    Criteria (as per teacher requirements):
    1. Number of completed applications
    2. Total number of applications
    
    Returns: ScoreResponse with score and breakdown
    """
    
    # Count total applications for this user (all statuses except DRAFT)
    total_result = await db.execute(
        select(func.count(Application.id))
        .where(
            Application.user_id == user_id,
            Application.status != Status.DRAFT
        )
    )
    total_applications = total_result.scalar() or 0
    
    # Count completed applications (COMPLETED or CLOSED status)
    completed_result = await db.execute(
        select(func.count(Application.id))
        .where(
            Application.user_id == user_id,
            Application.status.in_([Status.COMPLETED, Status.CLOSED])
        )
    )
    completed_applications = completed_result.scalar() or 0
    
    # Calculate score
    # Completed apps weighted more heavily than total apps
    score = (completed_applications * 10) + (total_applications * 5)
    
    return ScoreResponse(
        score=score,
        completed=completed_applications,
        applications=total_applications
    )