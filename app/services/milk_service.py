from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.repositories.milk_repository import MilkRepository
from app.repositories.user_repository import UserRepository

from app.models.milk_record import MilkRecord

@dataclass
class RecordMilkResult:
    success: bool
    created: bool
    duplicate: bool
    record_id: int | None = None
    message: str = ""


@dataclass
class GetMilkResult:
    found: bool
    record_id: int | None = None
    quantity_liters: Decimal | None = None
    record_date: date | None = None

@dataclass
class GetRecentMilkResult:
    found: bool
    records: list[MilkRecord]


@dataclass
class MonthlyMilkReport:
    found: bool
    year: int
    month: int
    days_recorded: int = 0
    total_liters: Decimal = Decimal("0")
    average_liters: Decimal = Decimal("0")
    highest_liters: Decimal = Decimal("0")
    lowest_liters: Decimal = Decimal("0")


@dataclass
class MilkReport:
    found: bool
    start_date: date
    end_date: date
    days_recorded: int = 0
    total_liters: Decimal = Decimal("0")
    average_liters: Decimal = Decimal("0")
    highest_liters: Decimal = Decimal("0")
    lowest_liters: Decimal = Decimal("0")

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

    def get_milk_for_date(
        self,
        telegram_id: int,
        record_date: date,
    ) -> GetMilkResult:
        user = self.user_repository.get_by_telegram_id(telegram_id)

        if user is None:
            return GetMilkResult(found=False)

        record = self.milk_repository.get_by_user_and_date(
            user_id=user.id,
            record_date=record_date,
        )

        if record is None:
            return GetMilkResult(found=False)

        return GetMilkResult(
            found=True,
            record_id=record.id,
            quantity_liters=record.quantity_liters,
            record_date=record.date,
        )

    def get_recent_milk(
        self,
        telegram_id: int,
        limit: int = 7,
    ) -> GetRecentMilkResult:
        user = self.user_repository.get_by_telegram_id(telegram_id)

        if user is None:
            return GetRecentMilkResult(
                found=False,
                records=[],
            )

        records = self.milk_repository.get_recent_by_user(
            user_id=user.id,
            limit=limit,
        )

        return GetRecentMilkResult(
            found=bool(records),
            records=records,
        )

    def get_monthly_report(
        self,
        telegram_id: int,
        year: int,
        month: int,
    ) -> MonthlyMilkReport:
        start_date = date(year, month, 1)

        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)

        end_date = end_date - timedelta(days=1)

        report = self.get_report_for_range(
            telegram_id=telegram_id,
            start_date=start_date,
            end_date=end_date,
        )

        return MonthlyMilkReport(
            found=report.found,
            year=year,
            month=month,
            days_recorded=report.days_recorded,
            total_liters=report.total_liters,
            average_liters=report.average_liters,
            highest_liters=report.highest_liters,
            lowest_liters=report.lowest_liters,
        )


    def get_report_for_range(
        self,
        telegram_id: int,
        start_date: date,
        end_date: date,
    ) -> MilkReport:
        if start_date > end_date:
            raise ValueError("Start date must not be after end date.")

        user = self.user_repository.get_by_telegram_id(telegram_id)

        if user is None:
            return MilkReport(
                found=False,
                start_date=start_date,
                end_date=end_date,
            )

        records = self.milk_repository.get_by_user_and_date_range(
            user_id=user.id,
            start_date=start_date,
            end_date=end_date,
        )

        if not records:
            return MilkReport(
                found=False,
                start_date=start_date,
                end_date=end_date,
            )

        quantities = [record.quantity_liters for record in records]

        total_liters = sum(quantities, Decimal("0"))
        days_recorded = len(records)

        return MilkReport(
            found=True,
            start_date=start_date,
            end_date=end_date,
            days_recorded=days_recorded,
            total_liters=total_liters,
            average_liters=total_liters / Decimal(days_recorded),
            highest_liters=max(quantities),
            lowest_liters=min(quantities),
        )

    def ensure_user(
        self,
        telegram_id: int,
        name: str | None,
    ):
        user = self.user_repository.get_by_telegram_id(telegram_id)

        if user is not None:
            return user

        user = self.user_repository.create(
            telegram_id=telegram_id,
            name=name,
        )

        self.session.commit()

        return user