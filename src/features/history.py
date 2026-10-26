"""Immutable history state with canonical, integrity-checked snapshot boundaries.

Recent attempt rows are compacted to one hour; lifetime source counters and event
IDs remain for novelty and duplicate protection. This is not a concurrent database.
"""
from collections import Counter
from dataclasses import dataclass

from .events import FeatureEvent, utc_datetime
from .schema import (CONTRACT_ID, SCHEMA_DIGEST, WINDOW_US, canonical_json, parse_json,
                     digest, identifier, integer)


@dataclass(frozen=True)
class Observation:
    event_id: str
    source: str
    time_us: int
    seq: int

    @classmethod
    def from_event(cls, event):
        return cls(event.event_id, event.source_vpa_id, event.event_time_utc_us, event.event_seq)


@dataclass(frozen=True)
class HistorySnapshot:
    payload_json: str
    sha256: str

    @classmethod
    def from_dict(cls, payload):
        return cls(canonical_json(payload), digest(payload))

    def to_dict(self):
        payload = parse_json(self.payload_json)
        if self.payload_json != canonical_json(payload) or self.sha256 != digest(payload):
            raise ValueError("Snapshot hash/canonicalization mismatch")
        return payload


@dataclass(frozen=True)
class HistoryView:
    event: FeatureEvent
    recent: tuple
    seen_sources: frozenset


@dataclass(frozen=True)
class _State:
    recent: tuple = ()
    seen_sources: frozenset = frozenset()
    event_ids: frozenset = frozenset()
    source_counts: tuple = ()
    last_position: tuple = None


class FeatureHistory:
    def __init__(self, namespace):
        self.namespace = identifier(namespace, "history_namespace")
        self._state = _State()

    def _validate(self):
        s = self._state
        if (type(s) is not _State or type(s.recent) is not tuple
                or type(s.seen_sources) is not frozenset or type(s.event_ids) is not frozenset
                or type(s.source_counts) is not tuple):
            raise ValueError("Malformed history state")
        counts = dict(s.source_counts)
        if (len(counts) != len(s.source_counts) or tuple(sorted(counts.items())) != s.source_counts
                or frozenset(counts) != s.seen_sources):
            raise ValueError("Inconsistent source counters")
        for source, count in counts.items():
            identifier(source, "observed source", vpa=True)
            integer(count, "source count", 1)
        for event_id in s.event_ids:
            identifier(event_id, "observed event ID")
        if sum(counts.values()) != len(s.event_ids):
            raise ValueError("Inconsistent event ID/count metadata")
        if not s.event_ids:
            if s != _State():
                raise ValueError("Nonempty metadata in empty history")
            return
        if not s.recent or type(s.last_position) is not tuple or len(s.last_position) != 2:
            raise ValueError("Missing history cutoff")
        last_time, last_seq = s.last_position
        utc_datetime(last_time)
        integer(last_seq, "last sequence")
        if len(s.event_ids) > last_seq + 1:
            raise ValueError("More observations than possible sequence positions")
        observed = set()
        recent_counts = Counter()
        prior_time, prior_seq = None, -1
        for row in s.recent:
            if type(row) is not Observation:
                raise ValueError("Invalid history observation")
            identifier(row.event_id, "observation ID")
            identifier(row.source, "observation source", vpa=True)
            utc_datetime(row.time_us)
            integer(row.seq, "observation sequence")
            if (row.event_id not in s.event_ids or row.event_id in observed
                    or row.source not in s.seen_sources or row.seq <= prior_seq
                    or (prior_time is not None and row.time_us < prior_time)
                    or not last_time - WINDOW_US < row.time_us <= last_time):
                raise ValueError("Corrupt/future/out-of-order history")
            observed.add(row.event_id)
            recent_counts[row.source] += 1
            prior_time, prior_seq = row.time_us, row.seq
        if (prior_time, prior_seq) != s.last_position:
            raise ValueError("History cutoff disagrees with final observation")
        if any(counts[source] < count for source, count in recent_counts.items()):
            raise ValueError("Recent history exceeds lifetime source counter")

    @property
    def next_sequence(self):
        self._validate()
        return 0 if self._state.last_position is None else self._state.last_position[1] + 1

    @property
    def empty(self):
        self._validate()
        return not self._state.event_ids

    def view_before(self, event):
        if type(event) is not FeatureEvent:
            raise ValueError("Expected a canonical FeatureEvent")
        self._validate()
        s = self._state
        if event.history_namespace != self.namespace or event.event_id in s.event_ids:
            raise ValueError("Wrong namespace or duplicate event ID")
        if s.last_position is not None:
            last_time, last_seq = s.last_position
            if event.event_time_utc_us < last_time or event.event_seq <= last_seq:
                raise ValueError("Backwards timestamp or nonincreasing sequence")
        return HistoryView(event, s.recent, s.seen_sources)

    def commit_observation(self, event):
        # This API accepts successfully processed/admitted events, not raw actions.
        self.view_before(event)
        s = self._state
        recent = tuple(row for row in s.recent
                       if row.time_us > event.event_time_utc_us - WINDOW_US)
        counts = dict(s.source_counts)
        counts[event.source_vpa_id] = counts.get(event.source_vpa_id, 0) + 1
        candidate = _State(
            recent + (Observation.from_event(event),),
            s.seen_sources | {event.source_vpa_id},
            s.event_ids | {event.event_id},
            tuple(sorted(counts.items())),
            event.position,
        )
        # Validate an isolated candidate; never leave a failed append committed.
        check = FeatureHistory(self.namespace)
        check._state = candidate
        check._validate()
        self._state = candidate

    def snapshot(self):
        self._validate()
        s = self._state
        return HistorySnapshot.from_dict({
            "contract_id": CONTRACT_ID, "schema_digest": SCHEMA_DIGEST,
            "namespace": self.namespace,
            "recent": [[r.event_id, r.source, r.time_us, r.seq] for r in s.recent],
            "seen_sources": sorted(s.seen_sources), "event_ids": sorted(s.event_ids),
            "source_counts": [list(pair) for pair in s.source_counts],
            "last_position": list(s.last_position) if s.last_position is not None else None,
        })

    @classmethod
    def from_snapshot(cls, snapshot, namespace):
        if type(snapshot) is not HistorySnapshot:
            raise ValueError("Expected a hashed HistorySnapshot")
        payload = snapshot.to_dict()
        expected = {"contract_id", "schema_digest", "namespace", "recent", "seen_sources",
                    "event_ids", "source_counts", "last_position"}
        if (type(payload) is not dict or set(payload) != expected
                or payload["contract_id"] != CONTRACT_ID or payload["schema_digest"] != SCHEMA_DIGEST
                or payload["namespace"] != namespace):
            raise ValueError("Snapshot contract/schema/namespace mismatch")
        for key in ("recent", "seen_sources", "event_ids", "source_counts"):
            if type(payload[key]) is not list:
                raise ValueError("Malformed snapshot collection")
        for key in ("seen_sources", "event_ids"):
            values = payload[key]
            if any(type(v) is not str for v in values) or sorted(set(values)) != values:
                raise ValueError("Noncanonical or duplicate snapshot identities")
        try:
            result = cls(namespace)
            result._state = _State(
                tuple(Observation(*row) for row in payload["recent"]),
                frozenset(payload["seen_sources"]), frozenset(payload["event_ids"]),
                tuple(tuple(pair) for pair in payload["source_counts"]),
                tuple(payload["last_position"]) if payload["last_position"] is not None else None,
            )
            result._validate()
            return result
        except (TypeError, KeyError, IndexError) as exc:
            raise ValueError("Malformed snapshot") from exc
