"""Opt-in bridge to the actual Milestone 1 loop, never selected by its runner."""
import copy

from src.environment.semantic import SemanticEnvironment, RunInvalid
from src.campaigns.generator import CampaignStatus
from .executor import CampaignExecutor


class SemanticCampaignExecutor(CampaignExecutor):
    """Use a fresh environment per campaign and explicitly interpret legacy UTC.

    Unexpected loop/feedback errors restore the entire pre-call semantic ledger
    and campaign accounting, mark the run invalid, and propagate. External user
    callback side effects cannot be rolled back and are not valid run evidence.
    """

    def execute_campaign(self, campaign, accounts, verbose=False, seed=None):
        env = self.environment
        if (type(env) is not SemanticEnvironment or not env.legacy_naive_utc
                or env.namespace != campaign.campaign_id or env.transactions
                or env.history.snapshot() != env.initial_snapshot or campaign.transactions
                or env._campaign_started or campaign.is_complete()
                or self.detector is not env.fraud_detector):
            raise ValueError("Use a fresh matching semantic environment/campaign and explicit legacy UTC")
        env._require_valid()
        original_state = env._state
        original_campaign = copy.deepcopy(campaign.__dict__)
        env._campaign_started = True
        try:
            result = super().execute_campaign(campaign, accounts, verbose=verbose, seed=seed)
            if result.status == CampaignStatus.INVALID:
                env.run_invalid = True
            return result
        except Exception as exc:
            env._state = original_state
            env.run_invalid = True
            campaign.__dict__.clear()
            campaign.__dict__.update(original_campaign)
            campaign.finalize(CampaignStatus.INVALID, "semantic_processing_error", campaign.created_at)
            raise RunInvalid("Semantic campaign invalidated; pre-call ledger/accounting restored") from exc
