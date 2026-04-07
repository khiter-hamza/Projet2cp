from fastapi import APIRouter, Depends
from typing import Optional
from app.core.database import AsyncSession, get_db
from app.core.dependencies import get_current_user_id
from app.services.dashboard.dashboard_service import *
from app.schemas.dashboard import *
from app.schemas.application import ApplicationResponse
from uuid import UUID

router = APIRouter()

@router.get("/researcher", response_model=ResearcherDashboardResponse)
async def get_researcher_dashboard_endpoint(
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id)
):
    """Get dashboard for researcher"""
    return await get_researcher_dashboard(str(user_id), db)

@router.get("/researcher/current-application", response_model=Optional[ApplicationResponse])
async def get_researcher_current_application_endpoint(
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id)
):
    """Get the current session application details for the researcher."""
    return await get_researcher_current_application(str(user_id), db)

@router.get("/admin", response_model=AdminDashboardResponse)
async def get_admin_dashboard_endpoint(
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
    filters: AdminDashboardFilters = Depends(get_admin_dashboard_filters)
):
    """Get dashboard for admin with optional filters"""
    return await get_admin_dashboard(str(user_id), db, filters)

@router.get("/cs", response_model=CSDashboardResponse)
async def get_cs_dashboard_endpoint(
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id)
):
    """Get dashboard for CS deliberation (current session only)"""
    return await get_cs_dashboard(str(user_id), db)

@router.get("/statistics", response_model=StatisticsResponse)
async def get_statistics_endpoint(
    db: AsyncSession = Depends(get_db)
):
    """Get overall system statistics"""
    return await get_statistics(db)