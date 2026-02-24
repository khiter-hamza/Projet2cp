from passlib.context import CryptContext 
from jose import jwt 


pwd_context = CryptContext(schemes=["bcrypt"],deprecated="auto")


def hash_password(password : str) -> str :
    return pwd_context.hash(password)

def verify_password(plain_password , hashpassword) -> bool :
    return pwd_context.verify(plain_password , hashpassword) 


SECRET_KEY="hamza"


def create_token(user_id : int ) -> str :
    return jwt.encode({"user_id": user_id} , key=SECRET_KEY)


def decode_token(token : str) :
    return jwt.decode(token=token, key=SECRET_KEY, algorithms=["HS256"])


