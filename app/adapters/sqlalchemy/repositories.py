from typing import List, Optional
from sqlalchemy.orm import Session
from app.ports.repositories import UsersRepository
from app.domain.models import User
from app.adapters.sqlalchemy.models import UserORM


class SqlAlchemyUsersRepository(UsersRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, user: User) -> User:
        orm_obj = UserORM(
            id=str(user.id),
            email=user.email,
            name=user.name,
            password_hash=user.password_hash,
        )
        self.session.add(orm_obj)
        self.session.commit()
        return user

    def get(self, user_id) -> Optional[User]:
        orm_obj = self.session.get(UserORM, str(user_id))
        return self._to_domain(orm_obj)

    def list(self) -> List[User]:
        return [self._to_domain(u) for u in self.session.query(UserORM).all()]

    @staticmethod
    def _to_domain(orm_obj: Optional[UserORM]) -> Optional[User]:
        if orm_obj is None:
            return None
        return User.model_validate(orm_obj, from_attributes=True)
