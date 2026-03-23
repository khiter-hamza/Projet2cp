from pydantic import BaseModel 
from datetime import date
from typing import Optional
from uuid import  UUID


class CreateIdemnity(BaseModel):
    zone_name : str
    idemnity_date : date

class IdemnityResonse(BaseModel):
    id : UUID
    idemnity_date : date
    zone_id  : UUID
    budjet : int
    
    model_config = {"from_attributes": True} 
    
    
class CreateZone(BaseModel):
    type : int
    name : str
    


class ZoneResponse(BaseModel):
    id : UUID
    type : int
    name : str
    
    model_config = {"from_attributes": True}
