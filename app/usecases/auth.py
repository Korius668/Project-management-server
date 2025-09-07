import jwt
from datetime import datetime, timedelta

from app.ports.repositories import UsersRepository
from app.domain.models import User
from app.domain.exceptions import AuthenticationError
from app.usecases.security import hash_password, verify_password
from app.config import secrets


class UsersService:

    def __init__(self, repository: UsersRepository):
        self._repository = repository

    def create_user(self, _login, _password, _email):
        password_hashed = hash_password(_password)
        user = User(name=_login, email=_email, password_hash=password_hashed)
        self._repository.add(user)
        return user

    def login(
        self,
        _login,
        _password,
    ):
        user = self._repository.get_by_name(_login)
        if not user or not verify_password(_password, user.password_hash):
            raise AuthenticationError("Invalid email or password")

        token = create_access_token(
            data={"sub": str(user.id)}, expires_delta=timedelta(hours=1)
        )
        return token


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now() + (
        expires_delta or timedelta(minutes=secrets.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secrets.secret_key, algorithm=secrets.algorithm)
    return encoded_jwt
