from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.repositories.milk_repository import MilkRepository
from app.repositories.user_repository import UserRepository


@dataclass
class RecordMilkResult:
    success: bool
    created: bool
    duplicate: bool
    record_id: int | None = None
    message: str = ""


class MilkService:
    def __init__(self, session: Session):
        self.session = session
        self.user_repository = UserRepository(session)
        self.milk_repository = MilkRepository(session)

    def record_milk(
        self,
        telegram_id: int,
        name: str | None,
        record_date: date,
        quantity_liters: Decimal,
    ) -> RecordMilkResult:
        if quantity_liters <= Decimal("0"):
            return RecordMilkResult(
                success=False,
                created=False,
                duplicate=False,
                message="Milk quantity must be greater than zero.",
            )

        user = self.user_repository.get_by_telegram_id(telegram_id)

        if user is None:
            user = self.user_repository.create(
                telegram_id=telegram_id,
                name=name,
            )

        existing_record = self.milk_repository.get_by_user_and_date(
            user_id=user.id,
            record_date=record_date,
        )

        if existing_record is not None:
            return RecordMilkResult(
                success=False,
                created=False,
                duplicate=True,
                record_id=existing_record.id,
                message=(
                    "A milk record already exists for this date."
                ),
            )

        try:
            record = self.milk_repository.create(
                user_id=user.id,
                record_date=record_date,
                quantity_liters=quantity_liters,
            )

            self.session.commit()

            return RecordMilkResult(
                success=True,
                created=True,
                duplicate=False,
                record_id=record.id,
                message="Milk record created successfully.",
            )

        except IntegrityError:
            self.session.rollback()

            return RecordMilkResult(
                success=False,
                created=False,
                duplicate=True,
                message=(
                    "A milk record already exists for this date."
                ),
            )