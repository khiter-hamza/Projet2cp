
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, and_, desc ,asc
from sqlalchemy.orm import joinedload
from fastapi import HTTPException

from app.core.database import AsyncSession
from app.models.application import Application
from app.models.session import Session
from app.models.user import User
from app.models.indemnity_calculation import Idemnity
from app.models.enums import Status, CSDecision, UserRole
from app.services.financial.indemnity_service import calculate_budget
from app.services.auth_service_utils import verify_cs_admin_role
from app.services.notification.notification_service import create_notification, notify_admins
from app.models.enums import NotificationType
from app.schemas.application import ApplicationResponse




async def approve_application(
    application_id: UUID,
    user_id: UUID,
    notes: str | None,
    db: AsyncSession
) -> dict:
    
    # Verify CS admin access
    user = await verify_cs_admin_role(user_id, db)
    
    application = await db.get(Application, application_id)
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    if application.status != Status.SUBMITTED:
        raise HTTPException(
            status_code=400,
            detail=f"Can only approve applications in SUBMITTED status. Current status: {application.status}"
        )
    
    # Update application
    application.cs_decision = CSDecision.approved
    application.status = Status.APPROVED
    application.approved_at = datetime.now()
    if notes:
        application.rejection_reason = notes  # Store notes here even for approval
    
    try:
        await db.commit()
        await db.refresh(application)
        
        # Calculate and create indemnity if not exists
        existing_indemnity = await db.execute(
            select(Idemnity).where(Idemnity.app_id == application_id)
        )
        if not existing_indemnity.scalar_one_or_none():
            # Create indemnity record (fee calculation happens in the endpoint or service)
            # This is just a placeholder for fee calculation logic
            pass
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    message = f"Application {application.id} has been approved by the Scientific Council. Notes: {notes or 'No additional notes.'}"
    try:
        await create_notification(
            db,
            application.user_id,
            "Your application has been approved",
            message,
            NotificationType.cs_decision,
            demande_id=application.id,
        )
        await notify_admins(
            db,
            "Application approved by Scientific Council",
            message,
            NotificationType.cs_decision,
            demande_id=application.id,
        )
    except Exception:
        pass
    
    return {
        "message": "Application approved successfully",
        "application_id": str(application_id),
        "cs_decision": application.cs_decision,
        "status": application.status,
        "approved_at": application.approved_at
    }


async def reject_application(
    application_id: UUID,
    user_id: UUID,
    rejection_reason: str,
    db: AsyncSession
) -> dict:
    """
    CS rejects application.
    
    Requires: CS admin access (admin_dpgr or assistant_dpgr)
    
    Actions:
    1. Verify user is CS admin
    2. Set cs_decision = rejected
    3. Change status from CS_PREPARATION to REJECTED
    4. Store rejection reason
    5. Record rejection timestamp
    
    Args:
        application_id: Application to reject
        user_id: User making the decision (must be CS admin)
        rejection_reason: Required reason for rejection
        db: Database session
        
    Returns:
        Decision confirmation with new status and reason
    """
    if not rejection_reason or not rejection_reason.strip():
        raise HTTPException(status_code=400, detail="Rejection reason is required")
    
    # Verify CS admin access
    user = await verify_cs_admin_role(user_id, db)
    
    application = await db.get(Application, application_id)
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    if application.status != Status.SUBMITTED:
        raise HTTPException(
            status_code=400,
            detail=f"Can only reject applications in CS_PREPARATION status. Current status: {application.status}"
        )
    
    # Update application
    application.cs_decision = CSDecision.rejected
    application.status = Status.REJECTED
    application.rejection_reason = rejection_reason
    application.rejected_at = datetime.now()
    application.closed_at = datetime.now()
    
    try:
        await db.commit()
        await db.refresh(application)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    message = f"Application {application.id} has been rejected by the Scientific Council. Reason: {rejection_reason}"
    try:
        await create_notification(
            db,
            application.user_id,
            "Your application has been rejected",
            message,
            NotificationType.cs_decision,
            demande_id=application.id,
        )
        await notify_admins(
            db,
            "Application rejected by Scientific Council",
            message,
            NotificationType.cs_decision,
            demande_id=application.id,
        )
    except Exception:
        pass
    
    return {
        "message": "Application rejected successfully",
        "application_id": str(application_id),
        "cs_decision": application.cs_decision,
        "status": application.status,
        "rejection_reason": rejection_reason,
        "rejected_at": application.rejected_at
    }


async def get_cs_decision_history(
    session_id: UUID | None,
    user_id: UUID,
    db: AsyncSession
) -> dict:
    """
    Get CS decision statistics and history.
    
    Requires: CS admin access (admin_dpgr or assistant_dpgr)
    
    Args:
        session_id: Optional filter by session
        user_id: User requesting statistics (must be CS admin)
        db: Database session
        
    Returns:
        Statistics with approved/rejected counts and approval rate
    """
    # Verify CS admin access
    user = await verify_cs_admin_role(user_id, db)
    
    query = select(Application).where(
        Application.cs_decision.isnot(None)
    )
    
    if session_id:
        query = query.where(Application.session_id == session_id)
    
    result = await db.execute(query)
    applications = result.scalars().all()
    
    approved_count = sum(1 for app in applications if app.cs_decision == CSDecision.approved)
    rejected_count = sum(1 for app in applications if app.cs_decision == CSDecision.rejected)
    
    return {
        "total_decisions": len(applications),
        "approved": approved_count,
        "rejected": rejected_count,
        "approval_rate": f"{(approved_count / len(applications) * 100):.1f}%" if applications else "0%"
    }

async def get_cs_dashboard_applications(
    session_id: UUID | None,
    user_id: UUID,
    db: AsyncSession
) -> list[dict]:
    """
    Get CS dashboard data with all CS_PREPARATION applications.
    
    Requires: CS admin access (admin_dpgr or assistant_dpgr)
    
    Args:
        session_id: Optional filter by session
        user_id: User requesting the dashboard (must be CS admin)
        db: Database session
        
    Returns:
        List of applications ready for CS deliberation
    """
    # Verify CS admin access
    user = await verify_cs_admin_role(user_id, db)
    
    query = select(Application).where(Application.status == Status.SUBMITTED)
    
    if session_id:
        query = query.where(Application.session_id == session_id)
    
    query = query.options(
        joinedload(Application.user),
        joinedload(Application.session)
    ).order_by(desc(Application.score), desc(Application.submitted_at))
    
    result = await db.execute(query)
    applications = result.unique().scalars().all()
    
    dashboard_data = []
    for app in applications:
        dashboard_data.append({
            "id": str(app.id),
            "user_name": f"{app.user.username} {app.user.lastname}" if app.user else "Unknown",
            "user_grade": app.user.grade if app.user else None,
            "stage_type": app.stage_type,
            "destination_country": app.destination_country,
            "host_institution": app.host_institution,
            "start_date": app.start_date,
            "end_date": app.end_date,
            "score": app.score,
            "is_eligible": app.is_eligible,
            "status": app.status,
            "submitted_at": app.submitted_at,
            "session_id": str(app.session_id) if app.session_id else None,
            "cs_decision": app.cs_decision,
            "rejection_reason": app.rejection_reason
        })
    
    return dashboard_data

async def get_applications_for_cs_preparation(
    session_id: UUID,
    db: AsyncSession
) -> list[Application]:
    """
    Get all applications eligible for CS preparation (status = SUBMITTED, is_eligible = True)
    for a specific session, ready for CS deliberation.
    """
    result = await db.execute(
        select(Application)
        .where(
            and_(
                Application.session_id == session_id,
                Application.status == Status.SUBMITTED,
                Application.is_eligible == True
            )
        )
        .options(
            joinedload(Application.user),
            joinedload(Application.session)
        )
        .order_by(desc(Application.submitted_at))
        .order_by(asc(Application.is_eligible))
    )
    return result.unique().scalars().all()