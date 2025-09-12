
from app.domain.exceptions import AuthenticationError
from app.domain.models import User
from app.usecases.security import hash_password, verify_password, create_access_token
from app.ports.head_repository import Repository

class AuthService:
    def __init__(self, repository: Repository):  # Added file storage dependency
        self.repository = repository

    def create_user(self, login, password, email) -> User:
        password_hashed = hash_password(password)
        return self.repository.create_user(login, password_hashed, email)

    def login(self, username, password ):
        user = self.repository.get_user(username)
        if not user or not verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid email or password")

        token = create_access_token(user.id)
        return token

    