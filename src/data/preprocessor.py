"""
Data Preprocessing Module for UPI Fraud Stress Lab

Handles feature engineering, scaling, and data transformation.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, List, Dict
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.model_selection import train_test_split
import logging
import pickle

logger = logging.getLogger(__name__)


class FraudDataPreprocessor:
    """Preprocess fraud detection data for model training"""

    def __init__(self, scaling_method: str = 'standard'):
        """
        Initialize preprocessor

        Args:
            scaling_method: 'standard', 'robust', or 'none'
        """
        self.scaling_method = scaling_method
        self.scaler = None
        self.feature_columns = None
        self.label_column = None

        if scaling_method == 'standard':
            self.scaler = StandardScaler()
        elif scaling_method == 'robust':
            self.scaler = RobustScaler()
        elif scaling_method != 'none':
            raise ValueError(f"Unknown scaling method: {scaling_method}")

    def identify_columns(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """
        Identify column types in the dataset

        Args:
            df: Input DataFrame

        Returns:
            Dictionary mapping column types to column names
        """
        # Find fraud label
        label_col = None
        for col in ['Class', 'isFraud', 'is_fraud', 'fraud', 'label']:
            if col in df.columns:
                label_col = col
                break

        if label_col is None:
            raise ValueError("No fraud label column found")

        self.label_column = label_col

        # Identify feature types
        feature_cols = [col for col in df.columns if col != label_col]

        time_cols = [col for col in feature_cols if 'time' in col.lower()]
        amount_cols = [col for col in feature_cols if 'amount' in col.lower()]

        # PCA features (V1, V2, etc.)
        pca_cols = [col for col in feature_cols
                    if col.startswith('V') and col[1:].isdigit()]

        # Other numeric features
        other_cols = [col for col in feature_cols
                     if col not in time_cols + amount_cols + pca_cols]

        self.feature_columns = feature_cols

        return {
            'label': [label_col],
            'time': time_cols,
            'amount': amount_cols,
            'pca': pca_cols,
            'other': other_cols,
            'all_features': feature_cols
        }

    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create additional features for fraud detection

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with additional features
        """
        df = df.copy()

        # Time-based features
        if 'Time' in df.columns:
            # Normalize time to hours
            df['Hour'] = (df['Time'] / 3600) % 24
            df['Day'] = (df['Time'] / (3600 * 24)).astype(int)

            # Cyclical encoding for hour
            df['Hour_sin'] = np.sin(2 * np.pi * df['Hour'] / 24)
            df['Hour_cos'] = np.cos(2 * np.pi * df['Hour'] / 24)

        # Amount-based features
        if 'Amount' in df.columns:
            # Log transform (with small constant for zeros)
            df['Amount_log'] = np.log1p(df['Amount'])

            # Amount bins
            df['Amount_bin'] = pd.cut(
                df['Amount'],
                bins=[0, 10, 50, 100, 500, np.inf],
                labels=['micro', 'small', 'medium', 'large', 'xlarge']
            ).astype(str)

            # One-hot encode amount bins
            amount_dummies = pd.get_dummies(df['Amount_bin'], prefix='Amount')
            df = pd.concat([df, amount_dummies], axis=1)
            df = df.drop('Amount_bin', axis=1)

        return df

    def preprocess(
        self,
        df: pd.DataFrame,
        fit: bool = True,
        engineer: bool = True
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Full preprocessing pipeline

        Args:
            df: Input DataFrame
            fit: Whether to fit the scaler (True for training data)
            engineer: Whether to engineer new features

        Returns:
            Tuple of (X, y) - features and labels
        """
        df = df.copy()

        # Identify columns
        col_types = self.identify_columns(df)

        # Engineer features
        if engineer:
            df = self.engineer_features(df)
            # Update feature columns after engineering
            self.feature_columns = [col for col in df.columns
                                   if col != self.label_column]

        # Extract features and labels
        X = df[self.feature_columns].copy()
        y = df[self.label_column].copy()

        # Handle missing values
        X = X.fillna(X.median())

        # Scale features
        if self.scaler is not None:
            if fit:
                X_scaled = self.scaler.fit_transform(X)
                logger.info(f"Fitted scaler on {len(X)} samples")
            else:
                X_scaled = self.scaler.transform(X)

            X = pd.DataFrame(X_scaled, columns=X.columns, index=X.index)

        return X, y

    def save(self, filepath: str):
        """Save preprocessor state"""
        state = {
            'scaling_method': self.scaling_method,
            'scaler': self.scaler,
            'feature_columns': self.feature_columns,
            'label_column': self.label_column
        }

        with open(filepath, 'wb') as f:
            pickle.dump(state, f)

        logger.info(f"Saved preprocessor to {filepath}")

    @classmethod
    def load(cls, filepath: str) -> 'FraudDataPreprocessor':
        """Load preprocessor state"""
        with open(filepath, 'rb') as f:
            state = pickle.load(f)

        preprocessor = cls(scaling_method=state['scaling_method'])
        preprocessor.scaler = state['scaler']
        preprocessor.feature_columns = state['feature_columns']
        preprocessor.label_column = state['label_column']

        logger.info(f"Loaded preprocessor from {filepath}")
        return preprocessor


def prepare_train_test_data(
    df: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = 42,
    scaling_method: str = 'standard',
    engineer_features: bool = True
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, FraudDataPreprocessor]:
    """
    Convenience function to prepare train/test data

    Args:
        df: Raw DataFrame
        test_size: Fraction for test set
        random_state: Random seed
        scaling_method: Scaling method to use
        engineer_features: Whether to engineer features

    Returns:
        Tuple of (X_train, X_test, y_train, y_test, preprocessor)
    """
    # Find label column
    label_col = None
    for col in ['Class', 'isFraud', 'is_fraud', 'fraud']:
        if col in df.columns:
            label_col = col
            break

    if label_col is None:
        raise ValueError("No fraud label column found")

    # Split data
    train_df, test_df = train_test_split(
        df,
        test_size=test_size,
        random_state=random_state,
        stratify=df[label_col]
    )

    # Initialize preprocessor
    preprocessor = FraudDataPreprocessor(scaling_method=scaling_method)

    # Preprocess train data (fit scaler)
    X_train, y_train = preprocessor.preprocess(
        train_df,
        fit=True,
        engineer=engineer_features
    )

    # Preprocess test data (transform only)
    X_test, y_test = preprocessor.preprocess(
        test_df,
        fit=False,
        engineer=engineer_features
    )

    logger.info(f"Prepared data: {len(X_train)} train, {len(X_test)} test")
    logger.info(f"Features: {X_train.shape[1]} columns")
    logger.info(f"Fraud rate - Train: {y_train.mean():.4f}, Test: {y_test.mean():.4f}")

    return X_train, X_test, y_train, y_test, preprocessor


def save_processed_data(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    output_dir: str = "data/processed"
):
    """
    Save processed data to disk

    Args:
        X_train: Training features
        X_test: Test features
        y_train: Training labels
        y_test: Test labels
        output_dir: Directory to save processed data
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Save as parquet for efficiency
    X_train.to_parquet(output_path / "X_train.parquet")
    X_test.to_parquet(output_path / "X_test.parquet")
    y_train.to_frame('label').to_parquet(output_path / "y_train.parquet")
    y_test.to_frame('label').to_parquet(output_path / "y_test.parquet")

    logger.info(f"Saved processed data to {output_path}")

    # Also save as CSV for easy inspection
    X_train.to_csv(output_path / "X_train.csv", index=False)
    y_train.to_frame('label').to_csv(output_path / "y_train.csv", index=False)

    logger.info(f"Saved CSV samples for inspection")


def load_processed_data(
    data_dir: str = "data/processed"
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Load processed data from disk

    Args:
        data_dir: Directory containing processed data

    Returns:
        Tuple of (X_train, X_test, y_train, y_test)
    """
    data_path = Path(data_dir)

    X_train = pd.read_parquet(data_path / "X_train.parquet")
    X_test = pd.read_parquet(data_path / "X_test.parquet")
    y_train = pd.read_parquet(data_path / "y_train.parquet")['label']
    y_test = pd.read_parquet(data_path / "y_test.parquet")['label']

    logger.info(f"Loaded processed data from {data_path}")
    logger.info(f"Train: {len(X_train)}, Test: {len(X_test)}")

    return X_train, X_test, y_train, y_test
