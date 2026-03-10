from passlib.context import CryptContext 
from jose import jwt ,JWTError
from fastapi import HTTPException


pwd_context = CryptContext(schemes=["bcrypt"],deprecated="auto")


def hash_password(password : str) -> str :
    return pwd_context.hash(password)

def verify_password(plain_password , hashpassword) -> bool :
    return pwd_context.verify(plain_password , hashpassword) 


SECRET_KEY="hamza"


def create_token(user_id) -> str :
    return jwt.encode({"user_id": str(user_id)} , key=SECRET_KEY)


def decode_token(token : str) :
    try:
        result = jwt.decode(token=token, key=SECRET_KEY, algorithms=["HS256"])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return result

