from sqlalchemy import select
from sqlalchemy.orm import joinedload
from app.core.database import AsyncSessionLocal
from app.models.laboratory import Laboratory
from uuid import UUID

async def get_laboratories(db: AsyncSessionLocal):
    result = await db.execute(select(Laboratory))
    return result.scalars().all()

async def get_laboratory(db: AsyncSessionLocal, lab_id: UUID):
    result = await db.execute(select(Laboratory).where(Laboratory.id == lab_id))
    return result.scalar_one_or_none()

async def create_laboratory(name: str, db: AsyncSessionLocal):
    
    existing = await db.execute(select(Laboratory).where(Laboratory.name == name))
    if existing.scalar_one_or_none():
        raise ValueError("Laboratory name already exists")
    
    new_lab = Laboratory(name=name)
    db.add(new_lab)
    await db.commit()
    await db.refresh(new_lab)
    return new_lab

async def update_laboratory(lab_id: UUID, name: str, db: AsyncSessionLocal):
    result = await db.execute(select(Laboratory).where(Laboratory.id == lab_id))
    lab = result.scalar_one_or_none()
    if not lab:
        raise ValueError("Laboratory not found")
    
    
    existing = await db.execute(select(Laboratory).where(Laboratory.name == name, Laboratory.id != lab_id))
    if existing.scalar_one_or_none():
        raise ValueError("Laboratory name already exists")
        
    lab.name = name
    await db.commit()
    await db.refresh(lab)
    return lab

async def delete_laboratory(lab_id: UUID, db: AsyncSessionLocal):
    try:
        result = await db.execute(select(Laboratory).options(joinedload(Laboratory.users)).where(Laboratory.id == lab_id))
        lab = result.unique().scalar_one_or_none()
        if not lab:
            raise ValueError("Laboratory not found")
            
       
        if lab.users:
            for user in lab.users:
                user.laboratory_id = None
            await db.flush() 
            
        await db.delete(lab)
        await db.commit()
        return True
    except Exception as e:
        await db.rollback()
        raise ValueError(f'Failed to delete laboratory: {str(e)}')
        
    
    
    
