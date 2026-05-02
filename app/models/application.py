from sqlalchemy import Column,  Date, String, Enum, ForeignKey, Text, Boolean, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from uuid import uuid4
from app.core.database import Base
from app.models.enums import *
from app.models.indemnity_calculation import Idemnity
from datetime import datetime
class Application(Base):
    __tablename__ = "applications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    stage_type = Column(Enum(StageType) ,nullable=False)
    status = Column(Enum(Status), default=Status.DRAFT, nullable=False, index=True)
    
    start_date = Column(Date, index=True)
    end_date = Column(Date)
    
    host_supervisor =  Column(String(100))
    supervisor_email =  Column(String(50))
    host_department =  Column(String(100))
    title_of_stay =  Column(String(100))
    research_axis =  Column(String(50))
    destination_country = Column(String(100))
    destination_city = Column(String(100))
    host_institution = Column(String(255))
    
    expected_outcomes = Column(Text)
    scientific_objective = Column(Text)
    
    score = Column(Float)
    
    is_eligible = Column(Boolean,nullable=True,index=True)
    verification_errors = Column(Text, nullable=True)  # Comma-separated list of errors
    
    cs_decision = Column(Enum(CSDecision), nullable=True, index=True)
    rejection_reason = Column(Text)
    #this for report and attestation,it just help the front end and it change during api call or at the generation of the attestation in the cs decision
    stage_report_id=Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    stage_report_submitted = Column(Boolean, default=False, nullable=False)
    stage_report_submitted_at = Column(DateTime, nullable=True)
    attestation_id=Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    attestation_submitted = Column(Boolean, default=False, nullable=False)
    attestation_submitted_at = Column(DateTime, nullable=True)
    #

    calculated_fees = Column(Float)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True)
    
    
    
    cancellation_reason = Column(Text)
    action_confirmation_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.today, index=True)
    submitted_at = Column(DateTime, index=True)
    approved_at = Column(DateTime, index=True)
    rejected_at = Column(DateTime, index=True)
    completed_at = Column(DateTime)#can be removed
    closed_at = Column(DateTime)
    cancelled_requested_at = Column(DateTime)
    cancelled_at = Column(DateTime)
    user = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="applications"
    )
    action_confirmation_by = relationship("User", foreign_keys=[action_confirmation_by_id])


    session = relationship("Session", back_populates="applications")
    idemnities = relationship(Idemnity, back_populates="application")
    documents = relationship(
    "Document",
    back_populates="application",
    foreign_keys="Document.application_id"
    )
    stage_report = relationship(
    "Document",
    foreign_keys=[stage_report_id],
    post_update=True
    )

    attestation = relationship(
    "Document",
    foreign_keys=[attestation_id],
    post_update=True
    )
