from uuid import uuid4
from sqlalchemy import Column, Integer , String , ForeignKey , Enum
from app.core.database import Base
from .enums import *
from sqlalchemy.orm import relationship





class Idemnity(Base):
