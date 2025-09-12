from fastapi import APIRouter, status, Depends
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from app.usecases.security import create_access_token
from app.usecases.auth import AuthService
from app.infrastructure.db.db import get_session
from app.adapters.repositories.sqlalchemy.head_repository import SqlAlchemyRepository

auth = APIRouter(prefix="/auth", tags=["auth"])


def get_users_service(session: Session = Depends(get_session)) -> AuthService:
    return AuthService(SqlAlchemyRepository(session))


@auth.post("/create_user", status_code=status.HTTP_201_CREATED)
def create_user(
    username: str,
    password: str,
    email: str,
    service: AuthService = Depends(get_users_service),
):

    new_user = service.create_user(username, password, email)
    return {"id": str(new_user.id), "email": new_user.email, "name": new_user.name}


@auth.post("/login")
def login(
    username: str, password: str, service: AuthService = Depends(get_users_service)
):
    token = service.login(username, password)

    return {"access_token": token, "token_type": "bearer"}
