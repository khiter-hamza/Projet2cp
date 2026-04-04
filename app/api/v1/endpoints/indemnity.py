from fastapi import APIRouter , Depends ,HTTPException
from app.schemas.indemnity import *
from app.services.financial.indemnity_service import *
from app.core.database import AsyncSessionLocal , get_db




app = APIRouter()





@app.post("/createIndemnity", response_model = IndemnityResponse)
async def createIndemnity(indemnity : CreateIndemnity , db : AsyncSessionLocal = Depends(get_db)) -> IndemnityResponse :
    return await create_indemnity(indemnity , db)






@app.delete("/deleteIndemnity" )
async def delete(indemnity_id : str , db : AsyncSessionLocal = Depends(get_db)):
    return await delete_indemnity(indemnity_id , db)




@app.post("/createZone", response_model = ZoneResponse)
async def createzone(zone : CreateZone , db : AsyncSessionLocal = Depends(get_db)):
    return await create_zone(zone , db)



@app.get("/zones", response_model = list[ZoneResponse])
async def getzones(db : AsyncSessionLocal = Depends(get_db)):
    return await get_zones(db)

@app.delete("/zone")
async def deletezone(zone_id : UUID , db : AsyncSessionLocal = Depends(get_db)):
    return await delete_zone(zone_id , db)

