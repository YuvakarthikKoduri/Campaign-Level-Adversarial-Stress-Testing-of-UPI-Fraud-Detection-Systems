"""Campaign constraint validator."""

from typing import Dict, List, Optional
from dataclasses import dataclass
from .campaign import Campaign


@dataclass
class ValidationResult:
    """Result of campaign validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]


class CampaignValidator:
    """Validates campaign constraints before execution."""

    def __init__(self):
        self.min_target = 100
        self.max_target = 100000
        self.min_step_amount = 10
        self.max_step_amount = 100000

    def validate(self, campaign: Campaign, accounts: List[str]) -> ValidationResult:
        """
        Validate campaign against constraints.

        Args:
            campaign: Campaign to validate
            accounts: Available accounts

        Returns:
            ValidationResult with errors/warnings
        """
        errors = []
        warnings = []

        # Validate target amount
        if campaign.target_amount < self.min_target:
            errors.append(f"Target amount ₹{campaign.target_amount} below minimum ₹{self.min_target}")

        if campaign.target_amount > self.max_target:
            warnings.append(f"Target amount ₹{campaign.target_amount} exceeds typical limit ₹{self.max_target}")

        # Validate accounts available
        if not accounts or len(accounts) == 0:
            errors.append("No accounts available for campaign execution")

        if len(accounts) < 5:
            warnings.append(f"Only {len(accounts)} accounts available, recommend at least 5")

        # Validate fraud type
        if campaign.fraud_type not in ["known", "unknown"]:
            errors.append(f"Invalid fraud type: {campaign.fraud_type}")

        # Validate max steps
        if hasattr(campaign, 'max_steps') and campaign.max_steps is not None:
            if campaign.max_steps < 1:
                errors.append("Max steps must be at least 1")

            if campaign.max_steps > 100:
                warnings.append(f"Max steps {campaign.max_steps} very high, may take long time")

        # Validate campaign family parameters
        if hasattr(campaign, 'parameters') and campaign.parameters:
            params = campaign.parameters

            if 'amount_range' in params:
                min_amt, max_amt = params['amount_range']

                if min_amt < self.min_step_amount:
                    errors.append(f"Minimum amount ₹{min_amt} below limit ₹{self.min_step_amount}")

                if max_amt > self.max_step_amount:
                    warnings.append(f"Maximum amount ₹{max_amt} exceeds typical limit")

                if min_amt >= max_amt:
                    errors.append(f"Invalid amount range: min (₹{min_amt}) >= max (₹{max_amt})")

        is_valid = len(errors) == 0

        return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)

    def validate_batch(
        self,
        campaigns: List[Campaign],
        accounts: List[str]
    ) -> Dict[str, ValidationResult]:
        """
        Validate multiple campaigns.

        Args:
            campaigns: List of campaigns to validate
            accounts: Available accounts

        Returns:
            Dictionary mapping campaign_id to ValidationResult
        """
        results = {}

        for campaign in campaigns:
            result = self.validate(campaign, accounts)
            results[campaign.campaign_id] = result

        return results

    def print_validation_report(self, result: ValidationResult, campaign_id: str):
        """Print human-readable validation report."""
        print(f"\nValidation Report: {campaign_id}")
        print("="*60)

        if result.is_valid:
            print("✓ Campaign is valid")
        else:
            print("✗ Campaign has errors")

        if result.errors:
            print("\nErrors:")
            for error in result.errors:
                print(f"  ✗ {error}")

        if result.warnings:
            print("\nWarnings:")
            for warning in result.warnings:
                print(f"  ⚠ {warning}")

        if not result.errors and not result.warnings:
            print("  No issues found")
