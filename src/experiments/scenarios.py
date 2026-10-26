"""S1-S4 orchestration over paired immutable workloads, retaining the scenario API."""
import json
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from src.attackers.family_based import make_attacker
from src.campaigns.executor import CampaignExecutor
from src.campaigns.generator import Campaign, CampaignFamily
from src.campaigns.vpa_strategy import VPAStrategy
from src.environment import UPIEnvironment
from src.evaluation.metrics import CampaignMetrics
from src.experiments.config import RunConfig, build_workload


class ExperimentScenarios:
    def __init__(self, detector, environment, config=None, workload=None):
        self.detector, self.environment = detector, environment
        self.config = config
        self.workload = workload
        self.records = {}

    def _run(self, scenario, num_campaigns=100, verbose=False, seed=42):
        config = self.config or RunConfig(
            seed=seed, campaigns=num_campaigns,
            flag_threshold=self.environment.threshold_config.flag_threshold,
            block_threshold=self.environment.threshold_config.block_threshold)
        if config.seed != seed or config.campaigns != num_campaigns:
            raise ValueError("Scenario arguments do not match immutable RunConfig")
        if (config.flag_threshold != self.environment.threshold_config.flag_threshold
                or config.block_threshold != self.environment.threshold_config.block_threshold):
            raise ValueError("Environment policy does not match RunConfig")
        workload = self.workload or build_workload(config)
        kind = "known" if scenario in ("S1", "S2") else "unknown"
        adaptive = scenario in ("S2", "S4")
        campaigns, records = [], []
        for spec in workload[kind]:
            family = CampaignFamily(spec.family)
            campaign = Campaign(spec.campaign_id, "controlled-attacker", "simulated transfer",
                                spec.target_amount, spec.fraud_type, family,
                                VPAStrategy(spec.vpa_strategy))
            campaign.created_at = datetime.fromisoformat(spec.start_time)
            campaign.policy_seed, campaign.timer_seed, campaign.vpa_seed = (
                spec.policy_seed, spec.timer_seed, spec.vpa_seed)
            campaign.budget = config.budget
            campaign.max_duration_seconds = config.max_duration_seconds
            campaign.is_fraud = spec.is_fraud
            # Preserve the supplied environment policy; no shared ledger state.
            from copy import deepcopy
            env = UPIEnvironment(threshold_config=deepcopy(self.environment.threshold_config),
                                 fraud_detector=self.detector)
            for vpa in config.accounts:
                env.create_account(vpa, config.initial_balance)
                env.create_vpa(vpa, vpa, vpa)
            actor = make_attacker(family, adaptive=adaptive, seed=spec.policy_seed)
            executor = CampaignExecutor(self.detector, env, actor, config.max_steps,
                                        config.feedback, config.max_transaction_amount)
            executor.execute_campaign(campaign, list(config.accounts), verbose, seed=seed)
            if campaign.status.value == "INVALID":
                raise RuntimeError(f"Invalid campaign {spec.campaign_id}: {campaign.invalid_action}")
            initial_total = config.initial_balance * len(config.accounts)
            if abs(sum(a.balance for a in env.accounts.values()) - initial_total) > 1e-6:
                raise RuntimeError("Ledger conservation failed")
            records.append({
                "spec": spec.to_dict(), "adaptive": adaptive,
                "outcome": campaign.to_dict(), "transactions": campaign.transactions,
                "feedback": actor.history,
                "attacker_state": actor.get_adaptation_summary(),
                "final_balances": {a: env.accounts[a].balance for a in config.accounts},
                "effective_policy": env.threshold_config.to_dict(),
            })
            campaigns.append(campaign)
        self.records[scenario] = records
        return CampaignMetrics.generate_summary(campaigns, scenario)

    def run_scenario_s1(self, num_campaigns=100, verbose=False, seed=42):
        return self._run("S1", num_campaigns, verbose, seed)

    def run_scenario_s2(self, num_campaigns=100, verbose=False, seed=42):
        return self._run("S2", num_campaigns, verbose, seed)

    def run_scenario_s3(self, num_campaigns=100, verbose=False, seed=42):
        return self._run("S3", num_campaigns, verbose, seed)

    def run_scenario_s4(self, num_campaigns=100, verbose=False, seed=42):
        return self._run("S4", num_campaigns, verbose, seed)

    def run_all_scenarios(self, num_campaigns=100, save_results=True,
                          detector_name="XGBoost", seed=42, output_dir=None):
        results = {name: self._run(name, num_campaigns, seed=seed)
                   for name in ("S1", "S2", "S3", "S4")}
        if save_results:
            # The CLI owns manifests; direct API calls must declare a fresh folder.
            if output_dir is None:
                raise ValueError("Explicit fresh output_dir required; fixed paths are disabled")
            root = Path(output_dir)
            root.mkdir(parents=True, exist_ok=False)
            (root / "summary.json").write_text(json.dumps(results, indent=2, allow_nan=False))
            (root / "campaigns.json").write_text(json.dumps(self.records, indent=2, allow_nan=False))
        return results
