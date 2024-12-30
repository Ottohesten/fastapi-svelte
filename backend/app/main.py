import uvicorn
from typing import Optional, Union, Annotated
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Field, SQLModel, create_engine, Session, select
from contextlib import contextmanager, asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException

from app.models import Hero, HeroCreate, HeroPublic, HeroUpdate
from app.deps import SessionDep, TokenDep, create_db_and_tables
from app.config import get_settings
from app.routers import (
    heroes,
    users,
    login
)

# @asynccontextmanager
# async def lifespan(app: FastAPI):





# app = FastAPI(dependencies=[Depends(oauth2_scheme)])
app = FastAPI(swagger_ui_parameters={"persistAuthorization": True})

origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    # Add more origins here
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




# hero_1 = Hero(name="Deadpond", secret_name="Dive Wilson")
# hero_2 = Hero(name="Spider-Boy", secret_name="Pedro Parqueador")
# hero_3 = Hero(name="Rusty-Man", secret_name="Tommy Sharp", age=48)


settings = get_settings()

print(settings.SQLALCHEMY_DATABASE_URI)


app.include_router(heroes.router)
app.include_router(users.router)
app.include_router(login.router)



@app.get("/")
async def read_root(token: TokenDep):
    return {"token": token}








