#gestion des demandes
from uuid import UUID
from fastapi import APIRouter , Depends , HTTPException
from typing import Annotated
from app.core.database import AsyncSession
from app.core.database import get_db
from app.core.database import get_db
from app.schemas.application import *
from app.services.application.application_service import *

router = APIRouter()

@router.get("/{id}", response_model=ApplicationResponse)
async def get_application_endpoint(id: UUID):
    return getApplication

@router.get("/", response_model=list[ApplicationResponse])
async def list_applications_endpoint(db:Annotated[AsyncSession,Depends(get_db)]):
    return await listAllApplications(db)

@router.post("/", response_model=ApplicationResponse)
async def create_draft_endpoint(data: ApplicationUpsert,db:Annotated[AsyncSession,Depends(get_db)],user_id:Annotated[UUID,Depends(get_current_user)]):
    return await createDraft(data,db,user_id)

@router.patch("/{id}", response_model=ApplicationResponse)
async def update_draft_endpoint(id: UUID, data: ApplicationUpsert):
    return updateDraft

@router.post("/{app_id}/submit", response_model=ApplicationResponse)
async def submit_application_endpoint(app_id: UUID,db:Annotated[AsyncSession,Depends(get_db)]):
    return submitApplication(app_id,db)