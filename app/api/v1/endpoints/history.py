from fastapi import APIRouter, Depends, Query
from uuid import UUID
from app.core.database import AsyncSession, get_db
from app.core.dependencies import get_current_user_id
from app.models.enums import Status, CSDecision
from app.schemas.history import (
    ApplicationHistoryListResponse,
    ApplicationHistoryPageResponse,
)
from app.services.application.history_service import (
    get_application_history,
    get_application_history_page,
)

router = APIRouter()

@router.get("/history", response_model=ApplicationHistoryPageResponse)
async def get_application_history_page_endpoint(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("submitted_at"),
    sort_order: str = Query("desc"),
    status: Status | None = Query(None),
    cs_decision: CSDecision | None = Query(None),
    search: str | None = Query(None),
    session_filter: str = Query("this", description="Filter by session: 'this' (current), 'previous', or 'all'"),
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    return await get_application_history_page(
        user_id,
        db,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order,
        status=status,
        cs_decision=cs_decision,
        search=search,
        session_filter=session_filter,
    )


@router.get("/{application_id}/history", response_model=ApplicationHistoryListResponse)
async def get_application_history_endpoint(
    application_id: UUID,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    return await get_application_history(application_id, user_id, db, limit=limit, offset=offset)
