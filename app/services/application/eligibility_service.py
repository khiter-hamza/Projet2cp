"""
Eligibility Verification Service

Handles automatic eligibility checks for applications based on:
1. User grade and stage type criteria
2. User's application history
3. Required documents
"""

from datetime import datetime
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.application import Application
from app.models.user import User
from app.models.document import Document
from app.models.enums import (
    UserGrade, StageType, Status, Documents_type
)
from app.schemas.eligibility import (
    EligibilityCheckResult,
    EligibilityDetailedResponse,
    HistoryCheckDetail,
    DocumentCheckDetail
)


# Required documents based on stage type
REQUIRED_DOCUMENTS_BY_STAGE = {
    StageType.stage_perfectionnement: [
        Documents_type.invitation,
        Documents_type.programme,
        Documents_type.cv,
        Documents_type.passport,
        Documents_type.accord_labo,
    ],
    StageType.sejour_scientifique: [
        Documents_type.invitation,
        Documents_type.programme,
        Documents_type.cv,
        Documents_type.passport,
        Documents_type.accord_labo,
    ]
}

# Duration constraints by grade
DURATION_CONSTRAINTS = {
    UserGrade.doctorant_non_salarie: {"min": 15, "max": 30, "stage_type": StageType.stage_perfectionnement},
    UserGrade.doctorant_salarie: {"min": 15, "max": 30, "stage_type": StageType.stage_perfectionnement},
    UserGrade.enseignant_chercheur: {"min": 15, "max": 30, "stage_type": StageType.stage_perfectionnement},
    UserGrade.professeur: {"duration": 7, "stage_type": StageType.sejour_scientifique},
    UserGrade.mca_a: {"duration": 7, "stage_type": StageType.sejour_scientifique},
    UserGrade.mca_b: {"min": 7, "max": 15, "stage_type": StageType.sejour_scientifique, "max_count": 4},
}


async def check_eligibility_by_grade(
    user: User,
    application: Application,
    db: AsyncSession
) -> tuple[bool, str]:
    """
    Check if user's grade allows this stage type and duration.
    
    Returns: (is_eligible: bool, message: str)
    """
    user_grade = user.grade
    stage_type = application.stage_type
    
    # Calculate duration in days
    if application.start_date and application.end_date:
        duration_days = (application.end_date - application.start_date).days
    else:
        return False, "Start and end dates are required"
    
    # Check if user grade can do this stage type
    if user_grade not in DURATION_CONSTRAINTS:
        return False, f"User grade '{user_grade}' is not eligible for any stage/séjour"
    
    constraints = DURATION_CONSTRAINTS[user_grade]
    
    # Check stage type match
    if constraints.get("stage_type") != stage_type:
        return False, f"User grade '{user_grade}' cannot do {stage_type}"
    
    # Check duration for specific length stages (7 days)
    if "duration" in constraints:
        if duration_days != constraints["duration"]:
            return False, f"Séjour must be exactly {constraints['duration']} days for grade '{user_grade}'"
    
    # Check duration range (15-30 days)
    if "min" in constraints and "max" in constraints:
        if not (constraints["min"] <= duration_days <= constraints["max"]):
            return False, f"Duration must be between {constraints['min']} and {constraints['max']} days"
    
    return True, "Grade eligibility passed"


async def check_history(
    user_id: UUID,
    user: User,
    application: Application,
    db: AsyncSession
) -> tuple[bool, str, HistoryCheckDetail]:
    """
    Check user's application history for restrictions.
    
    Returns: (is_eligible: bool, message: str, history_details: HistoryCheckDetail)
    """
    
    # Get all completed applications for this user
    result = await db.execute(
        select(Application).where(
            Application.user_id == user_id,
            Application.status.in_([Status.COMPLETED, Status.CLOSED])
        )
    )
    completed_apps = result.scalars().all()
    
    # Get all submitted applications (including current)
    result = await db.execute(
        select(Application).where(
            Application.user_id == user_id,
            Application.status != Status.DRAFT
        )
    )
    all_submitted = result.scalars().all()
    
    # Calculate totals
    total_applications = len(all_submitted)
    completed_applications = len(completed_apps)
    
    total_days_consumed = 0
    last_stage_date = None
    
    for app in completed_apps:
        if app.start_date and app.end_date:
            days = (app.end_date - app.start_date).days
            total_days_consumed += days
            
            if last_stage_date is None or app.end_date > last_stage_date:
                last_stage_date = app.end_date
    
    # Calculate days since last stage
    days_since_last = None
    if last_stage_date:
        days_since_last = (datetime.utcnow().date() - last_stage_date).days
    
    history_detail = HistoryCheckDetail(
        total_applications=total_applications,
        completed_applications=completed_applications,
        total_days_consumed=total_days_consumed,
        last_stage_date=last_stage_date,
        days_since_last_stage=days_since_last
    )
    
    # Check MCA-B limit (max 4 séjours)
    if user.grade == UserGrade.mca_b:
        mca_b_count = len([
            app for app in completed_apps
            if app.stage_type == StageType.sejour_scientifique
        ])
        if mca_b_count >= 4:
            return False, "MCA-B users are limited to 4 scientific séjours", history_detail
    
    # Check if user has at least some history (encouraged but not required)
    eligible = True
    message = "History check passed"
    
    if completed_applications == 0:
        message = "User has no completed stages/séjours yet (first time)"
    
    return eligible, message, history_detail


async def check_documents(
    application_id: UUID,
    stage_type: StageType,
    db: AsyncSession
) -> tuple[bool, str, DocumentCheckDetail]:
    """
    Check if all required documents are uploaded.
    
    Returns: (all_present: bool, message: str, document_details: DocumentCheckDetail)
    """
    
    required_docs = REQUIRED_DOCUMENTS_BY_STAGE.get(stage_type, [])
    
    # Get all uploaded documents for this application
    result = await db.execute(
        select(Document).where(
            Document.application_id == application_id
        )
    )
    uploaded_docs = result.scalars().all()
    
    uploaded_types = [doc.document_type for doc in uploaded_docs]
    
    # Find missing documents
    missing_docs = [
        doc.value for doc in required_docs if doc not in uploaded_types
    ]
    
    all_present = len(missing_docs) == 0
    
    document_detail = DocumentCheckDetail(
        required_documents=[doc.value for doc in required_docs],
        uploaded_documents=[doc.value for doc in uploaded_types],
        missing_documents=[doc.value for doc in missing_docs],
        all_documents_present=all_present
    )
    
    if not all_present:
        message = f"Missing documents: {', '.join(missing_docs)}"
    else:
        message = "All required documents are present"
    
    return all_present, message, document_detail


async def perform_eligibility_check(
    application_id: UUID,
    db: AsyncSession
) -> EligibilityCheckResult:
    """
    Main eligibility verification function.
    
    Performs all three checks and returns comprehensive result.
    Updates Application status based on eligibility result.
    """
    
    # Get application with user
    result = await db.execute(
        select(Application)
        .options(joinedload(Application.user))
        .where(Application.id == application_id)
    )
    application = result.unique().scalar_one_or_none()
    
    if not application:
        raise ValueError(f"Application {application_id} not found")
    
    user = application.user
    errors = []
    
    # 1. Check eligibility by grade
    grade_eligible, grade_message = await check_eligibility_by_grade(user, application, db)
    if not grade_eligible:
        errors.append(grade_message)
    
    # 2. Check history
    history_eligible, history_message, history_detail = await check_history(
        application.user_id, user, application, db
    )
    if not history_eligible:
        errors.append(history_message)
    
    # 3. Check documents
    docs_eligible, docs_message, docs_detail = await check_documents(
        application_id, application.stage_type, db
    )
    if not docs_eligible:
        errors.append(docs_message)
    
    # Determine overall eligibility
    is_eligible = (grade_eligible and history_eligible and docs_eligible)
    
    # Update application with results
    application.is_eligible = is_eligible
    application.verified_at = datetime.utcnow()
    application.verification_errors = "; ".join(errors) if errors else None
    
    # Update application status based on eligibility
    if is_eligible:
        application.status = Status.CS_PREPARATION
    else:
        application.status = Status.REJECTED
        application.rejection_reason = "; ".join(errors)
        application.rejected_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(application)
    
    result_obj = EligibilityCheckResult(
        is_eligible=is_eligible,
        verified_at=application.verified_at,
        eligible_by_grade=grade_eligible,
        eligible_by_history=history_eligible,
        eligible_by_documents=docs_eligible,
        errors=errors
    )
    
    return result_obj


async def get_eligibility_details(
    application_id: UUID,
    db: AsyncSession
) -> EligibilityDetailedResponse:
    """
    Get detailed eligibility information for an application.
    """
    
    # Get application with user
    result = await db.execute(
        select(Application)
        .options(joinedload(Application.user))
        .where(Application.id == application_id)
    )
    application = result.unique().scalar_one_or_none()
    
    if not application:
        raise ValueError(f"Application {application_id} not found")
    
    user = application.user
    errors = []
    
    # 1. Check eligibility by grade
    grade_eligible, grade_message = await check_eligibility_by_grade(user, application, db)
    grade_check = {
        "eligible": grade_eligible,
        "message": grade_message
    }
    if not grade_eligible:
        errors.append(grade_message)
    
    # 2. Check history
    history_eligible, history_message, history_detail = await check_history(
        application.user_id, user, application, db
    )
    if not history_eligible:
        errors.append(history_message)
    
    # 3. Check documents
    docs_eligible, docs_message, docs_detail = await check_documents(
        application_id, application.stage_type, db
    )
    if not docs_eligible:
        errors.append(docs_message)
    
    # Overall result
    is_eligible = (grade_eligible and history_eligible and docs_eligible)
    
    return EligibilityDetailedResponse(
        application_id=application.id,
        is_eligible=is_eligible,
        verified_at=application.verified_at or datetime.utcnow(),
        grade_check=grade_check,
        history_check=history_detail,
        document_check=docs_detail,
        errors=errors
    )
