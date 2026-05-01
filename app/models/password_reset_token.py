import uuid
from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens" 
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    token = Column(String(255), nullable=False, unique=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    duration= Column(Integer, nullable=False, default=15*60)  # Duration in minutes
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    user = relationship("User", back_populates="password_reset_tokens")
    already_used= Column(Boolean, default=False, nullable=False)
    def isvalid(self):
     import datetime as dt
     now = datetime.utcnow()
     if self.created_at.tzinfo is not None:
         now = now.replace(tzinfo=dt.timezone.utc)
     return  (not self.already_used) and (now - self.created_at).total_seconds() < self.duration 
    
