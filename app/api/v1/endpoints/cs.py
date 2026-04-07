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
    prepare_cs_deliberation,
    get_cs_dashboard_applications,
    approve_application,
    reject_application,
    get_cs_decision_history
)

router = APIRouter()


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/prepare-deliberation/{session_id}", response_model=CSPreparationResponse)
async def prepare_cs_deliberation_endpoint(
    session_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user_id: Annotated[UUID, Depends(get_current_user_id)]
):
    """
    Prepare CS deliberation for a session.
    
    **What it does**:
    - Gets all SUBMITTED applications that are eligible
    - Transitions them from SUBMITTED → CS_PREPARATION status
    - Readies them for CS deliberation
    
    **Who can use**: CS Admin / Super Admin
    
    **Response**: Summary of applications prepared
    
    Args:
        session_id: ID of the session to prepare for deliberation
    
    Returns:
        - message: Success confirmation
        - session_id: ID of the session
        - session_name: Name of the session
        - total_applications: Number of applications prepared
        - ready_for_deliberation: Whether ready for CS review
    
    Example:
        ```
        POST /api/v1/cs/prepare-deliberation/550e8400-e29b-41d4-a716-446655440000
        ```
    """
    return await prepare_cs_deliberation(session_id, current_user_id, db)


@router.get("/dashboard", response_model=CSDashboardResponse)
async def get_cs_dashboard_endpoint(
    session_id: Annotated[Optional[UUID], Query()] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)] = None
):
    """
    Get CS deliberation dashboard.
    
    **What it shows**:
    - All applications ready for CS deliberation (CS_PREPARATION status)
    - Sorted by score (highest first) and submission date
    - User information, stage details, and eligibility status
    - Current CS decision status (if already decided)
    
    **Who can use**: CS Admin / Super Admin
    
    **Query Parameters**:
    - session_id (optional): Filter by specific session
    
    **Response**: List of applications with:
    - Applicant info (name, grade)
    - Stage details (type, destination, duration)
    - Score and eligibility status
    - Current CS decision status and rejection reason (if any)
    
    Example:
        ```
        GET /api/v1/cs/dashboard
        GET /api/v1/cs/dashboard?session_id=550e8400-e29b-41d4-a716-446655440000
        ```
    """
    applications = await get_cs_dashboard_applications(session_id, current_user_id, db)
    return {
        "count": len(applications),
        "applications": applications
    }


@router.post("/deliberate/{application_id}", response_model=CSDecisionResponse)
async def cs_deliberation_endpoint(
    application_id: UUID,
    request: CSDecisionRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user_id: Annotated[UUID, Depends(get_current_user_id)]
):
    """
    Make CS decision on an application: APPROVE or REJECT.
    
    **What it does**:
    - CS approves (approuve) or rejects (rejete) the application
    - Updates application status accordingly
    - For approvals: transitions to APPROVED status (ready for fee calculation)
    - For rejections: transitions to REJECTED status and stores rejection reason
    - Records the decision timestamp
    
    **Who can use**: CS Admin / Super Admin
    
    **Request Body**:
    ```json
    {
        "decision": "approuve | rejete",
        "notes": "Optional notes or rejection reason"
    }
    ```
    
    **Status Transitions**:
    - CS_PREPARATION → APPROVED (if decision = "approuve")
    - CS_PREPARATION → REJECTED (if decision = "rejete")
    
    **Response**:
    - message: Confirmation message
    - application_id: ID of the application
    - cs_decision: The decision made (approuve/rejete)
    - status: New application status
    - approved_at / rejected_at: Timestamp of decision
    - rejection_reason: Only for rejections
    
    Example:
        ```
        POST /api/v1/cs/deliberate/550e8400-e29b-41d4-a716-446655440000
        {
            "decision": "approuve",
            "notes": "Excellent candidate, highly recommended for funding"
        }
        
        POST /api/v1/cs/deliberate/550e8400-e29b-41d4-a716-446655440000
        {
            "decision": "rejete",
            "notes": "Insufficient experience in the proposed research area"
        }
        ```
    """
    # Validate decision
    if request.decision not in ["approuve", "rejete"]:
        raise HTTPException(
            status_code=400,
            detail='Decision must be either "approuve" or "rejete"'
        )
    
    # Route to appropriate handler
    if request.decision == "approuve":
        return await approve_application(application_id, current_user_id, request.notes, db)
    else:  # rejete
        if not request.notes or not request.notes.strip():
            raise HTTPException(
                status_code=400,
                detail="Rejection reason is required when rejecting"
            )
        return await reject_application(application_id, current_user_id, request.notes, db)


@router.get("/statistics/{session_id}", response_model=CSStatisticsResponse)
async def get_cs_statistics_endpoint(
    session_id: Optional[UUID] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)] = None
):
    """
    Get CS decision statistics and history.
    
    **What it shows**:
    - Total decisions made in a session
    - Number of approvals vs rejections
    - Approval rate percentage
    
    **Who can use**: CS Admin / Super Admin
    
    **Query Parameters**:
    - session_id (optional): Filter by specific session
    
    **Response**:
    - total_decisions: Total CS decisions made
    - approved: Number of approved applications
    - rejected: Number of rejected applications
    - approval_rate: Percentage of applications approved
    
    Example:
        ```
        GET /api/v1/cs/statistics
        GET /api/v1/cs/statistics?session_id=550e8400-e29b-41d4-a716-446655440000
        ```
    """
    return await get_cs_decision_history(session_id, current_user_id, db)
