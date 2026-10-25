"""Future causal candidate iterator; no feature columns are sampled."""
from dataclasses import dataclass, asdict

from src.features import FeatureEvent
from src.features.schema import integer, identifier
from src.semantic_pipeline.authorization import require_permission
from src.semantic_pipeline.config import FAMILIES
from .semantic_entities import generate_entities, rng, rounded_units, lognormal


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    component_id: str
    history_namespace: str
    candidate_seq: int
    event_time_utc_us: int
    source_vpa_id: str
    beneficiary_vpa_id: str
    amount_paise: int
    intent: int
    family: str
    horizon_exceeded: bool = False

    def __post_init__(self):
        identifier(self.candidate_id, "candidate ID")
        identifier(self.component_id, "component ID")
        integer(self.candidate_seq, "candidate sequence")
        integer(self.intent, "intent", 0, 1)
        if self.family not in ("benign", *FAMILIES) or type(self.horizon_exceeded) is not bool:
            raise ValueError("Invalid latent label metadata")

    def feature_event(self, committed_sequence):
        return FeatureEvent(self.candidate_id, self.history_namespace, committed_sequence,
                            self.event_time_utc_us, self.source_vpa_id,
                            self.beneficiary_vpa_id, self.amount_paise)

    def to_dict(self):
        return asdict(self)


def generate_candidates(config, *, execution_id, permit=None, profile="baseline", entity_data=None):
    require_permission(permit, config, execution_id, "collect")
    data = entity_data if entity_data is not None else generate_entities(
        config, execution_id=execution_id, permit=permit, profile=profile)
    d, b = config.data, config.data["behavior"]

    def iterate():
        for component in data["components"]:
            people = sorted((e for e in data["entities"]
                             if e["component_id"] == component["component_id"]),
                            key=lambda e: e["vpa_id"])
            pool = [e["vpa_id"] for e in people]
            by_vpa = {e["vpa_id"]: e for e in people}
            previous_source, previous_payee = None, None
            escalation = b["escalation_start"]
            when = component["start_time_us"]
            horizon = when + b["episode_seconds"] * 1_000_000
            for seq in range(d["profiles"][profile]["candidate_cap"]):
                key = component["component_id"], seq
                br, tr = rng(d["root_seed"], "behavior", *key), rng(d["root_seed"], "timing", *key)
                intent = int(component["mixed"] and component["attack_start"] <= seq
                             < component["attack_start"] + component["attack_length"])
                family = component["family"] if intent else "benign"
                reuse = b["fraud_source_reuse"] if intent else b["benign_source_reuse"]
                if family == "beneficiary_hopping":
                    source = pool[0]
                elif previous_source is not None and br.random() < reuse:
                    source = previous_source
                else:
                    alternatives = [v for v in pool if v != previous_source] or pool
                    source = str(br.choice(alternatives))
                targets = [v for v in pool
                           if by_vpa[v]["account_id"] != by_vpa[source]["account_id"]]
                if family == "beneficiary_hopping":
                    choices = [v for v in targets if v != previous_payee] or targets
                    target = str(br.choice(choices))
                elif not intent and previous_payee in targets and br.random() < b["benign_payee_reuse"]:
                    target = previous_payee
                else:
                    target = str(br.choice(targets))
                minimum = b["amount_minimum_rupees"]
                if family == "gradual_escalation":
                    amount = escalation
                    escalation *= float(br.uniform(*b["escalation_multiplier"]))
                    escalation *= float(br.lognormal(0, b["escalation_jitter_sigma"]))
                    escalation = min(b["amount_maximum_rupees"], escalation)
                elif family == "high_value_burst" or (
                        not intent and br.random() < b["benign_high_value_probability"]):
                    amount = lognormal(br, b["burst_amount"])
                    minimum = b["burst_amount"]["minimum"]
                elif family == "slow_drain":
                    amount = lognormal(br, b["drain_amount"])
                else:
                    recipe = b["merchant_amount"] if by_vpa[source]["merchant"] else b["individual_amount"]
                    amount = lognormal(br, recipe)
                amount = min(b["amount_maximum_rupees"], max(minimum, amount))
                yield Candidate(f"{component['component_id']}:candidate:{seq:06d}",
                                component["component_id"], component["namespace"], seq, when,
                                source, target, rounded_units(amount), intent, family, when > horizon)
                if when > horizon:
                    break
                if family == "high_value_burst" or (
                        not intent and tr.random() < b["benign_short_delay_probability"]):
                    delay = float(tr.exponential(b["short_delay_mean"]))
                elif family == "slow_drain":
                    delay = lognormal(tr, b["drain_delay"])
                elif family == "beneficiary_hopping":
                    delay = float(tr.uniform(*b["hopping_delay"]))
                elif family == "gradual_escalation":
                    delay = float(tr.uniform(*b["escalation_delay"]))
                else:
                    delay = lognormal(tr, b["routine_delay"])
                delay = min(b["delay_clip_seconds"][1], max(b["delay_clip_seconds"][0], delay))
                when += 0 if tr.random() < b["same_time_probability"] else rounded_units(delay, 1_000_000)
                previous_source, previous_payee = source, target
    return iterate()
