from sqlalchemy import Column , Integer , String , Enum , ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from uuid import uuid4

from app.core.database import Base
from .enums import UserRole, UserGrade

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    username = Column(String  , index=True , nullable = False)
    lastname = Column(String,  index=True, nullable = False)
    email = Column(String , unique =True , nullable = False)
    hashed_password = Column(String , nullable = False)
    role = Column(Enum(UserRole),  default = UserRole.chercheur)
    grade = Column(Enum(UserGrade),  default = UserGrade.doctorant_non_salarie)
    anciente = Column(Integer , default = 0)
    laboratory_id = Column(UUID(as_uuid=True) , ForeignKey("laboratories.id"), nullable=False)
    
    laboratory = relationship("Laboratory", back_populates="users")
    notifications = relationship("Notification", back_populates="user")
    applications = relationship("Application",back_populates="user",foreign_keys="[Application.user_id]",cascade="all, delete-orphan")
    
