"""
Evaluation & Scoring Endpoints

Endpoints for calculating application scores based on user's history.

Scoring Criteria (per teacher requirements):
1. Number of completed applications (x10 points each)
2. Total number of applications (x5 points each)
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated

from app.core.database import AsyncSession, get_db
from app.core.dependencies import get_current_user
from app.services.evaluation.criteria_service import calculate_score
from app.schemas.evaluation import ScoreResponse, ScoringDetailResponse


router = APIRouter()


@router.get("/users/{user_id}/score", response_model=ScoreResponse)
async def get_user_score_endpoint(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user_id: Annotated[UUID, Depends(get_current_user)]
):
    """
    Get the score for a user based on their application history.
    
    Score calculation:
    - Completed applications: 10 points each
    - Total applications: 5 points each
    
    This score is used to rank applications for CS decision-making.
    """
    try:
        score = await calculate_score(db, user_id)
        return score
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate score: {str(e)}")


@router.get("/applications/{application_id}/score", response_model=ScoreResponse)
async def get_application_score_endpoint(
    application_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user_id: Annotated[UUID, Depends(get_current_user)]
):
    """
    Get the score for the user who submitted the application.
    
    This retrieves the user's score (based on their history) for ranking this application.
    """
    from sqlalchemy import select
    from app.models.application import Application
    
    try:
        # Get application to find user
        result = await db.execute(
            select(Application).where(Application.id == application_id)
        )
        application = result.scalar_one_or_none()
        
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Calculate score for the user
        score = await calculate_score(db, application.user_id)
        return score
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate score: {str(e)}")
