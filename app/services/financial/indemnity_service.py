

from app.schemas.indemnity import CreateZone
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


async def calculate_budget(idemnity: Idemnity, application, db: AsyncSessionLocal):
    zone = idemnity.zone
    if not zone:
       raise ValueError("zone not found for this idemnity")
    
    if not application.start_date or not application.end_date:
        raise ValueError("Application start_date and end_date must be set")
        
    days = (application.end_date - application.start_date).days + 1
    
    from app.models.zone import AllowanceScale

    scale_result = await db.execute(select(AllowanceScale).where(AllowanceScale.zone_type == zone.type))
    scale = scale_result.scalar_one_or_none()

    if scale:
        budget_1_10 = scale.days1_10
        budget_11_29_daily = scale.days11_29_day
        budget_11_29_forfait = scale.days11_29_pkg
        budget_multiple_month = scale.month
        budget_fraction_forfait = scale.fraction_pkg
        budget_fraction_daily = scale.fraction_day
    else:
        # Fallback to hardcoded defaults if not configured
        if zone.type == 1 :
            budget_1_10 = 12000
            budget_11_29_daily = 4000
            budget_11_29_forfait = 120000
            budget_multiple_month = 200000
            budget_fraction_forfait = 200000
            budget_fraction_daily = 6000
        elif zone.type == 2 :
            budget_1_10 = 10000
            budget_11_29_daily = 3000
            budget_11_29_forfait = 100000
            budget_multiple_month = 160000
            budget_fraction_forfait = 160000
            budget_fraction_daily = 5000
        else:
            budget_1_10 = 10000
            budget_11_29_daily = 3000
            budget_11_29_forfait = 100000
            budget_multiple_month = 160000
            budget_fraction_forfait = 160000
            budget_fraction_daily = 5000
     
    if days <= 10 :
        budget = budget_1_10 * days
    elif days <= 29 :
        extra_days = days - 10
        budget = budget_11_29_forfait + (extra_days * budget_11_29_daily)
    else :
        n_months = days // 30
        fraction_days = days % 30
        
        if fraction_days == 0 :
            budget = n_months * budget_multiple_month
        else :
            budget = (n_months * budget_multiple_month) + budget_fraction_forfait + (fraction_days * budget_fraction_daily)
    
    return budget


async def generate_indemnity_for_application(application, db: AsyncSessionLocal):
    """
    Produce indemnity budgets strictly bounded to an application instead of loose REST calls.
    Allows passing application object directly during `submitDraft` sequence.
    """
    if not application.destination_country:
        return None  # Can't calculate without a destination
        
    country_name = str(application.destination_country)

    
    # Try finding exact zone by country name (assuming zones cover country names)
    zone_result = await db.execute(select(Zone).where(Zone.name.ilike(f"%{country_name}%")))
    zone = zone_result.scalar_one_or_none()
    
    if not zone:
        # Auto-create zone as type 2 (all remaining countries) directly in session
        # Cannot use create_zone() here as it requires super_admin auth
        zone = Zone(name=country_name, type=2)
        db.add(zone)
        await db.flush()
    
    new_idemnity = Idemnity(date=application.start_date, zone_id=zone.id, app_id=application.id)
    new_idemnity.zone = zone
    db.add(new_idemnity)
    await db.flush()
    
    budget = await calculate_budget(new_idemnity, application, db)
    new_idemnity.budget = budget
    application.calculated_fees = float(budget)
    
    await db.flush()
    return new_idemnity


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

async def get_allowance_scales(user_id: UUID, db: AsyncSessionLocal):
    await verify_cs_admin_or_chercheur(user_id, db)
    from app.models.zone import AllowanceScale
    result = await db.execute(select(AllowanceScale))
    scales = result.scalars().all()
    return [AllowanceScaleResponse.model_validate(s) for s in scales]

async def update_allowance_scale(zone_type: int, scale_data: AllowanceScaleUpdate, user_id: UUID, db: AsyncSessionLocal):
    await verify_super_admin_role(user_id, db)
    from app.models.zone import AllowanceScale
    
    result = await db.execute(select(AllowanceScale).where(AllowanceScale.zone_type == zone_type))
    scale = result.scalar_one_or_none()
    
    if not scale:
        scale = AllowanceScale(zone_type=zone_type)
        db.add(scale)
        
    scale.days1_10 = scale_data.days1_10
    scale.days11_29_pkg = scale_data.days11_29_pkg
    scale.days11_29_day = scale_data.days11_29_day
    scale.month = scale_data.month
    scale.fraction_pkg = scale_data.fraction_pkg
    scale.fraction_day = scale_data.fraction_day
    
    await db.commit()
    await db.refresh(scale)
    return AllowanceScaleResponse.model_validate(scale)
    
