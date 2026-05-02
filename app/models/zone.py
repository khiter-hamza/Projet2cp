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

class AllowanceScale(Base):
    __tablename__ = "allowance_scales"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    zone_type = Column(Integer, unique=True, nullable=False) # 1 for Zone I, 2 for Zone II
    days1_10 = Column(Integer, nullable=False, default=10000)
    days11_29_pkg = Column(Integer, nullable=False, default=100000)
    days11_29_day = Column(Integer, nullable=False, default=3000)
    month = Column(Integer, nullable=False, default=160000)
    fraction_pkg = Column(Integer, nullable=False, default=160000)
    fraction_day = Column(Integer, nullable=False, default=5000)
