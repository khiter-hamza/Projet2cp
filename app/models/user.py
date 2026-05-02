from sqlalchemy import Column , Integer , String , Enum , ForeignKey , Boolean, DateTime
from sqlalchemy.sql import func
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
    # keep the column name that exists in the DB ('anciente')
    anciente = Column(Integer , default = 0)
    is_active = Column(Boolean , default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    phone_number = Column(String, nullable=True)
    laboratory_id = Column(UUID(as_uuid=True) , ForeignKey("laboratories.id"), nullable=True)
    
    laboratory = relationship("Laboratory", back_populates="users")
    notifications = relationship("Notification", back_populates="user")
    applications = relationship("Application",back_populates="user",foreign_keys="[Application.user_id]",cascade="all, delete-orphan")
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")
    
