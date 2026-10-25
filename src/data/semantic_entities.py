"""Causal entity identities and role-key RNGs; generation requires execution approval."""
import hashlib
import math
from decimal import Decimal, ROUND_HALF_UP

import numpy as np

from src.features import timestamp_us
from src.features.schema import canonical_json
from src.semantic_pipeline.authorization import require_permission
from src.semantic_pipeline.config import SPLITS


def derive_seed(root, role, *keys, bits=128):
    if type(root) is not int or root < 0 or bits not in (32, 128):
        raise ValueError("Invalid seed request")
    payload = canonical_json(["upi-gc-seed-v1", root, role, *keys]).encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:bits // 8], "big")


def rng(root, role, *keys):
    return np.random.Generator(np.random.PCG64(derive_seed(root, role, *keys)))


def rounded_units(value, scale=100):
    return int((Decimal(str(float(value))) * scale).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def lognormal(random, recipe):
    return float(random.lognormal(math.log(recipe["median"]), recipe["sigma"]))


def generate_entities(config, *, execution_id, permit=None, profile="baseline"):
    require_permission(permit, config, execution_id, "collect")
    d = config.data
    p = d["profiles"][profile]
    root = d["root_seed"]
    simulation = config.generation_digest[:16] + "-" + profile
    order = rng(root, "split", simulation).permutation(p["components"]).tolist()
    assignments, offset = {}, 0
    for name, count in zip(SPLITS, p["split_counts"]):
        for index in order[offset:offset + count]:
            assignments[index] = name
        offset += count
    components, entities, seeds = [], [], {}
    for index in range(p["components"]):
        component = f"{simulation}-g{index:06d}"
        namespace = component + "-episode0"
        seeds[component] = {role: derive_seed(root, role, component)
                            for role in ("entity", "ledger", "intent", "time")}
        er, lr, ir, tr = (rng(root, role, component)
                          for role in ("entity", "ledger", "intent", "time"))
        split = assignments[index]
        start, end = map(timestamp_us, d["splits"][split])
        start_time = int(tr.integers(start, end - d["behavior"]["episode_seconds"] * 1_000_000))
        family = str(ir.choice(d["behavior"]["families"], p=d["behavior"]["family_probabilities"]))
        mixed = bool(ir.random() < d["behavior"]["mixed_component_probability"])
        attack_start = int(ir.integers(p["attack_start"][0], p["attack_start"][1] + 1))
        components.append(dict(component_id=component, namespace=namespace, split=split,
                               start_time_us=start_time, mixed=mixed, family=family,
                               attack_start=attack_start, attack_length=p["attack_length"]))
        counts = d["entities"]["accounts"]
        account_count = int(er.integers(counts[0], counts[1] + 1))
        for account_index in range(account_count):
            account = f"{component}:a{account_index:04d}"
            balance_recipe = d["entities"]["initial_balance"]
            balance = min(balance_recipe["maximum"],
                          max(balance_recipe["minimum"], lognormal(lr, balance_recipe)))
            paise = rounded_units(balance)
            merchant = bool(er.random() < d["behavior"]["merchant_probability"])
            bounds = d["entities"]["vpas_per_account"]
            aliases = int(er.integers(bounds[0], bounds[1] + 1))
            for alias in range(aliases):
                entities.append(dict(
                    component_id=component, namespace=namespace, split=split,
                    account_id=account, vpa_id=f"{component}.a{account_index:04d}.v{alias}@lab",
                    initial_balance_paise=paise, created_time_us=start - 86400_000_000,
                    merchant=merchant,
                ))
    return dict(components=components, entities=entities, entity_seed_map=seeds,
                split_seed=derive_seed(root, "split", simulation))
