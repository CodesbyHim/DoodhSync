from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database.base import Base
from app.services.milk_service import MilkService


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")

    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    Base.metadata.drop_all(engine)


def test_record_milk_creates_user_and_record(session):
    service = MilkService(session)

    result = service.record_milk(
        telegram_id=123456789,
        name="Test User",
        record_date=date(2026, 8, 13),
        quantity_liters=Decimal("3.25"),
    )

    assert result.success is True
    assert result.created is True
    assert result.duplicate is False
    assert result.record_id is not None


def test_record_milk_rejects_non_positive_quantity(session):
    service = MilkService(session)

    result = service.record_milk(
        telegram_id=123456789,
        name="Test User",
        record_date=date(2026, 8, 13),
        quantity_liters=Decimal("0"),
    )

    assert result.success is False
    assert result.created is False
    assert result.duplicate is False


def test_record_milk_detects_duplicate_date(session):
    service = MilkService(session)

    first_result = service.record_milk(
        telegram_id=123456789,
        name="Test User",
        record_date=date(2026, 8, 13),
        quantity_liters=Decimal("3.25"),
    )

    second_result = service.record_milk(
        telegram_id=123456789,
        name="Test User",
        record_date=date(2026, 8, 13),
        quantity_liters=Decimal("4.10"),
    )

    assert first_result.success is True
    assert second_result.success is False
    assert second_result.duplicate is True


def test_different_dates_are_allowed(session):
    service = MilkService(session)

    first_result = service.record_milk(
        telegram_id=123456789,
        name="Test User",
        record_date=date(2026, 8, 12),
        quantity_liters=Decimal("3.25"),
    )

    second_result = service.record_milk(
        telegram_id=123456789,
        name="Test User",
        record_date=date(2026, 8, 13),
        quantity_liters=Decimal("4.10"),
    )

    assert first_result.success is True
    assert second_result.success is True