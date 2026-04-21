"""
CS Workflow Endpoints

Handles:
- CS deliberation preparation (consolidate eligible applications)
- CS decision making (approve/reject applications)
- CS dashboard with recommendations and statistics
"""

from uuid import UUID
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.database import AsyncSession, get_db
from app.core.dependencies import get_current_user_id
from app.schemas.cs import (
    CSDecisionRequest,
    CSPreparationResponse,
    CSDashboardResponse,
    CSDecisionResponse,
    CSStatisticsResponse
)
from app.services.admin.cs_service import (
    approve_application,
    reject_application,
)

router = APIRouter()


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/deliberate/{application_id}", response_model=CSDecisionResponse)
async def cs_deliberation_endpoint(
    application_id: UUID,
    request: CSDecisionRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user_id: Annotated[UUID, Depends(get_current_user_id)]
):
    # Validate decision
    if request.decision not in ["approved", "rejected"]:
        raise HTTPException(
            status_code=400,
            detail='Decision must be either "approved" or "rejected"'
        )
    
    # Route to appropriate handler
    if request.decision == "approved":
        return await approve_application(application_id, current_user_id, request.notes, db)
    else:  # rejected
        if not request.notes or not request.notes.strip():
            raise HTTPException(
                status_code=400,
                detail="Rejection reason is required when rejecting"
            )
        return await reject_application(application_id, current_user_id, request.notes, db)
