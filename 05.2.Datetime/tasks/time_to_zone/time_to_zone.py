from datetime import datetime

DEFAULT_TZ_NAME = "Europe/Moscow"


def now() -> datetime:
    """Return now in default timezone"""


def strftime(dt: datetime, fmt: str) -> str:
    """Return dt converted to string according to format in default timezone"""


def strptime(dt_str: str, fmt: str) -> datetime:
    """Return dt parsed from string according to format in default timezone"""


def diff(first_dt: datetime, second_dt: datetime) -> int:
    """Return seconds between two datetimes rounded down to closest int"""


def timestamp(dt: datetime) -> int:
    """Return timestamp for given datetime rounded down to closest int"""


def from_timestamp(ts: float) -> datetime:
    """Return datetime from given timestamp"""
