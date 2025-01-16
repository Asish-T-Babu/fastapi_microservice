from typing import Annotated
import uvicorn
import jwt
from fastapi import Depends, FastAPI, HTTPException, Query, status, Form
from sqlmodel import Field, Session, SQLModel, create_engine, select
from jwt.exceptions import InvalidTokenError
from pydantic import BaseModel, EmailStr
from typing import List, Dict, Any
from pydantic import BaseModel

from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
import requests


SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=" http://0.0.0.0:8001/user/token")


class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    name: str = Field(index=True)
    age: int | None = Field(default=None, index=True)
    secret_name: str

class HeroModel(BaseModel):
    user_id: str | None = None
    name: str
    age: int
    secret_name: str

# Response Model
class HeroResponse(BaseModel):
    id: int
    name: str
    age: int | None
    secret_name: str

    class Config:
        from_attributes = True 


class UserSchema(BaseModel):
    id: str
    username: str
    email: EmailStr | None = None
    first_name: str | None = None
    last_name: str | None = None
    heroes: List[HeroResponse]   


sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]

app = FastAPI(debug=True)

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

@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.post("/heroes/")
def create_hero(hero: Annotated[HeroModel, Form()], session: SessionDep, token: Annotated[str, Depends(oauth2_scheme)]):

    user_id = token_validation(token) 
    
    hero.user_id = user_id
    hero = Hero(**hero.__dict__)
    session.add(hero)
    session.commit()
    session.refresh(hero)
    return hero


# Endpoint to get all heroes by user_id
@app.get("/heroes/", response_model=UserSchema)
def get_heroes_by_user_id(session: SessionDep, token: Annotated[str, Depends(oauth2_scheme)]):

    user_id = token_validation(token)
    # Query the database
    statement = select(Hero).where(Hero.user_id == user_id)
    heroes = session.exec(statement).all()
    
    # Check if any heroes were found
    if not heroes:
        raise HTTPException(status_code=404, detail="No heroes found for this user_id")
    
    url = "http://127.0.0.1:8001/user/me/"
    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        # Print or process the response JSON data
        response = response.json()
    else:
        raise HTTPException(status_code=404, detail="User not found")
    response['heroes'] = heroes
    return UserSchema(**response)

@app.get("/heroes2/")
def read_heroes(
    session: SessionDep,

    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[HeroResponse]:
    heroes = session.exec(select(Hero).offset(offset).limit(limit)).all()
    return heroes


@app.get("/heroes/{hero_id}")
def read_hero(hero_id: int, session: SessionDep) -> Hero:
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    return hero


@app.delete("/heroes/{hero_id}")
def delete_hero(hero_id: int, session: SessionDep):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    session.delete(hero)
    session.commit()
    return {"ok": True}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)