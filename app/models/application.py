from sqlalchemy import Column, Integer, Date, String, Enum, ForeignKey, Text, Boolean, Float, DateTime
from sqlalchemy.orm import relationship
from uuid import uuid4 , UUID
from app.core.database import Base
from models.enums import *
from datetime import datetime

class Application(Base):
    __tablename__ = "applications"
    
    id = Column(UUID, primary_key=True, index=True, default=uuid4)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    stage_type = Column(Enum(StageType), nullable=False)
    status = Column(Enum(Status), default=Status.brouillon, nullable=False, index=True)
    
    start_date = Column(Date, nullable=True, index=True)
    end_date = Column(Date, nullable=True)
    
    destination_country = Column(Enum(Countries), nullable=True)
    destination_city = Column(String(100), nullable=True)
    host_institution = Column(String(255), nullable=True)
    
    scientific_objective = Column(Text, nullable=True)
    
    score = Column(Float, nullable=True)
    #anything to add later
#---------THIS SECTION WILL BE REVISED LATER--------------------------    
#is_eligible = Column(Boolean, default=None, nullable=True)
#eligibility_reason = Column(Text, nullable=True) 
    
    cs_decision = Column(Enum(CSDecision), nullable=True)
    rejection_reason = Column(Text, nullable=True)
#cs_decision_date = Column(Date, nullable=True)
#cs_notes = Column(Text, nullable=True)
    
    stage_report_submitted = Column(Boolean, default=False)
    stage_report_path = Column(String(500), nullable=True)
    stage_report_submitted_at = Column(DateTime, nullable=True)
    
#zone = Column(Enum(GeographicZone), nullable=True)
    calculated_fees = Column(Float, nullable=True)
#---------------------------------------------------------------------   
    
    attestation_generated = Column(Boolean, default=False)
    attestation_path = Column(String(500), nullable=True)
    attestation_generated_at = Column(DateTime, nullable=True)
    
    cancellation_reason = Column(Text, nullable=True)
    cancellation_requested_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.today, index=True)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.today)
    submitted_at = Column(DateTime, nullable=True, index=True)
    approved_at = Column(DateTime, nullable=True, index=True)
    rejected_at = Column(DateTime, nullable=True, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)