from datetime import date
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.milk_record import MilkRecord


class MilkRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_user_and_date(
        self,
        user_id: int,
        record_date: date,
    ) -> MilkRecord | None:
        statement = select(MilkRecord).where(
            MilkRecord.user_id == user_id,
            MilkRecord.date == record_date,
        )

        return self.session.scalar(statement)

    def get_recent_by_user(
        self,
        user_id: int,
        limit: int = 7,
    ) -> list[MilkRecord]:
        statement = (
            select(MilkRecord)
            .where(MilkRecord.user_id == user_id)
            .order_by(MilkRecord.date.desc())
            .limit(limit)
        )

        return list(self.session.scalars(statement).all())

    def create(
        self,
        user_id: int,
        record_date: date,
        quantity_liters: Decimal,
    ) -> MilkRecord:
        record = MilkRecord(
            user_id=user_id,
            date=record_date,
            quantity_liters=quantity_liters,
        )

        self.session.add(record)
        self.session.flush()

        return record

    def update_quantity(
        self,
        record: MilkRecord,
        quantity_liters: Decimal,
    ) -> MilkRecord:
        record.quantity_liters = quantity_liters
        self.session.flush()

        return record

    def delete(self, record: MilkRecord) -> None:
        self.session.delete(record)
        self.session.flush()