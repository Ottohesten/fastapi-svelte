from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import uvicorn
from typing import Optional, Union, Annotated
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Field, SQLModel, create_engine, Session, select
from contextlib import contextmanager, asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Request, Security

from app.deps import SessionDep, TokenDep, create_db_and_tables
from app.config import get_settings
from app.routers import (
    users,
    login,
    recipes,
    ingredients,
    game,
    roles,
    user_permissions
)

# @asynccontextmanager
# async def lifespan(app: FastAPI):





# app = FastAPI(dependencies=[Depends(oauth2_scheme)])
# app = FastAPI(swagger_ui_parameters={"persistAuthorization": True})
app = FastAPI()

origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    # Add more origins here
    "*",
    "0.0.0.0:8000",
    "0.0.0.0:10000",
    "https://fastapi-svelte-frontend.onrender.com",
    "fastapi-svelte:8000",
    "fastapi-svelte:10000",
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

# print(settings.SQLALCHEMY_DATABASE_URI)

app.include_router(users.router)
app.include_router(recipes.router)
app.include_router(ingredients.router)
app.include_router(game.router)
app.include_router(login.router)
app.include_router(roles.router)
app.include_router(user_permissions.router)



# security = HTTPBearer(
#     scheme_name="Authorization",
#     description="Bearer token for authorization",
#     auto_error=True
# )

# Use it in your endpoints





@app.get("/")
async def read_root(token: TokenDep):
    return {"token": token}





# @app.get("/protected-route")
# async def protected_route(credentials: HTTPAuthorizationCredentials = Security(security)):
#     return {"message": "You accessed a protected route"}





