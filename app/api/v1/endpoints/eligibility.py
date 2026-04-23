"""
Eligibility Endpoints

Endpoints for checking eligibility and getting detailed eligibility information for applications.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated

from app.core.database import AsyncSession, get_db
from app.core.dependencies import get_current_user_id
from app.services.application.eligibility_service import (
    get_eligibility_details,
)
from app.schemas.eligibility import (
    EligibilityDetailedResponse
)


router = APIRouter()


@router.get("/{application_id}/eligibility-details", response_model=EligibilityDetailedResponse)
async def get_eligibility_details_endpoint(
    application_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user_id: Annotated[UUID, Depends(get_current_user_id)]
):
    """
    Get detailed eligibility information for an application.
    
    Returns comprehensive details about:
    - Grade eligibility check
    - Application history analysis
    - Required documents status
    """
    try:
        result = await get_eligibility_details(application_id, db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get eligibility details: {str(e)}")
