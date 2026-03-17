from uuid import uuid4
from sqlalchemy import Column, Integer , String , ForeignKey , Enum , Date 
from app.core.database import Base
from .enums import *
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID





class Idemnity(Base):
    __tablename__ = "idemnities"
    id  = Column(UUID(as_uuid=True) ,primary_key=True , default=uuid4  ,index=True )
    date  = Column(Date , nullable=False)
    zone_id = Column(UUID ,ForeignKey("zones.id"))
    budjet = Column(Integer)
    app_id = Column(UUID , ForeignKey("applications.id"))
    
    application = relationship("Application", back_populates="idemnities")
    zone = relationship("Zone", back_populates="idemnities")
 
  