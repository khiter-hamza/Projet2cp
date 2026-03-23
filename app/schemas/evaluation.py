"""
Evaluation & Scoring Schemas

Response models for scoring and evaluation criteria.
"""

from pydantic import BaseModel
from uuid import UUID
from typing import Optional


class ScoreResponse(BaseModel):
    """Score calculation response"""
    score: float
    completed: int  # Number of completed applications
    applications: int  # Total number of applications
    
    class Config:
        from_attributes = True


class ScoringDetailResponse(BaseModel):
    """Detailed scoring breakdown"""
    application_id: UUID
    user_id: UUID
    score: float
    
    # Criteria values
    completed_applications: int
    total_applications: int
    
    # Breakdown
    score_from_completed: float  # completed * 10
    score_from_total: float  # total * 5
    
    class Config:
        from_attributes = True
