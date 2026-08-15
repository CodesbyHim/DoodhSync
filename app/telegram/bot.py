from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

from app.config import settings
from app.telegram.handlers import (
    help_handler,
    history_handler,
    milk_quantity_handler,
    start_handler,
    today_handler,
)

from app.telegram.handlers import (
    help_handler,
    history_handler,
    milk_quantity_handler,
    month_handler,
    start_handler,
    today_handler,
)

from app.telegram.handlers import (
    help_handler,
    history_handler,
    milk_quantity_handler,
    month_handler,
    range_handler,
    start_handler,
    today_handler,
)

def create_application() -> Application:
    application = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start_handler)
    )

    application.add_handler(
        CommandHandler("help", help_handler)
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            milk_quantity_handler,
        )
    )    

    application.add_handler(
        CommandHandler("today", today_handler)
    )

    application.add_handler(
        CommandHandler("history", history_handler)
    )   
    
    application.add_handler(
        CommandHandler("month", month_handler)
    )

    application.add_handler(
        CommandHandler("range", range_handler)
    )

    return application


def run() -> None:
    application = create_application()

    application.run_polling()