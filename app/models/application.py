from sqlalchemy import Column, Integer, Date, String, Enum, ForeignKey, Text, Boolean, Float, DateTime 
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from uuid import uuid4
from app.core.database import Base
from app.models.enums import *
from datetime import datetime
class Application(Base):
    __tablename__ = "applications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    stage_type = Column(Enum(StageType))
    status = Column(Enum(Status), default=Status.brouillon, nullable=False, index=True)
    
    start_date = Column(Date, index=True)
    end_date = Column(Date)
    
    destination_country = Column(Enum(Countries))
    destination_city = Column(String(100))
    host_institution = Column(String(255))
    
    scientific_objective = Column(Text)
    
    score = Column(Float)
    
    cs_decision = Column(Enum(CSDecision), default=CSDecision.en_attente, index=True)
    rejection_reason = Column(Text)
    
    stage_report_submitted = Column(Boolean, default=False, nullable=False)
    stage_report_path = Column(String(500))
    stage_report_submitted_at = Column(DateTime)
    
    calculated_fees = Column(Float)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True)

    attestation_generated = Column(Boolean, default=False, nullable=False)
    attestation_path = Column(String(500))
    attestation_generated_at = Column(DateTime)
    
    cancellation_reason = Column(Text)
    cancellation_requested_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    
    created_at = Column(DateTime, nullable=False, default=datetime.today, index=True)
    updated_at = Column(DateTime, onupdate=datetime.today)
    submitted_at = Column(DateTime, index=True)
    approved_at = Column(DateTime, index=True)
    rejected_at = Column(DateTime, index=True)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    closed_at = Column(DateTime)
    cancelled_at = Column(DateTime)

    user = relationship(
    "User",
    foreign_keys=[user_id],
    back_populates="applications"
)
    cancellation_requested_by_user = relationship("User", foreign_keys=[cancellation_requested_by])
    documents = relationship("Document", back_populates="application")
    session = relationship("Session", back_populates="applications")
