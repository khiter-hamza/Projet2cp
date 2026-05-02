from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from app.models.enums import UserRole, UserGrade



class CreateUser(BaseModel):
    username : str
    lastname : str
    email : str
    password : str
    role : UserRole
    grade : UserGrade
    is_active : bool = True
    anciente : int
    laboratory_name : str
    phone_number : str | None = None
    
class UpdateUser(BaseModel):
    username : str | None = None
    lastname : str | None = None
    email : str | None = None
    password : str | None = None
    role : UserRole | None = None
    grade : UserGrade | None = None
    is_active : bool | None = None
    anciente : int | None = None
    laboratory_name : str | None = None
    phone_number : str | None = None

class LaboratoryMinimal(BaseModel):
    id: UUID
    name: str

    model_config = {"from_attributes": True}

class UserResponse(BaseModel):
    id : UUID
    username : str
    lastname : str
    email : str
    role: UserRole
    grade: UserGrade | None = None
    is_active: bool
    created_at: datetime
    phone_number: str | None = None
    laboratory: LaboratoryMinimal | None = None

    model_config = {"from_attributes": True}


class CurrentUserResponse(BaseModel):
    id: UUID
    username: str
    lastname: str
    email: str
    role: UserRole
    grade: UserGrade | None = None
    anciente: int | None = None
    is_active: bool

    model_config = {"from_attributes": True}
    
    
class UserLogin(BaseModel) :
    email :str
    password : str


class forget_User(BaseModel):
    email: str


class reset_Password(BaseModel):
    new_password: str