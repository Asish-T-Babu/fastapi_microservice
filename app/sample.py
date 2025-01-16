from typing import Annotated

from fastapi import FastAPI, Form
from pydantic import BaseModel

app = FastAPI()


class FormData(BaseModel):
    username: str
    password: str


@app.post("/login/")
async def login(data: Annotated[FormData, Form()]):
    return data

import uvicorn
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)