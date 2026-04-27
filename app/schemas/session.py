import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class CreateSession(BaseModel):
    name: str
    academic_year: str
    start_date: date
    end_date: date
    budget: float


class UpdateSession(BaseModel):
    name: Optional[str] = None
    academic_year: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget: Optional[float] = None
    is_open: Optional[bool] = None
    is_active: Optional[bool] = None


class SessionResponse(BaseModel):
    id: uuid.UUID
    name: str
    academic_year: str
    start_date: date
    end_date: date
    budget: float
    is_open: bool
    is_active: bool
    created_by: Optional[uuid.UUID] = None
    created_at: datetime

    model_config = {"from_attributes": True}
