from fastapi import HTTPException ,Depends
from pydantic import ValidationError
from typing import Annotated
from sqlalchemy import select
from app.services.auth.auth_service import get_current_user
from app.core.database import get_db
from app.core.database import AsyncSession
from app.schemas.application import ApplicationResponse , ApplicationUpsert
from app.models.application import Application
from app.models.user import User
from app.models.enums import *
from uuid import UUID



async def createDraft(data:ApplicationUpsert,db:Annotated[AsyncSession,Depends(get_db)] ,user_id: Annotated[UUID , Depends(get_current_user)]):
    id = user_id
    user = await db.get(User,id)
    if(not user):
        raise HTTPException(status_code=404,detail="User not found.")
    result = await db.execute(select(Application).where(Application.user_id==user_id).where(Application.status==Status.brouillon))
    result = result.scalar_one_or_none()
    if(result):
        raise HTTPException(status_code=409,detail="A draft application already exists for this user.")
    data = data.model_dump()
    application = Application(user_id=user.id,**data)
    if(user.grade in (UserGrade.doctorant_non_salarie , UserGrade.doctorant_salarie)):
        application.stage_type = StageType.stage_perfectionnement
    else:
        application.stage_type = StageType.sejour_scientifique

    db.add(application)
    await db.commit()
    await db.refresh(application) 

    try:
        response = ApplicationResponse.model_validate(application)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return response


def updateDraft():
    return

def getApplication():
    return

async def listAllApplications(db:Annotated[AsyncSession,Depends(get_db)]):
    result = await db.execute(select(Application))
    result = result.scalars().all()
    if not result:
        return result
    try:
        result = [ApplicationResponse.model_validate(application) for application in result]
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return result

def submitApplication(app_id:UUID,db:Annotated[AsyncSession,Depends(get_db)]):

    return