from fastapi import HTTPException, status
from typing import Annotated
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
import jwt

from app.core.settings import pwd_context, ALGORITHM, SECRET_KEY
from app.schemas.user_models_schemas import UserSchema, UserSchemaInDB
from app.models.user_models import User

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserSchemaInDB(**user_dict)


def authenticate_user(db: Session, form_data: dict) -> User | bool:
    user = db.query(User).filter(
        User.username == form_data.username).first()
    if not user:
        return False
    if not verify_password(form_data.password, user.password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def token_validation(token):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("id")
        if not user_id:
            raise credentials_exception
    except:
        raise credentials_exception
    return user_id
