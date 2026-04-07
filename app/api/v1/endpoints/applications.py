#gestion des demandes
from uuid import UUID
from fastapi import APIRouter , Depends , Query
from typing import Annotated
from app.core.database import AsyncSession
from app.core.database import get_db
from app.core.database import get_db
from app.schemas.application import *
from app.services.application.application_service import *
from app.core.dependencies import get_current_user_id

router = APIRouter()

@router.get("/{id}", response_model=ApplicationResponse)
async def get_User_application_endpoint(id: UUID, db: Annotated[AsyncSession, Depends(get_db)], user_id: Annotated[UUID, Depends(get_current_user_id)]):
    return await getUserApplication(id, user_id, db)

@router.get("/", response_model=list[ApplicationResponse])
async def get_applications_endpoint(db: Annotated[AsyncSession, Depends(get_db)],user_id: Annotated[UUID, Depends(get_current_user_id)],appFilterQuery:Annotated[ApplicationFilterParams,Depends(get_filter_params)]):
    return await listApplications(db,user_id,appFilterQuery)

@router.post("/", response_model=ApplicationResponse)
async def create_draft_endpoint(data: ApplicationUpsert, db: Annotated[AsyncSession, Depends(get_db)], user_id: Annotated[UUID, Depends(get_current_user_id)]):
    return await createDraft(data, db, user_id)

@router.patch("/{id}", response_model=ApplicationResponse)
async def update_draft_endpoint(id: UUID, data: ApplicationUpsert, db: Annotated[AsyncSession, Depends(get_db)], user_id: Annotated[UUID, Depends(get_current_user_id)]):
    return await updateDraft(id, data, db, user_id)

@router.post("/{app_id}/submit", status_code=200)
async def submit_draft_endpoint(app_id: UUID, data: ApplicationUpsert, db: Annotated[AsyncSession, Depends(get_db)], user_id: Annotated[UUID, Depends(get_current_user_id)]):
    return await submitDraft(app_id, data, db, user_id)

@router.post("/{app_id}/cancel", response_model=ApplicationResponse)
async def cancel_application_endpoint(
    app_id: UUID,
    data: ApplicationCancellationRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user_id: Annotated[UUID, Depends(get_current_user_id)]
):
    return await cancel_application(app_id, data, db, user_id)

@router.delete("/{app_id}", status_code=204)
async def delete_draft_endpoint(app_id: UUID, db: Annotated[AsyncSession, Depends(get_db)], user_id: Annotated[UUID, Depends(get_current_user_id)]):
    return await deleteDraft(app_id, db, user_id)