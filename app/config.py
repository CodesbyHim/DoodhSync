from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    telegram_bot_token: str
    telegram_allowed_user_id: int
    database_url: str = "sqlite:///./doodhsync.db"
    timezone: str = "Asia/Kolkata"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()