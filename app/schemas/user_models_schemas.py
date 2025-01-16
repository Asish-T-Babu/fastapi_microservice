from pydantic import BaseModel, Field, EmailStr

class UserSchema(BaseModel):
    id: str
    username: str
    email: EmailStr | None = None
    first_name: str | None = None
    last_name: str | None = None
    
    class Config:
        from_attributes = True 


class UserSchemaInDB(UserSchema):
    password: str


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., max_length=100)
    email: EmailStr