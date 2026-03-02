from pydantic import BaseModel
from uuid import UUID
from app.models.enums import *
from datetime import date , datetime
from pydantic import Field
#all models has a relation with application

class ApplicationResponse(BaseModel):
    """Réponse complète"""
    id: UUID
    user_id: UUID
    status: Status
    stage_type: StageType | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    destination_country: Countries | None = None
    destination_city: str | None = None
    host_institution: str | None = None
    scientific_objective: str | None = None
    score: float | None = None
    cs_decision: CSDecision | None = None
    rejection_reason: str | None = None
    calculated_fees: float | None = None
    created_at: datetime
    submitted_at: datetime | None = None
    
    class Config:
        from_attributes = True

class ApplicationUpsert(BaseModel):
    """Pour créer OU modifier un brouillon"""
    start_date: date | None = None
    end_date: date | None = None
    destination_country: Countries | None = None
    host_institution: str | None = Field(None, max_length=255)
    scientific_objective: str | None = None
