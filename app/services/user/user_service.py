from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.schemas.user import CreateUser, UserResponse
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.laboratory import Laboratory
from app.core.security import hash_password
from uuid import UUID


async def create_user(user: CreateUser, db: AsyncSessionLocal) -> UserResponse:
    hashed_pwd = hash_password(user.password)

    # Resolve laboratory: find by name or create it
    result = await db.execute(select(Laboratory).where(Laboratory.name == user.laboratory_name))
    lab = result.scalar_one_or_none()
    if not lab:
        lab = Laboratory(name=user.laboratory_name)
        db.add(lab)
        # flush to populate lab.id without committing
        await db.flush()

    new_user = User(
        email=user.email,
        hashed_password=hashed_pwd,
        username=user.username,
        lastname=user.lastname,
        role=user.role,
        grade=user.grade,
        is_active=user.is_active,
        anciente=user.anciente,
        laboratory_id=lab.id,
    )

    new_user.laboratory = lab
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    new_user.laboratory = lab # ensure it's not expired by refresh
    return UserResponse.model_validate(new_user)


async def get_users(db: AsyncSessionLocal) -> list[UserResponse]:
    result = await db.execute(select(User).options(selectinload(User.laboratory)))
    users = result.scalars().all()
    return [UserResponse.model_validate(u) for u in users]


async def get_user(db: AsyncSessionLocal, user_id: str):
    from uuid import UUID as _UUID

    uid = _UUID(user_id) if isinstance(user_id, str) else user_id
    result = await db.execute(select(User).where(User.id == uid).options(selectinload(User.laboratory)))
    user = result.scalar_one_or_none()
    return user


async def update_user(new_user: CreateUser, user_id: UUID, db: AsyncSessionLocal) -> UserResponse:
    """
    Update user fields - only updates non-null fields from new_user.
    Preserves existing values for fields that are None in new_user.
    """
    result = await db.execute(select(User).where(User.id == user_id).options(selectinload(User.laboratory)))
    user = result.scalar_one_or_none()

    if not user:
        raise ValueError('User not found')

    # Get only the fields that were explicitly set (exclude unset fields)
    update_data = new_user.model_dump(exclude_unset=True)

    # Update only non-null fields
    for field, value in update_data.items():
        if value is not None:
            # Hash password if updating password
            if field == 'password' and value:
                value = hash_password(value)
                setattr(user, 'hashed_password', value)
            elif field == 'laboratory_name':
                lab_result = await db.execute(select(Laboratory).where(Laboratory.name == value))
                lab = lab_result.scalar_one_or_none()
                if not lab:
                    lab = Laboratory(name=value)
                    db.add(lab)
                    await db.flush()
                setattr(user, 'laboratory_id', lab.id)
                user.laboratory = lab # explicitly set to avoid lazy load after refresh
            else:
                setattr(user, field, value)

    try:
        await db.commit()
        await db.refresh(user)
    except Exception as e:
        await db.rollback()
        raise ValueError(f'Failed to update user: {str(e)}')

    return UserResponse.model_validate(user)
