from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.usecases.security import get_user_id_from_token
from app.infrastructure.db.db import get_session
from app.infrastructure.container import get_container
from app.domain.models import User

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session),
) -> User:
    """Extract current user from JWT token"""
    token = credentials.credentials
    user_id = get_user_id_from_token(token)

    container = get_container(session)
    users_service = container.users_service()

    user = users_service._repository.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    return user
