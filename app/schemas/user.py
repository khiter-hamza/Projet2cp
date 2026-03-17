from pydantic import BaseModel
from uuid import UUID
from app.models.enums import UserRole, UserGrade



class CreateUser(BaseModel):
    username : str
    lastname : str
    email : str
    password : str
    role : UserRole
    grade : UserGrade
    ancientee : int
    laboratory_name : str
    


class UserResponse(BaseModel):
    id : UUID
    username : str
    lastname : str
    email : str

    model_config = {"from_attributes": True}
    
    
class UserLogin(BaseModel) :
    email :str
    password : str