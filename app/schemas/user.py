from pydantic import BaseModel
from uuid import UUID


class CreateUser(BaseModel):
    username : str
    lastname : str
    email : str
    password : str
    


class UserResponse(BaseModel):
    id : UUID
    username : str
    lastname : str
    email : str

    model_config = {"from_attributes": True}
    
    
class UserLogin(BaseModel) :
    email :str
    password : str