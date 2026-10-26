"""Explicit Gate B simulator adapter with single-writer staged state publication.

The legacy UPIEnvironment is not altered. All transaction-visible ledger, history,
sequence and diagnostic changes are staged and published by one state-reference
swap. Cached Account/list references are snapshots; access current state via env.
"""
import copy
from dataclasses import dataclass, field

from src.features import FeatureEvent, FeatureHistory, timestamp_us
from src.features import extractor as shared
from src.features.events import rupees_to_paise, utc_datetime
from src.features.schema import MAX_AMOUNT_PAISE
from src.detectors.semantic import FixtureDetector
from .entities import Transaction
from .simulator import UPIEnvironment


class RunInvalid(RuntimeError):
    """Internal/order/inference failure: this run cannot continue or count as valid."""


@dataclass
class _LedgerState:
    history: FeatureHistory
    accounts: dict = field(default_factory=dict)
    vpas: dict = field(default_factory=dict)
    transactions: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)
    balances_paise: dict = field(default_factory=dict)
    events: tuple = ()


class SemanticEnvironment(UPIEnvironment):
    """Gate B fixture-only opt-in path; no legacy model can silently enter it."""

    def _validate_predictor(self, predictor):
        """Default Gate B path stays fixture-only; explicit adapters may narrow by purpose."""
        if type(predictor) is not FixtureDetector:
            raise ValueError("Gate B requires an explicit FixtureDetector, not a legacy model")

    def __init__(self, namespace, fraud_detector, *, snapshot=None,
                 legacy_naive_utc=False, threshold_config=None):
        self._validate_predictor(fraud_detector)
        if type(legacy_naive_utc) is not bool:
            raise ValueError("legacy_naive_utc must be explicit boolean")
        history = (FeatureHistory(namespace) if snapshot is None
                   else FeatureHistory.from_snapshot(snapshot, namespace))
        self._state = _LedgerState(history)
        self.namespace = namespace
        self.legacy_naive_utc = legacy_naive_utc
        self.run_invalid = False
        self._processing = False
        self._campaign_started = False
        super().__init__(threshold_config=threshold_config, fraud_detector=fraud_detector)
        self.initial_snapshot = history.snapshot()

    # The inherited read/setup API uses the current state, never parallel fields.
    @property
    def accounts(self):
        return self._state.accounts

    @accounts.setter
    def accounts(self, value):
        self._state.accounts = value

    @property
    def vpas(self):
        return self._state.vpas

    @vpas.setter
    def vpas(self, value):
        self._state.vpas = value

    @property
    def transactions(self):
        return self._state.transactions

    @transactions.setter
    def transactions(self, value):
        self._state.transactions = value

    @property
    def stats(self):
        return self._state.stats

    @stats.setter
    def stats(self, value):
        self._state.stats = value

    @property
    def history(self):
        return self._state.history

    @property
    def admitted_events(self):
        return self._state.events

    def create_account(self, account_id, initial_balance=10000.0, account_type="savings"):
        paise = rupees_to_paise(initial_balance, allow_zero=True)
        account = super().create_account(account_id, paise / 100.0, account_type)
        self._state.balances_paise[account_id] = paise
        return account

    @staticmethod
    def _invalid(details, event_id=None):
        return dict(transaction_id=event_id, decision=None, status="failed",
                    execution_status="invalid", amount_transferred=0.0,
                    risk_score=None, details=details)

    def _require_valid(self):
        if self.run_invalid:
            raise RunInvalid("This semantic run has already been invalidated")

    def process_transaction(self, transaction_data):
        self._require_valid()
        try:
            sequence = self.history.next_sequence
        except Exception as exc:
            self.run_invalid = True
            raise RunInvalid("Corrupt history before transaction admission") from exc
        try:
            permitted = {"transaction_id", "from_vpa", "to_vpa", "amount", "timestamp"}
            if type(transaction_data) is not dict or set(transaction_data) - permitted:
                raise ValueError("Only the explicit pre-decision transaction projection is accepted")
            event = FeatureEvent(
                transaction_data.get("transaction_id", f"{self.namespace}:event:{sequence}"),
                self.namespace, sequence,
                timestamp_us(transaction_data["timestamp"],
                             legacy_naive_utc=self.legacy_naive_utc),
                transaction_data["from_vpa"], transaction_data["to_vpa"],
                rupees_to_paise(transaction_data["amount"]),
            )
        except (ValueError, TypeError, KeyError, OverflowError) as exc:
            return self._invalid(str(exc))
        return self.process_event(event)

    def _validate_ledger(self, stage):
        if set(stage.accounts) != set(stage.balances_paise):
            raise ValueError("Ledger account index mismatch")
        for key, account in stage.accounts.items():
            if (account.account_id != key
                    or type(account.is_active) is not bool
                    or rupees_to_paise(account.balance, allow_zero=True) != stage.balances_paise[key]):
                raise ValueError("Ledger integer/mirror balance mismatch")
        for key, vpa in stage.vpas.items():
            if (vpa.vpa_id != key or vpa.account_id not in stage.accounts
                    or type(vpa.is_active) is not bool):
                raise ValueError("Corrupt VPA/account mapping")
        if len(stage.events) != len(stage.transactions):
            raise ValueError("Admitted-event/diagnostic mismatch")
        initial = self.initial_snapshot.to_dict()
        expected_sources = dict(initial["source_counts"])
        expected_ids = set(initial["event_ids"])
        expected_recent = list(initial["recent"])
        last_position = initial["last_position"]
        histories = {key: [] for key in stage.accounts}
        statistics = dict(total_transactions=0, allowed=0, flagged=0, blocked=0, failed=0)
        for event, txn in zip(stage.events, stage.transactions):
            if (type(event) is not FeatureEvent or type(txn) is not Transaction
                    or event.history_namespace != self.namespace
                    or event.event_id in expected_ids
                    or (last_position is not None and
                        (event.event_time_utc_us < last_position[0]
                         or event.event_seq <= last_position[1]))
                    or txn.transaction_id != event.event_id
                    or txn.from_vpa != event.source_vpa_id or txn.to_vpa != event.beneficiary_vpa_id
                    or rupees_to_paise(txn.amount) != event.amount_paise
                    or timestamp_us(txn.timestamp, legacy_naive_utc=self.legacy_naive_utc)
                    != event.event_time_utc_us
                    or txn.status not in ("success", "flagged", "blocked")):
                raise ValueError("Corrupt canonical event/transaction lineage")
            if txn.status != "blocked":
                for vpa_id in (txn.from_vpa, txn.to_vpa):
                    histories[stage.vpas[vpa_id].account_id].append(event.event_id)
            statistics["total_transactions"] += 1
            statistics[{"success": "allowed", "flagged": "flagged", "blocked": "blocked"}[txn.status]] += 1
            expected_sources[event.source_vpa_id] = expected_sources.get(event.source_vpa_id, 0) + 1
            expected_ids.add(event.event_id)
            last_position = list(event.position)
            expected_recent.append([event.event_id, event.source_vpa_id,
                                    event.event_time_utc_us, event.event_seq])
        if stage.stats != statistics or any(
                account.transaction_history != histories[key]
                for key, account in stage.accounts.items()):
            raise ValueError("Ledger history/statistics mismatch")
        current = stage.history.snapshot().to_dict()
        if last_position is not None:
            from src.features.schema import WINDOW_US
            expected_recent = [row for row in expected_recent
                               if row[2] > last_position[0] - WINDOW_US]
        if (current["event_ids"] != sorted(expected_ids)
                or current["source_counts"] != [list(p) for p in sorted(expected_sources.items())]
                or current["last_position"] != last_position or current["recent"] != expected_recent):
            raise ValueError("Feature history/admitted ledger mismatch")

    def _eligible(self, event):
        self._validate_ledger(self._state)
        if event.source_vpa_id not in self.vpas or event.beneficiary_vpa_id not in self.vpas:
            return False
        source, target = self.vpas[event.source_vpa_id], self.vpas[event.beneficiary_vpa_id]
        if source.account_id == target.account_id:
            return False
        sender, receiver = self.accounts[source.account_id], self.accounts[target.account_id]
        return (
            source.is_active and target.is_active and sender.is_active and receiver.is_active
            and self._state.balances_paise[source.account_id] >= event.amount_paise
            and self._state.balances_paise[target.account_id] + event.amount_paise <= MAX_AMOUNT_PAISE
        )

    @staticmethod
    def _settle(stage, event, decision):
        if decision == "BLOCK":
            return
        source = stage.vpas[event.source_vpa_id].account_id
        target = stage.vpas[event.beneficiary_vpa_id].account_id
        amount = event.amount_paise / 100.0
        if not stage.accounts[source].debit(amount, event.event_id):
            raise RuntimeError("Validated debit failed")
        if not stage.accounts[target].credit(amount, event.event_id):
            raise RuntimeError("Validated credit failed")
        # Exact integer money is authoritative; float balances are compatibility views.
        stage.balances_paise[source] -= event.amount_paise
        stage.balances_paise[target] += event.amount_paise
        stage.accounts[source].balance = stage.balances_paise[source] / 100.0
        stage.accounts[target].balance = stage.balances_paise[target] / 100.0

    def _response(self, event, record, decision, score):
        when = utc_datetime(event.event_time_utc_us)
        if self.legacy_naive_utc:
            when = when.replace(tzinfo=None)
        blocked = decision == "BLOCK"
        return dict(
            transaction_id=event.event_id, risk_score=score, risk_factors=[],
            decision=decision, status="blocked" if blocked else "success",
            execution_status="blocked" if blocked else "success",
            amount_transferred=0.0 if blocked else event.amount_paise / 100.0,
            from_vpa=event.source_vpa_id, to_vpa=event.beneficiary_vpa_id,
            amount=event.amount_paise / 100.0, timestamp=when.isoformat(),
            details="Gate B fixture-only; simulated transfer, no recovery",
            features=record.to_dict(), effective_policy=self.threshold_config.to_dict(),
        )

    def _before_publish(self, stage):
        """Fault-injection/validation boundary; must not mutate live state."""
        self._require_valid()
        self._validate_ledger(stage)
        if sum(stage.balances_paise.values()) != sum(self._state.balances_paise.values()):
            raise ValueError("Ledger conservation failure")
        if stage.stats["total_transactions"] != len(stage.transactions):
            raise ValueError("Diagnostic/ledger count mismatch")
        stage.history.snapshot()

    def process_event(self, event):
        self._require_valid()
        if self._processing:
            self.run_invalid = True
            raise RunInvalid("Reentrant processing is not supported")
        self._processing = True
        try:
            return self._process_event(event)
        finally:
            self._processing = False

    def _process_event(self, event):
        try:
            view = self.history.view_before(event)
            if not self._eligible(event):
                return self._invalid("Unregistered, inactive, insufficient, or ineligible ledger",
                                     event.event_id)
            record = shared.extract_features(event, view)
            vector = shared.encode_vector(record)
            self._validate_predictor(self.fraud_detector)
            score = self.fraud_detector.predict(vector)
            decision = self.threshold_config.get_decision(score).value
            stage = copy.deepcopy(self._state)
            self._settle(stage, event, decision)
            response = self._response(event, record, decision, score)
            transaction = Transaction.from_dict(copy.deepcopy(response))
            transaction.mark_status("blocked" if decision == "BLOCK" else
                                    "flagged" if decision == "FLAG" else "success")
            stage.transactions.append(transaction)
            stage.events += (event,)
            stage.stats["total_transactions"] += 1
            stage.stats[{"ALLOW": "allowed", "FLAG": "flagged", "BLOCK": "blocked"}[decision]] += 1
            stage.history.commit_observation(event)
            self._before_publish(stage)
        except Exception as exc:
            self.run_invalid = True
            raise RunInvalid("Semantic processing failed; no candidate state was committed") from exc
        # No fallible application work follows publication.
        self._state = stage
        return response
