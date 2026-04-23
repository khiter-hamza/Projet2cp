import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.session import Session
from app.models.user import User
from app.schemas.session import CreateSession, SessionResponse, UpdateSession

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
        await db.execute(update(Session).values(is_active=False,is_open=False))
        #applications_to_be_removed 
        #application_to_be_expired
        #HAMAIDI IMPLEMENT THIS
        await db.commit()
    except Exception as e:
        db.rollback()
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

@router.patch('/{session_id}') # for douaa
async def close_session(session_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    if user.role.value != "admin_dpgr":
        raise HTTPException(status_code=403, detail="Not authorized")
    session = await db.get(Session, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.is_active=False
    await db.commit()
    return session

