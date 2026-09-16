"""
Data Loading Module for UPI Fraud Stress Lab

Provides functions to load and validate fraud detection datasets.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, Dict
import logging

logger = logging.getLogger(__name__)


class FraudDataLoader:
    """Load and validate fraud detection datasets"""

    def __init__(self, data_dir: str = "data/raw"):
        """
        Initialize the data loader

        Args:
            data_dir: Directory containing raw data files
        """
        self.data_dir = Path(data_dir)
        self.dataset_path = self.data_dir / "creditcard.csv"

    def load_raw(self, nrows: Optional[int] = None) -> pd.DataFrame:
        """
        Load raw fraud dataset

        Args:
            nrows: Number of rows to load (None = all)

        Returns:
            DataFrame with raw transaction data
        """
        if not self.dataset_path.exists():
            raise FileNotFoundError(
                f"Dataset not found at {self.dataset_path}. "
                f"Run 'python data/raw/download_dataset.py' first."
            )

        logger.info(f"Loading dataset from {self.dataset_path}")
        df = pd.read_csv(self.dataset_path, nrows=nrows)

        logger.info(f"Loaded {len(df)} transactions")
        logger.info(f"Columns: {list(df.columns)}")

        return df

    def validate_dataset(self, df: pd.DataFrame) -> Dict[str, any]:
        """
        Validate dataset structure and content

        Args:
            df: DataFrame to validate

        Returns:
            Dictionary with validation statistics
        """
        stats = {
            'total_transactions': len(df),
            'features': list(df.columns),
            'missing_values': df.isnull().sum().to_dict(),
            'fraud_count': 0,
            'legitimate_count': 0,
            'fraud_rate': 0.0,
        }

        # Check for Class/fraud label column
        fraud_col = None
        for col in ['Class', 'isFraud', 'is_fraud', 'fraud']:
            if col in df.columns:
                fraud_col = col
                break

        if fraud_col:
            stats['fraud_count'] = int(df[fraud_col].sum())
            stats['legitimate_count'] = int(len(df) - stats['fraud_count'])
            stats['fraud_rate'] = float(stats['fraud_count'] / len(df))
            stats['fraud_column'] = fraud_col
        else:
            logger.warning("No fraud label column found!")
            stats['fraud_column'] = None

        # Check for Time and Amount columns
        stats['has_time'] = 'Time' in df.columns
        stats['has_amount'] = 'Amount' in df.columns

        if stats['has_amount']:
            stats['amount_stats'] = {
                'mean': float(df['Amount'].mean()),
                'median': float(df['Amount'].median()),
                'min': float(df['Amount'].min()),
                'max': float(df['Amount'].max()),
                'std': float(df['Amount'].std()),
            }

        return stats

    def load_train_test_split(
        self,
        test_size: float = 0.2,
        random_state: int = 42,
        stratify: bool = True
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Load data and split into train/test sets

        Args:
            test_size: Fraction of data for testing
            random_state: Random seed for reproducibility
            stratify: Whether to stratify split by fraud label

        Returns:
            Tuple of (train_df, test_df)
        """
        from sklearn.model_selection import train_test_split

        df = self.load_raw()

        # Find fraud column
        fraud_col = None
        for col in ['Class', 'isFraud', 'is_fraud', 'fraud']:
            if col in df.columns:
                fraud_col = col
                break

        if stratify and fraud_col:
            train_df, test_df = train_test_split(
                df,
                test_size=test_size,
                random_state=random_state,
                stratify=df[fraud_col]
            )
        else:
            train_df, test_df = train_test_split(
                df,
                test_size=test_size,
                random_state=random_state
            )

        logger.info(f"Train set: {len(train_df)} transactions")
        logger.info(f"Test set: {len(test_df)} transactions")

        return train_df, test_df

    def get_dataset_info(self) -> Dict[str, any]:
        """
        Get comprehensive dataset information without loading all data

        Returns:
            Dictionary with dataset metadata
        """
        if not self.dataset_path.exists():
            return {'status': 'not_found', 'path': str(self.dataset_path)}

        # Load sample to get schema
        sample = pd.read_csv(self.dataset_path, nrows=1000)

        # Get file size
        file_size_mb = self.dataset_path.stat().st_size / (1024 * 1024)

        info = {
            'status': 'available',
            'path': str(self.dataset_path),
            'file_size_mb': round(file_size_mb, 2),
            'columns': list(sample.columns),
            'dtypes': sample.dtypes.to_dict(),
        }

        # Add validation stats from sample
        info.update(self.validate_dataset(sample))

        return info


def load_fraud_data(
    data_dir: str = "data/raw",
    nrows: Optional[int] = None
) -> pd.DataFrame:
    """
    Convenience function to load fraud dataset

    Args:
        data_dir: Directory containing raw data
        nrows: Number of rows to load (None = all)

    Returns:
        DataFrame with transaction data
    """
    loader = FraudDataLoader(data_dir)
    return loader.load_raw(nrows)


def get_fraud_label_column(df: pd.DataFrame) -> str:
    """
    Find the fraud label column in a DataFrame

    Args:
        df: DataFrame to search

    Returns:
        Name of fraud label column

    Raises:
        ValueError: If no fraud label column found
    """
    for col in ['Class', 'isFraud', 'is_fraud', 'fraud', 'label']:
        if col in df.columns:
            return col

    raise ValueError("No fraud label column found in dataset")
