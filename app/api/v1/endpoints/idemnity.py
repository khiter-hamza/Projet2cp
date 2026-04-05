from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from app.schemas.indemnity import *
from app.services.financial.indemnity_service import *
from app.core.database import AsyncSessionLocal, get_db




app = APIRouter()





@app.post("/createIdemnity", response_model = IdemnityResonse)
async def createIdemnity(idemnity : CreateIdemnity , db : AsyncSessionLocal = Depends(get_db)) -> IdemnityResonse :
    return await create_idemnity(idemnity , db)






@app.delete("/deleteIdemnity" )
async def delete(idemnity_id : str , db : AsyncSessionLocal = Depends(get_db)):
    # call the service with provided id
    return await delete_idemnity(idemnity_id, db)




@app.post("/createZone", response_model = ZoneResponse)
async def createzone(zone : CreateZone , db : AsyncSessionLocal = Depends(get_db)):
    return await create_zone(zone , db)



@app.get("/zones", response_model = list[ZoneResponse])
async def getzones(db : AsyncSessionLocal = Depends(get_db)):
    return await get_zones(db)

@app.delete("/zone")
async def deletezone(zone_id : UUID , db : AsyncSessionLocal = Depends(get_db)):
    return await delete_zone(zone_id , db)

