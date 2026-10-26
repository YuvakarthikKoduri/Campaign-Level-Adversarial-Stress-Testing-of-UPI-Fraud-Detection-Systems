"""The sole semantic-v2 feature calculation and float64 vector encoder."""
import math
from dataclasses import dataclass

import numpy as np

from .events import utc_datetime, rupees_to_paise
from .history import HistoryView
from .schema import FEATURE_NAMES, MAX_AMOUNT_PAISE, WINDOW_US, integer


@dataclass(frozen=True)
class FeatureRecord:
    amount: float
    hour_of_day: int
    velocity_1h: int
    is_new_vpa: int

    def __post_init__(self):
        if (type(self.amount) is not float or not math.isfinite(self.amount)
                or not 0 < self.amount <= MAX_AMOUNT_PAISE / 100):
            raise ValueError("Invalid rupee feature")
        rupees_to_paise(self.amount)  # no fractional paise in serialized feature rows
        integer(self.hour_of_day, "hour_of_day", 0, 23)
        integer(self.velocity_1h, "velocity_1h")
        integer(self.is_new_vpa, "is_new_vpa", 0, 1)

    def to_dict(self):
        return {key: getattr(self, key) for key in FEATURE_NAMES}


def extract_features(event, history_view):
    if type(history_view) is not HistoryView or history_view.event != event:
        raise ValueError("History view is bound to a different event")
    # Every row in the view must precede the event, including same-time rows.
    if any(row.time_us > event.event_time_utc_us or row.seq >= event.event_seq
           for row in history_view.recent):
        raise ValueError("Future event in feature history")
    velocity = sum(
        row.source == event.source_vpa_id
        and event.event_time_utc_us - WINDOW_US < row.time_us <= event.event_time_utc_us
        for row in history_view.recent
    )
    return FeatureRecord(
        event.amount_paise / 100.0,
        utc_datetime(event.event_time_utc_us).hour,
        velocity,
        int(event.source_vpa_id not in history_view.seen_sources),
    )


def encode_vector(record):
    if type(record) is not FeatureRecord:
        raise ValueError("Expected a typed FeatureRecord, not arbitrary feature columns")
    record.__post_init__()
    result = np.asarray([[getattr(record, key) for key in FEATURE_NAMES]], dtype=np.float64)
    result.setflags(write=False)
    return result
