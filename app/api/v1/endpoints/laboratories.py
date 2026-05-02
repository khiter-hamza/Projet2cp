import uuid
from fastapi import APIRouter, Depends, HTTPException
from app.core.database import AsyncSessionLocal, get_db
from app.schemas.laboratory import CreateLaboratory, UpdateLaboratory, LaboratoryResponse
from app.services.laboratory.laboratory_service import (
    create_laboratory, get_laboratories, get_laboratory, update_laboratory, delete_laboratory
)

router = APIRouter()

@router.post("/", response_model=LaboratoryResponse)
async def create_lab_endpoint(lab: CreateLaboratory, db: AsyncSessionLocal = Depends(get_db)):
    try:
        return await create_laboratory(lab.name, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=list[LaboratoryResponse])
async def get_labs_endpoint(db: AsyncSessionLocal = Depends(get_db)):
    return await get_laboratories(db)

@router.get("/{lab_id}", response_model=LaboratoryResponse)
async def get_lab_endpoint(lab_id: uuid.UUID, db: AsyncSessionLocal = Depends(get_db)):
    lab = await get_laboratory(db, lab_id)
    if not lab:
        raise HTTPException(status_code=404, detail="Laboratory not found")
    return lab

@router.put("/{lab_id}", response_model=LaboratoryResponse)
async def update_lab_endpoint(lab_id: uuid.UUID, lab_data: UpdateLaboratory, db: AsyncSessionLocal = Depends(get_db)):
    try:
        return await update_laboratory(lab_id, lab_data.name, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{lab_id}")
async def delete_lab_endpoint(lab_id: uuid.UUID, db: AsyncSessionLocal = Depends(get_db)):
    try:
        await delete_laboratory(lab_id, db)
        return {"message": "Laboratory deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
