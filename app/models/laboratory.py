import uuid
from sqlalchemy import Column , Integer , String ,Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base

class Laboratory(Base) :
    __tablename__ = "laboratories"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String , index=True , nullable = False)
    users = relationship("User", back_populates="laboratory")
    
