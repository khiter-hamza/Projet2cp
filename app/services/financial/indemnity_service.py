

from app.models.indemnity_calculation import Idemnity
from app.models.zone import Zone
from app.core.database import AsyncSessionLocal
from sqlalchemy import select, func
from datetime import datetime, timedelta
from app.schemas.indemnity import *
from uuid import UUID
from app.services.auth_service_utils import (
    verify_cs_admin_role,
    verify_super_admin_role,
    verify_cs_admin_or_chercheur
)


async def calculate_budjet(idemnity: Idemnity, db: AsyncSessionLocal):
   
    
    zone = idemnity.zone
    
    if not zone :
       raise ValueError("zone not found for this idemnity")
    
    
    
    if isinstance(idemnity.date , int) :
        days= idemnity.date
    else :
        days = idemnity.date.day
    
    
    
    if zone.type == 1 :
        budjet_1_10 = 12000
        budjet_11_29_daily = 4000
        budjet_11_29_forfait = 120000
        budjet_multiple_month = 200000
        budjet_fraction_forfait = 200000
        budjet_fraction_daily = 6000
    elif zone.type == 2 :
        budjet_1_10 = 10000
        budjet_11_29_daily = 3000
        budjet_11_29_forfait = 100000
        budjet_multiple_month = 160000
        budjet_fraction_forfait = 160000
        budjet_fraction_daily = 5000
     
     
     
     
     
    if days <= 10 :
        budjet = budjet_1_10 * days
    elif days <= 29 :
        extra_days = days - 10
        budjet = budjet_11_29_forfait + (extra_days * budjet_11_29_daily)
    else :
        n_months = days // 30
        fraction_days = days % 30
        
        if fraction_days == 0 :
            budjet = n_months * budjet_multiple_month
        else :
            budjet = (n_months * budjet_multiple_month) + budjet_fraction_forfait + (fraction_days * budjet_fraction_daily)
    
    
    return budjet 


async def create_idemnity(idemnity : CreateIdemnity, user_id: UUID, db : AsyncSessionLocal ) -> IdemnityResonse:
    """
    Create a new indemnity record.
    
    Authorization: CS admin only (admin_dpgr or asistant_dpgr)
    """
    user = await verify_cs_admin_role(user_id, db)
   
    zone_result = await db.execute(select(Zone).where(Zone.name == idemnity.zone_name))
    zone = zone_result.scalar_one_or_none()
    
    if not zone:
        raise ValueError("Zone not found")
    
    new_idemnity = Idemnity(date = idemnity.date , zone_id = zone.id) 
    db.add(new_idemnity)
    await db.commit()
    await db.refresh(new_idemnity)
    
    budjet = await calculate_budjet(new_idemnity , db)
    new_idemnity.budjet = budjet
    db.add(new_idemnity)
    await db.commit()
    await db.refresh(new_idemnity)
    
    return IdemnityResonse.model_validate(new_idemnity)


async def delete_idemnity(idemnity_id: str, user_id: UUID, db: AsyncSessionLocal) -> bool:
    """
    Delete an indemnity by ID.
    
    Authorization: super_admin only
    """
    user = await verify_super_admin_role(user_id, db)
    
    result = await db.execute(select(Idemnity).where(Idemnity.id == idemnity_id))
    idemnity = result.scalar_one_or_none()
    
    if not idemnity:
        raise ValueError("Indemnity not found")
    
    await db.delete(idemnity)
    await db.commit()
    
    return True



async def create_zone(zone : CreateZone, user_id: UUID, db : AsyncSessionLocal):
    """
    Create a new zone.
    
    Authorization: super_admin only
    """
    user = await verify_super_admin_role(user_id, db)
    
    new_zone = Zone(name = zone.name , type = zone.type)
    db.add(new_zone)
    await db.commit()
    await db.refresh(new_zone)
    return new_zone




async def get_zones(user_id: UUID, db : AsyncSessionLocal):
    """
    Get all zones.
    
    Authorization: chercheur + CS admin (anyone viewing applications)
    """
    user = await verify_cs_admin_or_chercheur(user_id, db)
    
    result = await db.execute(select(Zone))
    zones = result.scalars().all()
    return [ZoneResponse.model_validate(u) for u in zones ]
    
    
async def delete_zone(zone_id : str, user_id: UUID, db : AsyncSessionLocal ):
    """
    Delete a zone.
    
    Authorization: super_admin only
    """
    user = await verify_super_admin_role(user_id, db)
    
    result = await db.execute(select(Zone).where(Zone.id == zone_id))
    zone = result.scalar_one_or_none()
    if not  zone :
        raise ValueError("zone not found")
    await db.delete(zone)
    await db.commit()
    return True
    
