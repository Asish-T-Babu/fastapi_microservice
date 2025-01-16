from fastapi import APIRouter, HTTPException, status, Depends, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Annotated
from datetime import timedelta

from app.database import get_db
from app.utils import hash_password, authenticate_user, create_access_token, token_validation
from app.models.user_models import User
from app.schemas.user_models_schemas import UserCreate, UserSchema
from app.core.settings import oauth2_scheme, ACCESS_TOKEN_EXPIRE_DAYS
from app.schemas.utils_shemas import Token

router = APIRouter()

@router.post("/create/")
async def create_user(user: Annotated[UserCreate, Form()], db: Session = Depends(get_db)):
    # Check if the username already exists
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already taken")

    # Hash the password
    hashed_password = hash_password(user.password)

    # Create a new user object
    new_user = User(
        username=user.username,
        password=hashed_password,
        first_name=user.first_name,
        email=user.email
    )

    # Add and commit the new user to the database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"id": new_user.id, "username": new_user.username, "first_name": new_user.first_name}

@router.post("/token")
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)) -> Token:
    print(form_data, type(form_data), 'hello i am asish')
    user = authenticate_user(db, form_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    access_token = create_access_token(
        data={"id": user.id}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

@router.get("/me/", response_model=UserSchema)
def read_users_me(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    user_id = token_validation(token)
    # Check if the username already exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    return UserSchema.from_orm(user)
