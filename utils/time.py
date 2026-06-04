from datetime import datetime
import pytz

COLUMBUS_TZ = pytz.timezone("America/New_York")


def now_columbus() -> datetime:
    return datetime.now(COLUMBUS_TZ)


def now_columbus_naive() -> datetime:
    return datetime.now(COLUMBUS_TZ).replace(tzinfo=None)