from datetime import datetime
from zoneinfo import ZoneInfo

from app.config import settings


def test_doodhsync_timezone_is_configured():
    timezone = ZoneInfo(settings.timezone)

    current_date = datetime.now(timezone).date()

    assert current_date is not None