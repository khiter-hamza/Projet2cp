from sqlalchemy import Column , Integer , String , Enum , ForeignKey
from sqlalchemy.orm import relationship


from app.core.database import Base
from .enums import UserRole , UserGrade

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String  , index=True , nullable = False)
    lastname = Column(String,  index=True, nullable = False)
    email = Column(String , unique =True , nullable = False)
    hashed_password = Column(String , nullable = False)
    role = Column(Enum(UserRole),  default = UserRole.chercheur)
    grade = Column(Enum(UserGrade),  default = UserGrade.doctorant_non_salarie)
    anciente = Column(Integer , default = 0)
    laboratory_id = Column(Integer , ForeignKey("laboratories.id"))
    
    laboratory = relationship("Laboratory", back_populates="users")
    
