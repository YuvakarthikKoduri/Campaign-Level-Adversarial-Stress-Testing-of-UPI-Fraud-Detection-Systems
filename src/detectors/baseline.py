"""
Baseline fraud detector using XGBoost.

This module provides a simple interface for fraud detection with trained XGBoost models.
"""

import pickle
import numpy as np
import pandas as pd
from typing import Dict, Union, Optional
from pathlib import Path
import warnings

warnings.filterwarnings('ignore')


class BaselineDetector:
    """
    Baseline fraud detector using XGBoost classifier.

    Provides a clean interface for fraud detection with methods for:
    - predict: Returns fraud probability [0-1]
    - risk_score: Returns risk score [0-1] (alias for predict)
    """

    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the baseline detector.

        Args:
            model_path: Path to the trained model file. If None, model must be loaded later.
        """
        self.model = None
        self.feature_names = None
        self.scaler = None
        self.model_path = model_path

        if model_path and Path(model_path).exists():
            self.load_model(model_path)

    def load_model(self, model_path: str) -> None:
        """
        Load a trained model from disk.

        Args:
            model_path: Path to the pickled model file
        """
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)

        self.model = model_data['model']
        self.feature_names = model_data['feature_names']
        self.scaler = model_data.get('scaler', None)

        print(f"Model loaded from {model_path}")
        print(f"Features: {len(self.feature_names)}")

    def save_model(self, model_path: str) -> None:
        """
        Save the trained model to disk.

        Args:
            model_path: Path where the model should be saved
        """
        model_data = {
            'model': self.model,
            'feature_names': self.feature_names,
            'scaler': self.scaler
        }

        Path(model_path).parent.mkdir(parents=True, exist_ok=True)

        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)

        print(f"Model saved to {model_path}")

    def _prepare_features(self, transaction: Union[Dict, pd.DataFrame]) -> np.ndarray:
        """
        Convert transaction data to model input format.

        Args:
            transaction: Either a dict with feature values or a DataFrame

        Returns:
            Numpy array ready for model prediction
        """
        if self.model is None:
            raise ValueError("Model not loaded. Call load_model() or train() first.")

        # Convert dict to DataFrame if needed
        if isinstance(transaction, dict):
            transaction = pd.DataFrame([transaction])

        # Ensure all required features are present
        missing_features = set(self.feature_names) - set(transaction.columns)
        if missing_features:
            raise ValueError(f"Missing features: {missing_features}")

        # Select and order features
        X = transaction[self.feature_names].values

        # Apply scaling if scaler is available
        if self.scaler is not None:
            X = self.scaler.transform(X)

        return X

    def predict(self, transaction: Union[Dict, pd.DataFrame]) -> float:
        """
        Predict fraud probability for a transaction.

        Args:
            transaction: Transaction data as dict or DataFrame

        Returns:
            Fraud probability as float [0-1]
        """
        X = self._prepare_features(transaction)

        # Get probability of fraud class (class 1)
        prob = self.model.predict_proba(X)[:, 1]

        return float(prob[0]) if len(prob) == 1 else prob

    def risk_score(self, transaction: Union[Dict, pd.DataFrame]) -> float:
        """
        Calculate risk score for a transaction.

        This is an alias for predict() that returns the fraud probability.

        Args:
            transaction: Transaction data as dict or DataFrame

        Returns:
            Risk score as float [0-1]
        """
        return self.predict(transaction)

    def predict_batch(self, transactions: pd.DataFrame) -> np.ndarray:
        """
        Predict fraud probabilities for multiple transactions.

        Args:
            transactions: DataFrame with transaction features

        Returns:
            Array of fraud probabilities
        """
        X = self._prepare_features(transactions)
        probs = self.model.predict_proba(X)[:, 1]
        return probs

    def classify(self, transaction: Union[Dict, pd.DataFrame], threshold: float = 0.5) -> bool:
        """
        Classify transaction as fraud or legitimate.

        Args:
            transaction: Transaction data as dict or DataFrame
            threshold: Decision threshold (default 0.5)

        Returns:
            True if fraud, False if legitimate
        """
        prob = self.predict(transaction)
        return prob >= threshold


def load_detector(model_path: str) -> BaselineDetector:
    """
    Convenience function to load a trained detector.

    Args:
        model_path: Path to the trained model file

    Returns:
        Loaded BaselineDetector instance
    """
    return BaselineDetector(model_path=model_path)
