from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_telegram_id(self, telegram_id: int) -> User | None:
        statement = select(User).where(User.telegram_id == telegram_id)
        return self.session.scalar(statement)

    def create(
        self,
        telegram_id: int,
        name: str | None = None,
    ) -> User:
        user = User(
            telegram_id=telegram_id,
            name=name,
        )

        self.session.add(user)
        self.session.flush()

        return user