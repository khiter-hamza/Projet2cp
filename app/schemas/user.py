from pydantic import BaseModel
import uuid


class CreateUser(BaseModel):
    username : str
    lastname : str
    email : str
    password : str
    


class UserResponse(BaseModel):
    id : uuid.UUID
    username : str
    lastname : str
    email : str

    model_config = {"from_attributes": True}
    
    
class UserLogin(BaseModel) :
    email :str
    password : str