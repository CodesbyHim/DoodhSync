from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from telegram import Update

from app.telegram.bot import create_application


telegram_application = create_application()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await telegram_application.initialize()
    await telegram_application.start()

    yield

    await telegram_application.stop()
    await telegram_application.shutdown()


app = FastAPI(
    title="DoodhSync",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/telegram/webhook")
async def telegram_webhook(request: Request) -> dict[str, bool]:
    data = await request.json()

    update = Update.de_json(
        data=data,
        bot=telegram_application.bot,
    )

    await telegram_application.update_queue.put(update)

    return {"ok": True}