import uuid
from datetime import date

from app.models.enums import Status
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.application import Application
from app.models.session import Session
from app.models.user import User
from app.schemas.session import CreateSession, SessionResponse, UpdateSession
from app.services.notification.notification_service import create_notification, notify_admins
from app.models.enums import NotificationType
router = APIRouter()


@router.post("/", response_model=SessionResponse)
async def create_session(
    data: CreateSession,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role.value != "assistant_dpgr":
        raise HTTPException(status_code=403, detail="Not authorized")
    if data.start_date >= data.end_date:
        raise HTTPException(status_code=400, detail="start_date must be before end_date")
    if data.end_date < date.today():
        raise HTTPException(status_code=400, detail="end_date must be in the future")
    try:
        res = await db.execute(
            select(Session)
            .options(joinedload(Session.applications).joinedload(Application.user))
            .where(Session.is_active == True)
        )
        result = res.unique().scalar_one_or_none()
        if result:
            applications = result.applications
            # Archive previous active session and expire unfinished applications.
            for app in applications:
                if app.status != Status.CANCELLED and app.status != Status.COMPLETED and app.status != Status.CLOSED:
                    app.status = Status.EXPIRED
                    await create_notification(
                 db,
                 app.user_id,
                 "Expired Application",
                 "Your application has been expired due to the session ending.",
                 NotificationType.status_change,
                 demande_id=app.id,
             )
                    await notify_admins(
                        db,
                        "Application Expired",
                        f"The Application of {app.user.username} {app.user.lastname} has been expired due to the session ending,Application ID: {app.id}.",
                        NotificationType.status_change,
                        demande_id=app.id,
                    )
            result.is_open = False
            result.is_active = False
            await db.commit()

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"internal server error {str(e)}")
    new_session = Session(
        name=data.name,
        academic_year=data.academic_year,
        start_date=data.start_date,
        end_date=data.end_date,
        is_active=True,
        is_open=True,
        created_by=user.id,
    )
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    return new_session


@router.get("/", response_model=list[SessionResponse])
async def list_sessions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role.value != "assistant_dpgr":
        raise HTTPException(status_code=403, detail="Not authorized")
    result = await db.execute(select(Session).order_by(Session.created_at.desc()))
    return result.scalars().all()


@router.get("/active", response_model=SessionResponse)#for the front end  to get the active session if there is no active session it will return 404 and the front end can handle it by showing a message or something like that//
async def get_active_session(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Session).where(Session.is_active == True)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="No active session")
    return session


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role.value != "assistant_dpgr":
        raise HTTPException(status_code=403, detail="Not authorized")
    session = await db.get(Session, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

#to be deleted

@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: uuid.UUID,
    data: UpdateSession,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role.value != "assistant_dpgr":
        raise HTTPException(status_code=403, detail="Not authorized")
    session = await db.get(Session, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    update_data = data.model_dump(exclude_unset=True)
    if "start_date" in update_data or "end_date" in update_data:
        new_start = update_data.get("start_date", session.start_date)
        new_end = update_data.get("end_date", session.end_date)
        if new_start >= new_end:
            raise HTTPException(status_code=400, detail="start_date must be before end_date")

    if update_data.get("is_active") is True:
        await db.execute(
            update(Session)
            .where(Session.id != session_id)
            .values(is_active=False)
        )

    for field, value in update_data.items():
        setattr(session, field, value)

    await db.commit()
    await db.refresh(session)
    return session


@router.delete("/{session_id}")
async def delete_session(
    session_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role.value != "assistant_dpgr":
        raise HTTPException(status_code=403, detail="Not authorized")
    session = await db.get(Session, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    await db.delete(session)
    await db.commit()
    return {"detail": "Session deleted"}


@router.patch('/{session_id}/close')
async def close_session(session_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    if user.role.value not in ["assistant_dpgr", "admin_dpgr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    res=await db.execute(select(Session).options(
               joinedload(Session.applications).joinedload(Application.user)).where(Session.is_active == True, Session.id==session_id))
    result = res.unique().scalar_one_or_none()
    if result:
        applications=result.applications
        #for those who are in draft status we will change their status to submitted because the session is closed and they can't edit their application anymore and they can only see it and they can see the status of their application is submitted and they can see the date of submission of their application which is the date of closing of the session and for those who are in submitted status we will keep their status as submitted because they have already submitted their application and they can see the date of submission of their application which is the date of closing of the session and for those who are in accepted or rejected status we will keep their status as it is because they have already received a decision on their application and they can see the date of decision on their application which is the date of closing of the session
        for app in applications:
            if app.status==Status.DRAFT:
             app.status=Status.SUBMITTED
             await create_notification(
                 db,
                user_id=app.user_id,
                title="Your application has been submitted",
                message=f"Your application has been submitted for review.",
                notification_type=NotificationType.status_change
            )
             await notify_admins(
                db,
                title="New Application Submitted",
                message=f"Researcher {app.user.username} {app.user.lastname} has submitted an application ({app.id}).",
                notification_type=NotificationType.status_change,
                demande_id=app.id
            )
        result.is_open = False
        await db.commit()
        return result
    raise HTTPException(status_code=404, detail="Active session not found")


@router.patch('/{session_id}/archive') # for douaa
async def archive_session(session_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    if user.role.value not in ["assistant_dpgr", "admin_dpgr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    res=await db.execute(select(Session).options(
               joinedload(Session.applications).joinedload(Application.user)).where(Session.is_active == True, Session.id==session_id))
    result = res.unique().scalar_one_or_none()
    if result:
        applications=result.applications
        #for those who are not closed or completed or canceled we will change their status to expired because the session is archived and they can't do anything with their application anymore and they can only see it and they can see the status of their application is expired and they can see the date of expiration of their application which is the date of archiving of the session and for those who are in closed or completed or canceled status we will keep their status as it is because they have already received a decision on their application and they can see the date of decision on their application which is the date of closing of the session
        for app in applications:
            if app.status!=Status.CANCELLED and app.status!=Status.COMPLETED and app.status!=Status.CLOSED:
             app.status=Status.EXPIRED
             await create_notification(
                 db,
                    user_id=app.user_id,
                    title="Your application has been expired",
                    message=f"Your application has been expired due to the session being archived.",
                    notification_type=NotificationType.status_change
                )
             await notify_admins(
                    db,
                    title="Application Expired",
                    message=f"The Application of {app.user.username} {app.user.lastname} has been expired due to the session being archived,Application ID: {app.id}.",
                    notification_type=NotificationType.status_change,
                    demande_id=app.id
                )
        result.is_open = False
        result.is_active = False
        await db.commit()
        return result
    raise HTTPException(status_code=404, detail="Active session not found")
