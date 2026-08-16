import logging

from telegram import Update
from telegram.ext import ContextTypes

from app.config import settings

from datetime import date, datetime
from zoneinfo import ZoneInfo
from decimal import Decimal, InvalidOperation

from app.database.session import SessionLocal
from app.services.milk_service import MilkService


logger = logging.getLogger(__name__)


async def start_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if update.effective_message is None:
        return

    user = update.effective_user

    if user is None:
        return

    session = SessionLocal()

    try:
        service = MilkService(session)

        service.ensure_user(
            telegram_id=user.id,
            name=user.full_name,
        )

        await update.effective_message.reply_text(
            "🥛 Welcome to DoodhSync!\n\n"
            "Your personal milk tracker is ready.\n\n"
            "Send today's milk quantity in liters.\n\n"
            "Example:\n"
            "3.25\n\n"
            "Commands:\n"
            "/today - Today's milk\n"
            "/history - Last 7 days\n"
            "/month - This month's report\n"
            "/range - Custom date range\n"
            "/help - Show help"
        )

    finally:
        session.close()


async def help_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if update.effective_message is not None:
        await update.effective_message.reply_text(
            "🥛 DoodhSync Help\n\n"
            "Send a number to record today's milk quantity.\n\n"
            "Example:\n"
            "3.25\n\n"
            "Commands:\n"
            "/start - Start DoodhSync\n"
            "/today - Show today's milk\n"
            "/history - Show the last 7 days\n"
            "/month - Show this month's report\n"
            "/range - Show a custom date-range report\n"
            "/help - Show this help message\n\n"
            "Example range:\n"
            "/range 2026-08-01 2026-08-15"
        )


async def milk_quantity_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if update.effective_message is None:
        return

    text = update.effective_message.text

    if text is None:
        return

    text = text.strip()

    try:
        quantity = Decimal(text)
    except InvalidOperation:
        await update.effective_message.reply_text(
            "Please send only the milk quantity in liters.\n\n"
            "Example: 3.25"
        )
        return

    if quantity <= Decimal("0"):
        await update.effective_message.reply_text(
            "Milk quantity must be greater than zero."
        )
        return

    user = update.effective_user

    if user is None:
        return

    record_date = datetime.now(
        ZoneInfo(settings.timezone)
    ).date()

    session = SessionLocal()

    try:
        service = MilkService(session)

        result = service.record_milk(
            telegram_id=user.id,
            name=user.full_name,
            record_date=record_date,
            quantity_liters=quantity,
        )

        if result.success:
            await update.effective_message.reply_text(
                f"🥛 Recorded {quantity} L for today."
            )
        elif result.duplicate:
            await update.effective_message.reply_text(
                "A milk record already exists for today."
            )
        else:
            await update.effective_message.reply_text(
                result.message
            )

    finally:
        session.close()


async def today_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if update.effective_message is None:
        return

    user = update.effective_user

    if user is None:
        return

    record_date = datetime.now(
        ZoneInfo(settings.timezone)
    ).date()

    session = SessionLocal()

    try:
        service = MilkService(session)

        result = service.get_milk_for_date(
            telegram_id=user.id,
            record_date=record_date,
        )

        if not result.found:
            await update.effective_message.reply_text(
                "🥛 No milk record found for today."
            )
            return

        await update.effective_message.reply_text(
            f"🥛 Today's milk\n"
            f"📅 {result.record_date.strftime('%d %b %Y')}\n"
            f"📦 Quantity: {result.quantity_liters} L"
        )

    finally:
        session.close()


async def history_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if update.effective_message is None:
        return

    user = update.effective_user

    if user is None:
        return

    session = SessionLocal()

    try:
        service = MilkService(session)

        result = service.get_recent_milk(
            telegram_id=user.id,
            limit=7,
        )

        if not result.found:
            await update.effective_message.reply_text(
                "🥛 No milk records found."
            )
            return

        lines = ["🥛 Milk History", ""]

        total = Decimal("0")

        for record in result.records:
            quantity = record.quantity_liters
            total += quantity

            lines.append(
                f"{record.date.strftime('%d %b')} — {quantity} L"
            )

        lines.extend(
            [
                "",
                f"Total: {total} L",
            ]
        )

        await update.effective_message.reply_text(
            "\n".join(lines)
        )

    finally:
        session.close()


async def month_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if update.effective_message is None:
        return

    user = update.effective_user

    if user is None:
        return

    current_date = datetime.now(
        ZoneInfo(settings.timezone)
    ).date()

    session = SessionLocal()

    try:
        service = MilkService(session)

        result = service.get_monthly_report(
            telegram_id=user.id,
            year=current_date.year,
            month=current_date.month,
        )

        month_name = current_date.strftime("%B")

        if not result.found:
            await update.effective_message.reply_text(
                f"🥛 {month_name} {current_date.year}\n\n"
                "No milk records found for this month."
            )
            return

        await update.effective_message.reply_text(
            f"🥛 {month_name} {current_date.year}\n\n"
            f"Days recorded: {result.days_recorded}\n"
            f"Total: {result.total_liters} L\n"
            f"Average: {result.average_liters:.2f} L/day\n"
            f"Highest: {result.highest_liters} L\n"
            f"Lowest: {result.lowest_liters} L"
        )

    finally:
        session.close()


async def range_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if update.effective_message is None:
        return

    user = update.effective_user

    if user is None:
        return

    if len(context.args) != 2:
        await update.effective_message.reply_text(
            "Usage:\n"
            "/range YYYY-MM-DD YYYY-MM-DD\n\n"
            "Example:\n"
            "/range 2026-08-01 2026-08-15"
        )
        return

    try:
        start_date = date.fromisoformat(context.args[0])
        end_date = date.fromisoformat(context.args[1])
    except ValueError:
        await update.effective_message.reply_text(
            "Invalid date format.\n\n"
            "Please use YYYY-MM-DD.\n"
            "Example: /range 2026-08-01 2026-08-15"
        )
        return

    if start_date > end_date:
        await update.effective_message.reply_text(
            "Start date must not be after end date."
        )
        return

    session = SessionLocal()

    try:
        service = MilkService(session)

        result = service.get_report_for_range(
            telegram_id=user.id,
            start_date=start_date,
            end_date=end_date,
        )

        date_range = (
            f"{start_date.strftime('%d %b %Y')} → "
            f"{end_date.strftime('%d %b %Y')}"
        )

        if not result.found:
            await update.effective_message.reply_text(
                f"🥛 Milk Report\n"
                f"{date_range}\n\n"
                "No milk records found."
            )
            return

        await update.effective_message.reply_text(
            f"🥛 Milk Report\n"
            f"{date_range}\n\n"
            f"Days recorded: {result.days_recorded}\n"
            f"Total: {result.total_liters} L\n"
            f"Average: {result.average_liters:.2f} L/day\n"
            f"Highest: {result.highest_liters} L\n"
            f"Lowest: {result.lowest_liters} L"
        )

    finally:
        session.close()


async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    logger.exception(
        "Exception while processing Telegram update",
        exc_info=context.error,
    )

    if update is not None and update.effective_message is not None:
        await update.effective_message.reply_text(
            "Sorry, something went wrong. Please try again."
        )