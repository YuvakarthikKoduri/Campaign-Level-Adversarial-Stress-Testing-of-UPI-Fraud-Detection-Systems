"""Immutable action projection. Labels, decisions, and future outcomes cannot enter."""
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from decimal import Decimal, InvalidOperation
import re

from .schema import integer, identifier, MAX_AMOUNT_PAISE

EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
MIN_TIME_US = -62135596800000000
MAX_TIME_US = 253402300799999999


def utc_datetime(value):
    integer(value, "event_time_utc_us", MIN_TIME_US, MAX_TIME_US)
    return EPOCH + timedelta(microseconds=value)


def timestamp_us(value, *, legacy_naive_utc=False):
    if isinstance(value, str):
        pattern = (r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?"
                   r"(?:Z|[+-]\d{2}:\d{2})")
        legacy_pattern = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?"
        if not (re.fullmatch(pattern, value) or
                (legacy_naive_utc and re.fullmatch(legacy_pattern, value))):
            raise ValueError("Require RFC 3339 with explicit offset and at most six fractional digits")
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("Invalid timestamp") from exc
    if not isinstance(value, datetime):
        raise ValueError("A timestamp must be an explicitly zoned datetime or ISO string")
    if value.tzinfo is None or value.utcoffset() is None:
        if not legacy_naive_utc:
            raise ValueError("Ambiguous naive time; explicitly opt into legacy UTC")
        value = value.replace(tzinfo=timezone.utc)
    delta = value.astimezone(timezone.utc) - EPOCH
    result = (delta.days * 86400 + delta.seconds) * 1_000_000 + delta.microseconds
    utc_datetime(result)
    return result


def rupees_to_paise(value, *, allow_zero=False):
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise ValueError("Money must be numeric rupees, not a boolean")
    try:
        paise = Decimal(str(value)) * 100
        if not paise.is_finite() or paise != paise.to_integral_value():
            raise ValueError("Money must have exact integer paise")
        return integer(int(paise), "amount_paise", 0 if allow_zero else 1, MAX_AMOUNT_PAISE)
    except (InvalidOperation, OverflowError) as exc:
        raise ValueError("Invalid money") from exc


@dataclass(frozen=True)
class FeatureEvent:
    event_id: str
    history_namespace: str
    event_seq: int
    event_time_utc_us: int
    source_vpa_id: str
    beneficiary_vpa_id: str
    amount_paise: int

    def __post_init__(self):
        identifier(self.event_id, "event_id")
        identifier(self.history_namespace, "history_namespace")
        integer(self.event_seq, "event_seq")
        utc_datetime(self.event_time_utc_us)
        identifier(self.source_vpa_id, "source_vpa_id", vpa=True)
        identifier(self.beneficiary_vpa_id, "beneficiary_vpa_id", vpa=True)
        if self.source_vpa_id == self.beneficiary_vpa_id:
            raise ValueError("Self-transfer is not an admitted action")
        integer(self.amount_paise, "amount_paise", 1, MAX_AMOUNT_PAISE)

    @property
    def position(self):
        return self.event_time_utc_us, self.event_seq
