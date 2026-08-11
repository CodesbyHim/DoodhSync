from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.base import Base
from app.models.milk_record import MilkRecord
from app.models.user import User
from app.repositories.milk_repository import MilkRepository
from app.repositories.user_repository import UserRepository


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")

    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    Base.metadata.drop_all(engine)


def test_create_and_find_user(session):
    repository = UserRepository(session)

    user = repository.create(
        telegram_id=123456789,
        name="Test User",
    )

    found_user = repository.get_by_telegram_id(123456789)

    assert found_user is not None
    assert found_user.id == user.id
    assert found_user.telegram_id == 123456789
    assert found_user.name == "Test User"


def test_find_unknown_user_returns_none(session):
    repository = UserRepository(session)

    result = repository.get_by_telegram_id(999999999)

    assert result is None


def test_create_and_find_milk_record(session):
    user_repository = UserRepository(session)
    milk_repository = MilkRepository(session)

    user = user_repository.create(
        telegram_id=123456789,
        name="Test User",
    )

    record = milk_repository.create(
        user_id=user.id,
        record_date=date(2026, 8, 11),
        quantity_liters=Decimal("3.25"),
    )

    found_record = milk_repository.get_by_user_and_date(
        user_id=user.id,
        record_date=date(2026, 8, 11),
    )

    assert found_record is not None
    assert found_record.id == record.id
    assert found_record.quantity_liters == Decimal("3.25")


def test_update_milk_quantity(session):
    user_repository = UserRepository(session)
    milk_repository = MilkRepository(session)

    user = user_repository.create(
        telegram_id=123456789,
        name="Test User",
    )

    record = milk_repository.create(
        user_id=user.id,
        record_date=date(2026, 8, 11),
        quantity_liters=Decimal("3.25"),
    )

    updated_record = milk_repository.update_quantity(
        record,
        Decimal("3.50"),
    )

    assert updated_record.quantity_liters == Decimal("3.50")


def test_delete_milk_record(session):
    user_repository = UserRepository(session)
    milk_repository = MilkRepository(session)

    user = user_repository.create(
        telegram_id=123456789,
        name="Test User",
    )

    record = milk_repository.create(
        user_id=user.id,
        record_date=date(2026, 8, 11),
        quantity_liters=Decimal("3.25"),
    )

    milk_repository.delete(record)

    found_record = milk_repository.get_by_user_and_date(
        user_id=user.id,
        record_date=date(2026, 8, 11),
    )

    assert found_record is None


def test_duplicate_user_date_is_rejected(session):
    user_repository = UserRepository(session)
    milk_repository = MilkRepository(session)

    user = user_repository.create(
        telegram_id=123456789,
        name="Test User",
    )

    milk_repository.create(
        user_id=user.id,
        record_date=date(2026, 8, 11),
        quantity_liters=Decimal("3.25"),
    )

    with pytest.raises(IntegrityError):
        milk_repository.create(
            user_id=user.id,
            record_date=date(2026, 8, 11),
            quantity_liters=Decimal("3.50"),
        )