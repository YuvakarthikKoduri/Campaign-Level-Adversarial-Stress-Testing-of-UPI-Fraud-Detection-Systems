"""
Training script for baseline XGBoost fraud detector.

This script:
1. Loads processed data
2. Splits into train/test sets
3. Handles class imbalance using SMOTE
4. Trains XGBoost classifier
5. Evaluates model performance
6. Saves trained model and metrics
"""

import sys
import json
import pickle
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    classification_report,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    roc_curve
)
import xgboost as xgb
from imblearn.over_sampling import SMOTE

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.detectors.baseline import BaselineDetector


def load_processed_data(data_path: str) -> pd.DataFrame:
    """Load processed dataset."""
    print(f"Loading data from {data_path}")

    # Try multiple formats
    path = Path(data_path)

    if path.suffix == '.csv':
        df = pd.read_csv(data_path)
    elif path.suffix == '.parquet':
        df = pd.read_parquet(data_path)
    elif path.suffix == '.pkl':
        df = pd.read_pickle(data_path)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")

    print(f"Loaded {len(df)} transactions")
    print(f"Fraud rate: {df['is_fraud'].mean():.2%}")

    return df


def prepare_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, list]:
    """
    Prepare features and target for training.

    Returns:
        X: Feature DataFrame
        y: Target Series
        feature_names: List of feature names
    """
    # Separate features and target
    target_col = 'is_fraud'

    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataset")

    y = df[target_col]

    # Remove target and non-feature columns
    drop_cols = [target_col, 'transaction_id'] if 'transaction_id' in df.columns else [target_col]
    X = df.drop(columns=drop_cols)

    # Get feature names
    feature_names = X.columns.tolist()

    print(f"\nFeatures: {len(feature_names)}")
    print(f"Target distribution:")
    print(y.value_counts())

    return X, y, feature_names


def handle_class_imbalance(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    method: str = 'smote',
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Handle class imbalance using SMOTE or class weights.

    Args:
        X_train: Training features
        y_train: Training target
        method: 'smote' or 'weights'
        random_state: Random seed

    Returns:
        Resampled X_train and y_train (if SMOTE) or original (if weights)
    """
    fraud_rate = y_train.mean()
    print(f"\nOriginal fraud rate: {fraud_rate:.2%}")
    print(f"Class distribution: {y_train.value_counts().to_dict()}")

    if method == 'smote':
        print("\nApplying SMOTE...")

        # Use SMOTE to oversample minority class
        smote = SMOTE(random_state=random_state, k_neighbors=5)
        X_resampled, y_resampled = smote.fit_resample(X_train, y_train)

        print(f"After SMOTE:")
        print(f"  Samples: {len(X_resampled)} (was {len(X_train)})")
        print(f"  Fraud rate: {y_resampled.mean():.2%}")
        print(f"  Class distribution: {pd.Series(y_resampled).value_counts().to_dict()}")

        return pd.DataFrame(X_resampled, columns=X_train.columns), pd.Series(y_resampled)

    elif method == 'weights':
        print("\nUsing class weights (no resampling)")
        return X_train, y_train

    else:
        raise ValueError(f"Unknown method: {method}")


def train_xgboost(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    use_scale_pos_weight: bool = False
) -> xgb.XGBClassifier:
    """
    Train XGBoost classifier.

    Args:
        X_train: Training features
        y_train: Training target
        X_val: Validation features
        y_val: Validation target
        use_scale_pos_weight: Whether to use scale_pos_weight for imbalance

    Returns:
        Trained XGBoost model
    """
    print("\nTraining XGBoost classifier...")

    # Calculate scale_pos_weight if needed
    scale_pos_weight = 1.0
    if use_scale_pos_weight:
        scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
        print(f"Using scale_pos_weight: {scale_pos_weight:.2f}")

    # XGBoost parameters
    params = {
        'max_depth': 6,
        'learning_rate': 0.1,
        'n_estimators': 200,
        'objective': 'binary:logistic',
        'eval_metric': 'auc',
        'scale_pos_weight': scale_pos_weight,
        'random_state': 42,
        'n_jobs': -1,
        'tree_method': 'hist',
        'early_stopping_rounds': 20
    }

    # Initialize model
    model = xgb.XGBClassifier(**params)

    # Train with early stopping
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False
    )

    print(f"Training complete. Best iteration: {model.best_iteration}")

    return model


def evaluate_model(
    model: xgb.XGBClassifier,
    X_test: pd.DataFrame,
    y_test: pd.Series
) -> Dict:
    """
    Evaluate model performance.

    Returns:
        Dictionary with evaluation metrics
    """
    print("\nEvaluating model...")

    # Predictions
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]

    # Calculate metrics
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_pred_proba)

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()

    metrics = {
        'precision': float(precision),
        'recall': float(recall),
        'f1_score': float(f1),
        'roc_auc': float(roc_auc),
        'confusion_matrix': {
            'true_negatives': int(tn),
            'false_positives': int(fp),
            'false_negatives': int(fn),
            'true_positives': int(tp)
        },
        'test_samples': int(len(y_test)),
        'fraud_rate': float(y_test.mean())
    }

    # Print results
    print("\n" + "="*50)
    print("BASELINE MODEL EVALUATION")
    print("="*50)
    print(f"\nPrecision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"F1 Score:  {f1:.4f}")
    print(f"ROC-AUC:   {roc_auc:.4f}")

    print(f"\nConfusion Matrix:")
    print(f"  TN: {tn:6d}  FP: {fp:6d}")
    print(f"  FN: {fn:6d}  TP: {tp:6d}")

    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['Legitimate', 'Fraud']))

    return metrics


def save_model_and_metrics(
    model: xgb.XGBClassifier,
    feature_names: list,
    scaler: StandardScaler,
    metrics: Dict,
    model_path: str,
    metrics_path: str
) -> None:
    """Save trained model and evaluation metrics."""

    # Save model using BaselineDetector format
    detector = BaselineDetector()
    detector.model = model
    detector.feature_names = feature_names
    detector.scaler = scaler

    detector.save_model(model_path)

    # Save metrics
    Path(metrics_path).parent.mkdir(parents=True, exist_ok=True)

    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)

    print(f"\nMetrics saved to {metrics_path}")


def main():
    """Main training pipeline."""

    # Paths
    data_path = project_root / 'data' / 'processed' / 'transactions.csv'
    model_path = project_root / 'models' / 'baseline_xgboost.pkl'
    metrics_path = project_root / 'results' / 'metrics' / 'baseline_evaluation.json'

    # Check if data exists
    if not data_path.exists():
        # Try alternative formats
        for ext in ['.parquet', '.pkl']:
            alt_path = data_path.with_suffix(ext)
            if alt_path.exists():
                data_path = alt_path
                break
        else:
            raise FileNotFoundError(
                f"Processed data not found. Expected at: {data_path}\n"
                "Please run data preparation first."
            )

    # Load data
    df = load_processed_data(str(data_path))

    # Prepare features
    X, y, feature_names = prepare_features(df)

    # Split data
    print("\nSplitting data (80/20 train/test)...")
    X_train_full, X_test, y_train_full, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Further split train into train/val for early stopping
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_full, y_train_full, test_size=0.2, random_state=42, stratify=y_train_full
    )

    print(f"Train: {len(X_train)} samples")
    print(f"Val:   {len(X_val)} samples")
    print(f"Test:  {len(X_test)} samples")

    # Scale features
    print("\nScaling features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)

    # Convert back to DataFrames
    X_train_scaled = pd.DataFrame(X_train_scaled, columns=feature_names)
    X_val_scaled = pd.DataFrame(X_val_scaled, columns=feature_names)
    X_test_scaled = pd.DataFrame(X_test_scaled, columns=feature_names)

    # Handle class imbalance
    X_train_resampled, y_train_resampled = handle_class_imbalance(
        X_train_scaled, y_train, method='smote'
    )

    # Train model
    model = train_xgboost(
        X_train_resampled, y_train_resampled,
        X_val_scaled, y_val,
        use_scale_pos_weight=False  # Already handled by SMOTE
    )

    # Evaluate
    metrics = evaluate_model(model, X_test_scaled, y_test)

    # Save
    save_model_and_metrics(
        model, feature_names, scaler, metrics,
        str(model_path), str(metrics_path)
    )

    print("\n" + "="*50)
    print("TRAINING COMPLETE")
    print("="*50)
    print(f"\nModel saved to: {model_path}")
    print(f"Metrics saved to: {metrics_path}")

    return model, metrics


if __name__ == '__main__':
    main()
