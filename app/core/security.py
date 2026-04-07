from passlib.context import CryptContext 
from jose import jwt ,JWTError
from fastapi import HTTPException
from datetime import datetime, timedelta


pwd_context = CryptContext(schemes=["bcrypt"],deprecated="auto")


def hash_password(password : str) -> str :
    return pwd_context.hash(password)

def verify_password(plain_password , hashpassword) -> bool :
    return pwd_context.verify(plain_password , hashpassword) 


SECRET_KEY="hamza"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 
ALGORITHM = "HS256"


def create_token(data: dict) -> str:
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token : str) :
    try:
        result = jwt.decode(token=token, key=SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return result

