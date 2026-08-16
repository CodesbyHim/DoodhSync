import pytest

from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database.base import Base

from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select

from app.models.user import User
from app.services.milk_service import MilkService

from app.telegram.handlers import (
    help_handler,
    milk_quantity_handler,
    range_handler,
    error_handler,
)


@pytest.mark.asyncio
async def test_help_handler():
    message = MagicMock()
    message.reply_text = AsyncMock()

    update = MagicMock()
    update.effective_message = message

    await help_handler(update, MagicMock())

    message.reply_text.assert_awaited_once()
    response = message.reply_text.await_args.args[0]

    assert "DoodhSync Help" in response
    assert "/today" in response
    assert "/range" in response


@pytest.mark.asyncio
async def test_milk_quantity_handler_rejects_invalid_input():
    message = MagicMock()
    message.text = "abc"
    message.reply_text = AsyncMock()

    update = MagicMock()
    update.effective_message = message

    await milk_quantity_handler(update, MagicMock())

    message.reply_text.assert_awaited_once_with(
        "Please send only the milk quantity in liters.\n\n"
        "Example: 3.25"
    )


@pytest.mark.asyncio
async def test_milk_quantity_handler_rejects_zero():
    message = MagicMock()
    message.text = "0"
    message.reply_text = AsyncMock()

    update = MagicMock()
    update.effective_message = message

    await milk_quantity_handler(update, MagicMock())

    message.reply_text.assert_awaited_once_with(
        "Milk quantity must be greater than zero."
    )


@pytest.mark.asyncio
async def test_range_handler_requires_two_dates():
    message = MagicMock()
    message.reply_text = AsyncMock()

    update = MagicMock()
    update.effective_message = message
    update.effective_user = MagicMock()

    context = MagicMock()
    context.args = []

    await range_handler(update, context)

    message.reply_text.assert_awaited_once()

    response = message.reply_text.await_args.args[0]

    assert "Usage:" in response
    assert "/range YYYY-MM-DD YYYY-MM-DD" in response


@pytest.mark.asyncio
async def test_range_handler_rejects_invalid_dates():
    message = MagicMock()
    message.reply_text = AsyncMock()

    update = MagicMock()
    update.effective_message = message
    update.effective_user = MagicMock()

    context = MagicMock()
    context.args = ["hello", "world"]

    await range_handler(update, context)

    message.reply_text.assert_awaited_once()

    response = message.reply_text.await_args.args[0]

    assert "Invalid date format." in response


@pytest.mark.asyncio
async def test_range_handler_rejects_reversed_dates():
    message = MagicMock()
    message.reply_text = AsyncMock()

    update = MagicMock()
    update.effective_message = message
    update.effective_user = MagicMock()

    context = MagicMock()
    context.args = ["2026-08-16", "2026-08-01"]

    await range_handler(update, context)

    message.reply_text.assert_awaited_once_with(
        "Start date must not be after end date."
    )


@pytest.mark.asyncio
async def test_milk_quantity_handler_records_valid_quantity():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        message = MagicMock()
        message.text = "3.25"
        message.reply_text = AsyncMock()

        user = MagicMock()
        user.id = 123456789
        user.full_name = "Test User"

        update = MagicMock()
        update.effective_message = message
        update.effective_user = user

        with patch(
            "app.telegram.handlers.SessionLocal",
            return_value=session,
        ):
            await milk_quantity_handler(update, MagicMock())

        message.reply_text.assert_awaited_once_with(
            "🥛 Recorded 3.25 L for today."
        )

    Base.metadata.drop_all(engine)



@pytest.mark.asyncio
async def test_today_handler_returns_record():
    from app.telegram.handlers import today_handler

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        service = MilkService(session)

        today = date.today()

        service.record_milk(
            telegram_id=123456789,
            name="Test User",
            record_date=today,
            quantity_liters=Decimal("3.25"),
        )

        message = MagicMock()
        message.reply_text = AsyncMock()

        user = MagicMock()
        user.id = 123456789

        update = MagicMock()
        update.effective_message = message
        update.effective_user = user

        with patch("app.telegram.handlers.SessionLocal", return_value=session), \
             patch("app.telegram.handlers.settings.timezone", "UTC"), \
             patch("app.telegram.handlers.datetime") as mock_datetime:

            mock_datetime.now.return_value = datetime.combine(
                today,
                datetime.min.time(),
                tzinfo=ZoneInfo("UTC"),
            )

            await today_handler(update, MagicMock())

        message.reply_text.assert_awaited_once()
        response = message.reply_text.await_args.args[0]

        assert "Today's milk" in response
        assert "3.25 L" in response

    Base.metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_history_handler_returns_history():
    from app.telegram.handlers import history_handler

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        service = MilkService(session)

        service.record_milk(
            telegram_id=1,
            name="User",
            record_date=date(2026, 8, 10),
            quantity_liters=Decimal("3.00"),
        )
        service.record_milk(
            telegram_id=1,
            name="User",
            record_date=date(2026, 8, 11),
            quantity_liters=Decimal("4.00"),
        )

        message = MagicMock()
        message.reply_text = AsyncMock()

        update = MagicMock()
        update.effective_message = message
        update.effective_user = MagicMock(id=1)

        with patch("app.telegram.handlers.SessionLocal", return_value=session):
            await history_handler(update, MagicMock())

        response = message.reply_text.await_args.args[0]

        assert "Milk History" in response
        assert "3.00 L" in response
        assert "4.00 L" in response
        assert "Total: 7.00 L" in response

    Base.metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_month_handler_returns_report():
    from app.telegram.handlers import month_handler

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        service = MilkService(session)

        service.record_milk(
            telegram_id=1,
            name="User",
            record_date=date(2026, 8, 10),
            quantity_liters=Decimal("3.00"),
        )
        service.record_milk(
            telegram_id=1,
            name="User",
            record_date=date(2026, 8, 11),
            quantity_liters=Decimal("5.00"),
        )

        message = MagicMock()
        message.reply_text = AsyncMock()

        update = MagicMock()
        update.effective_message = message
        update.effective_user = MagicMock(id=1)

        with patch("app.telegram.handlers.SessionLocal", return_value=session), \
             patch("app.telegram.handlers.settings.timezone", "UTC"), \
             patch("app.telegram.handlers.datetime") as mock_datetime:

            mock_datetime.now.return_value = datetime.combine(
                date(2026, 8, 20),
                datetime.min.time(),
                tzinfo=ZoneInfo("UTC"),
            )

            await month_handler(update, MagicMock())

        response = message.reply_text.await_args.args[0]

        assert "August 2026" in response
        assert "Total: 8.00 L" in response
        assert "Average: 4.00 L/day" in response

    Base.metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_range_handler_returns_report():
    from app.telegram.handlers import range_handler

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        service = MilkService(session)

        service.record_milk(
            telegram_id=1,
            name="User",
            record_date=date(2026, 8, 10),
            quantity_liters=Decimal("3.00"),
        )
        service.record_milk(
            telegram_id=1,
            name="User",
            record_date=date(2026, 8, 11),
            quantity_liters=Decimal("5.00"),
        )

        message = MagicMock()
        message.reply_text = AsyncMock()

        update = MagicMock()
        update.effective_message = message
        update.effective_user = MagicMock(id=1)

        context = MagicMock()
        context.args = ["2026-08-01", "2026-08-31"]

        with patch("app.telegram.handlers.SessionLocal", return_value=session):
            await range_handler(update, context)

        response = message.reply_text.await_args.args[0]

        assert "Milk Report" in response
        assert "Total: 8.00 L" in response
        assert "Average: 4.00 L/day" in response

    Base.metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_start_handler_creates_user():
    from app.telegram.handlers import start_handler

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        message = MagicMock()
        message.reply_text = AsyncMock()

        user = MagicMock()
        user.id = 123456789
        user.full_name = "Test User"

        update = MagicMock()
        update.effective_message = message
        update.effective_user = user

        with patch("app.telegram.handlers.SessionLocal", return_value=session):
            await start_handler(update, MagicMock())

        created_user = session.scalar(
            select(User).where(User.telegram_id == 123456789)
        )

        assert created_user is not None
        assert created_user.name == "Test User"

        response = message.reply_text.await_args.args[0]
        assert "Welcome to DoodhSync!" in response

    Base.metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_error_handler_logs_exception_and_notifies_user(caplog):
    import logging

    message = MagicMock()
    message.reply_text = AsyncMock()

    update = MagicMock()
    update.effective_message = message

    context = MagicMock()
    context.error = RuntimeError("Test error")

    with caplog.at_level(logging.ERROR):
        await error_handler(update, context)

    assert "Exception while processing Telegram update" in caplog.text

    message.reply_text.assert_awaited_once_with(
        "Sorry, something went wrong. Please try again."
    )