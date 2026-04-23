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

@router.get("/current", response_model=ApplicationResponse)
async def get_current_application_endpoint(db: Annotated[AsyncSession, Depends(get_db)], user_id: Annotated[UUID, Depends(get_current_user_id)]):
    return await getCurrentApplication(db, user_id)


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

@router.post("/{app_id}/cancel_confirm")
async def cancel_application_confirm_endpoint(
    app_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user_id: Annotated[UUID, Depends(get_current_user_id)]
):
    return await cancel_application_confirm(app_id, db, user_id)

@router.post("/{app_id}/close_application", response_model=ApplicationResponse)
async def close_application_endpoint(app_id: UUID, db: Annotated[AsyncSession, Depends(get_db)], user_id: Annotated[UUID, Depends(get_current_user_id)]):
    return await close_application(app_id, db, user_id)

@router.delete("/{app_id}", status_code=204)
async def delete_draft_endpoint(app_id: UUID, db: Annotated[AsyncSession, Depends(get_db)], user_id: Annotated[UUID, Depends(get_current_user_id)]):
    return await deleteDraft(app_id, db, user_id)



@router.post("/{app_id}/flag")
async def flag_endpoint(app_id: UUID ,reason:str, db:Annotated[AsyncSession, Depends(get_db)], user_id:Annotated[UUID,Depends(get_current_user_id)]):
    return await flag(app_id, db, flagReason=reason, user_id=user_id)

#i need it after
"""    if document_type == Documents_type.report:
        app = await db.get(Application, application_id)
        if app:
            app.stage_report_submitted = True
            now = datetime.utcnow()
            app.stage_report_submitted_at = now
            app.stage_report_id = new_document.id
            
            # Transition to COMPLETED if it was APPROVED
            if app.status == Status.APPROVED:
                app.status = Status.COMPLETED
                app.completed_at = now 
"""