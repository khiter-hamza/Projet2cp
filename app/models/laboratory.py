from sqlalchemy import Column , Integer , String ,Enum
from sqlalchemy.orm import relationship

from app.core.database import Base

class Laboratory(Base) :
    __tablename__ = "laboratories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String , index=True , nullable = False)
    users = relationship("User", backref="laboratory")
    
