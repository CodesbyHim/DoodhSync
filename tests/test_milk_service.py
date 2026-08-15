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


def test_get_milk_for_date_returns_record(session):
    service = MilkService(session)

    service.record_milk(
        telegram_id=123456789,
        name="Test User",
        record_date=date(2026, 8, 13),
        quantity_liters=Decimal("3.25"),
    )

    result = service.get_milk_for_date(
        telegram_id=123456789,
        record_date=date(2026, 8, 13),
    )

    assert result.found is True
    assert result.record_id is not None
    assert result.quantity_liters == Decimal("3.25")
    assert result.record_date == date(2026, 8, 13)


def test_get_milk_for_date_returns_not_found(session):
    service = MilkService(session)

    result = service.get_milk_for_date(
        telegram_id=123456789,
        record_date=date(2026, 8, 13),
    )

    assert result.found is False
    assert result.record_id is None
    assert result.quantity_liters is None
    assert result.record_date is None


def test_get_recent_milk_returns_records_newest_first(session):
    service = MilkService(session)

    service.record_milk(
        telegram_id=123456789,
        name="Test User",
        record_date=date(2026, 8, 11),
        quantity_liters=Decimal("3.25"),
    )

    service.record_milk(
        telegram_id=123456789,
        name="Test User",
        record_date=date(2026, 8, 13),
        quantity_liters=Decimal("4.10"),
    )

    service.record_milk(
        telegram_id=123456789,
        name="Test User",
        record_date=date(2026, 8, 12),
        quantity_liters=Decimal("3.75"),
    )

    result = service.get_recent_milk(
        telegram_id=123456789,
        limit=7,
    )

    assert result.found is True
    assert len(result.records) == 3

    assert result.records[0].date == date(2026, 8, 13)
    assert result.records[0].quantity_liters == Decimal("4.10")

    assert result.records[1].date == date(2026, 8, 12)
    assert result.records[2].date == date(2026, 8, 11)


def test_get_recent_milk_returns_not_found_for_unknown_user(session):
    service = MilkService(session)

    result = service.get_recent_milk(
        telegram_id=999999999,
        limit=7,
    )

    assert result.found is False
    assert result.records == []


def test_get_monthly_report_calculates_summary(session):
    service = MilkService(session)

    service.record_milk(
        telegram_id=123456789,
        name="Test User",
        record_date=date(2026, 8, 1),
        quantity_liters=Decimal("3.00"),
    )

    service.record_milk(
        telegram_id=123456789,
        name="Test User",
        record_date=date(2026, 8, 10),
        quantity_liters=Decimal("4.00"),
    )

    service.record_milk(
        telegram_id=123456789,
        name="Test User",
        record_date=date(2026, 8, 20),
        quantity_liters=Decimal("5.00"),
    )

    result = service.get_monthly_report(
        telegram_id=123456789,
        year=2026,
        month=8,
    )

    assert result.found is True
    assert result.year == 2026
    assert result.month == 8
    assert result.days_recorded == 3
    assert result.total_liters == Decimal("12.00")
    assert result.average_liters == Decimal("4.00")
    assert result.highest_liters == Decimal("5.00")
    assert result.lowest_liters == Decimal("3.00")


def test_get_monthly_report_ignores_other_months(session):
    service = MilkService(session)

    service.record_milk(
        telegram_id=123456789,
        name="Test User",
        record_date=date(2026, 7, 31),
        quantity_liters=Decimal("10.00"),
    )

    service.record_milk(
        telegram_id=123456789,
        name="Test User",
        record_date=date(2026, 8, 1),
        quantity_liters=Decimal("3.00"),
    )

    result = service.get_monthly_report(
        telegram_id=123456789,
        year=2026,
        month=8,
    )

    assert result.found is True
    assert result.days_recorded == 1
    assert result.total_liters == Decimal("3.00")


def test_get_monthly_report_returns_not_found_when_empty(session):
    service = MilkService(session)

    result = service.get_monthly_report(
        telegram_id=123456789,
        year=2026,
        month=8,
    )

    assert result.found is False
    assert result.days_recorded == 0
    assert result.total_liters == Decimal("0")


def test_get_report_for_range_calculates_summary(session):
    service = MilkService(session)

    service.record_milk(
        telegram_id=123456789,
        name="Test User",
        record_date=date(2026, 8, 5),
        quantity_liters=Decimal("3.00"),
    )

    service.record_milk(
        telegram_id=123456789,
        name="Test User",
        record_date=date(2026, 8, 10),
        quantity_liters=Decimal("4.00"),
    )

    service.record_milk(
        telegram_id=123456789,
        name="Test User",
        record_date=date(2026, 8, 15),
        quantity_liters=Decimal("5.00"),
    )

    result = service.get_report_for_range(
        telegram_id=123456789,
        start_date=date(2026, 8, 1),
        end_date=date(2026, 8, 15),
    )

    assert result.found is True
    assert result.days_recorded == 3
    assert result.total_liters == Decimal("12.00")
    assert result.average_liters == Decimal("4.00")
    assert result.highest_liters == Decimal("5.00")
    assert result.lowest_liters == Decimal("3.00")


def test_get_report_for_range_excludes_records_outside_range(session):
    service = MilkService(session)

    service.record_milk(
        telegram_id=123456789,
        name="Test User",
        record_date=date(2026, 7, 31),
        quantity_liters=Decimal("10.00"),
    )

    service.record_milk(
        telegram_id=123456789,
        name="Test User",
        record_date=date(2026, 8, 10),
        quantity_liters=Decimal("3.00"),
    )

    service.record_milk(
        telegram_id=123456789,
        name="Test User",
        record_date=date(2026, 8, 21),
        quantity_liters=Decimal("8.00"),
    )

    result = service.get_report_for_range(
        telegram_id=123456789,
        start_date=date(2026, 8, 1),
        end_date=date(2026, 8, 20),
    )

    assert result.found is True
    assert result.days_recorded == 1
    assert result.total_liters == Decimal("3.00")


def test_get_report_for_range_rejects_invalid_range(session):
    service = MilkService(session)

    with pytest.raises(ValueError, match="Start date must not be after end date"):
        service.get_report_for_range(
            telegram_id=123456789,
            start_date=date(2026, 8, 20),
            end_date=date(2026, 8, 1),
        )


def test_get_report_for_range_returns_not_found_when_empty(session):
    service = MilkService(session)

    result = service.get_report_for_range(
        telegram_id=123456789,
        start_date=date(2026, 8, 1),
        end_date=date(2026, 8, 15),
    )

    assert result.found is False
    assert result.days_recorded == 0
    assert result.total_liters == Decimal("0")


def test_users_can_only_see_their_own_records(session):
    service = MilkService(session)

    service.record_milk(
        telegram_id=111111111,
        name="User A",
        record_date=date(2026, 8, 13),
        quantity_liters=Decimal("3.25"),
    )

    service.record_milk(
        telegram_id=222222222,
        name="User B",
        record_date=date(2026, 8, 13),
        quantity_liters=Decimal("7.50"),
    )

    user_a_today = service.get_milk_for_date(
        telegram_id=111111111,
        record_date=date(2026, 8, 13),
    )

    user_b_today = service.get_milk_for_date(
        telegram_id=222222222,
        record_date=date(2026, 8, 13),
    )

    assert user_a_today.found is True
    assert user_a_today.quantity_liters == Decimal("3.25")

    assert user_b_today.found is True
    assert user_b_today.quantity_liters == Decimal("7.50")


def test_users_cannot_see_each_others_history(session):
    service = MilkService(session)

    service.record_milk(
        telegram_id=111111111,
        name="User A",
        record_date=date(2026, 8, 12),
        quantity_liters=Decimal("3.25"),
    )

    service.record_milk(
        telegram_id=111111111,
        name="User A",
        record_date=date(2026, 8, 13),
        quantity_liters=Decimal("3.50"),
    )

    service.record_milk(
        telegram_id=222222222,
        name="User B",
        record_date=date(2026, 8, 13),
        quantity_liters=Decimal("7.50"),
    )

    result = service.get_recent_milk(
        telegram_id=111111111,
        limit=7,
    )

    assert result.found is True
    assert len(result.records) == 2

    quantities = {
        record.quantity_liters
        for record in result.records
    }

    assert quantities == {
        Decimal("3.25"),
        Decimal("3.50"),
    }


def test_users_cannot_see_each_others_monthly_report(session):
    service = MilkService(session)

    service.record_milk(
        telegram_id=111111111,
        name="User A",
        record_date=date(2026, 8, 10),
        quantity_liters=Decimal("3.00"),
    )

    service.record_milk(
        telegram_id=222222222,
        name="User B",
        record_date=date(2026, 8, 10),
        quantity_liters=Decimal("10.00"),
    )

    result = service.get_monthly_report(
        telegram_id=111111111,
        year=2026,
        month=8,
    )

    assert result.found is True
    assert result.days_recorded == 1
    assert result.total_liters == Decimal("3.00")
    assert result.highest_liters == Decimal("3.00")
    assert result.lowest_liters == Decimal("3.00")


def test_users_cannot_see_each_others_range_report(session):
    service = MilkService(session)

    service.record_milk(
        telegram_id=111111111,
        name="User A",
        record_date=date(2026, 8, 10),
        quantity_liters=Decimal("3.00"),
    )

    service.record_milk(
        telegram_id=222222222,
        name="User B",
        record_date=date(2026, 8, 11),
        quantity_liters=Decimal("10.00"),
    )

    result = service.get_report_for_range(
        telegram_id=111111111,
        start_date=date(2026, 8, 1),
        end_date=date(2026, 8, 31),
    )

    assert result.found is True
    assert result.days_recorded == 1
    assert result.total_liters == Decimal("3.00")


def test_ensure_user_creates_new_user(session):
    service = MilkService(session)

    user = service.ensure_user(
        telegram_id=123456789,
        name="Test User",
    )

    assert user.id is not None
    assert user.telegram_id == 123456789
    assert user.name == "Test User"


def test_ensure_user_does_not_create_duplicate_user(session):
    service = MilkService(session)

    first_user = service.ensure_user(
        telegram_id=123456789,
        name="Test User",
    )

    second_user = service.ensure_user(
        telegram_id=123456789,
        name="Test User",
    )

    assert first_user.id == second_user.id