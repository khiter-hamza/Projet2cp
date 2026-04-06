from uuid import uuid4
from sqlalchemy import Column , String , Integer  , ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


from app.core.database import Base

class Zone(Base) :
    __tablename__ = "zones"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    type = Column(Integer, nullable=False)
    # use String for zone name
    name = Column(String(100), nullable=False)
    
   
    idemnities = relationship("Idemnity", back_populates="zone")
