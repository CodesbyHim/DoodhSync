from telegram import Update
from telegram.ext import ContextTypes

from app.config import settings

from datetime import datetime
from zoneinfo import ZoneInfo
from decimal import Decimal, InvalidOperation

from app.database.session import SessionLocal
from app.services.milk_service import MilkService

def is_authorized(update: Update) -> bool:
    user = update.effective_user

    if user is None:
        return False

    return user.id == settings.telegram_allowed_user_id


async def reject_unauthorized(
    update: Update,
) -> None:
    if update.effective_message is not None:
        await update.effective_message.reply_text(
            "You are not authorized to use DoodhSync."
        )


async def start_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if not is_authorized(update):
        await reject_unauthorized(update)
        return

    if update.effective_message is not None:
        await update.effective_message.reply_text(
            "Welcome to DoodhSync! 🥛\n\n"
            "Send today's milk quantity in liters.\n\n"
            "Example:\n"
            "3.25"
        )


async def help_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if not is_authorized(update):
        await reject_unauthorized(update)
        return

    if update.effective_message is not None:
        await update.effective_message.reply_text(
            "DoodhSync Help\n\n"
            "Send a number to record today's milk quantity.\n\n"
            "Example:\n"
            "3.25\n\n"
            "Commands:\n"
            "/start - Start DoodhSync\n"
            "/help - Show this help message"
        )


async def milk_quantity_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if not is_authorized(update):
        await reject_unauthorized(update)
        return

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