from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from app.schemas.indemnity import *
from app.services.financial.indemnity_service import *
from app.core.database import AsyncSessionLocal, get_db
from app.core.dependencies import get_current_user_id

app = APIRouter()

@app.post("/createZone", response_model = ZoneResponse)
async def createzone(zone : CreateZone , db : AsyncSessionLocal = Depends(get_db),user_id:UUID=Depends(get_current_user_id)):
    return await create_zone(zone, user_id, db)

@app.get("/zones", response_model = list[ZoneResponse])
async def getzones(db : AsyncSessionLocal = Depends(get_db),user_id:UUID=Depends(get_current_user_id)):
    return await get_zones(user_id, db)

@app.delete("/zone")
async def deletezone(zone_id : UUID , db : AsyncSessionLocal = Depends(get_db),user_id:UUID=Depends(get_current_user_id)):
    return await delete_zone(str(zone_id), user_id, db)

@app.get("/allowance-scales", response_model=list[AllowanceScaleResponse])
async def get_allowance_scales_endpoint(db: AsyncSessionLocal = Depends(get_db), user_id: UUID = Depends(get_current_user_id)):
    return await get_allowance_scales(user_id, db)

@app.put("/allowance-scales/{zone_type}", response_model=AllowanceScaleResponse)
async def update_allowance_scale_endpoint(zone_type: int, scale: AllowanceScaleUpdate, db: AsyncSessionLocal = Depends(get_db), user_id: UUID = Depends(get_current_user_id)):
    return await update_allowance_scale(zone_type, scale, user_id, db)
