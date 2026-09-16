"""
Synthetic UPI-like transaction generator.

Converts general fraud data into UPI-like format with VPAs, accounts, etc.
"""
import pandas as pd
import numpy as np
from typing import List, Dict
import random


class SyntheticUPIGenerator:
    """Generate synthetic UPI-like transactions."""

    def __init__(self, num_accounts: int = 100):
        """
        Initialize generator.

        Args:
            num_accounts: Number of unique VPA accounts to generate
        """
        self.num_accounts = num_accounts
        self.vpas = [f"user{i}@upi" for i in range(num_accounts)]

    def convert_to_upi_format(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert generic fraud dataset to UPI-like format.

        Args:
            df: DataFrame with fraud data

        Returns:
            DataFrame with UPI-like columns added
        """
        upi_df = df.copy()

        # Add VPA addresses
        upi_df['from_vpa'] = np.random.choice(self.vpas, size=len(df))

        # To VPA should be different from From VPA
        upi_df['to_vpa'] = upi_df.apply(
            lambda _: random.choice([v for v in self.vpas if v != _['from_vpa']]),
            axis=1
        )

        # Ensure Amount column exists
        if 'Amount' not in upi_df.columns:
            # Generate reasonable amounts
            upi_df['Amount'] = np.random.lognormal(7, 2, len(df))

        # Add transaction IDs
        upi_df['transaction_id'] = [f"txn_{i:08d}" for i in range(len(df))]

        return upi_df

    def generate_known_fraud_features(
        self,
        base_amount: float = 25000
    ) -> Dict:
        """
        Generate features for a known fraud transaction.

        Known fraud: high amount, typical fraud patterns
        """
        return {
            'Amount': base_amount * np.random.uniform(0.8, 1.5),
            'from_vpa': random.choice(self.vpas),
            'to_vpa': random.choice(self.vpas),
        }

    def generate_unknown_fraud_features(
        self,
        base_amount: float = 3000
    ) -> Dict:
        """
        Generate features for an unknown fraud transaction.

        Unknown fraud: small amounts, different patterns
        """
        return {
            'Amount': base_amount * np.random.uniform(0.7, 1.3),
            'from_vpa': random.choice(self.vpas),
            'to_vpa': random.choice(self.vpas),
        }
