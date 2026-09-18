"""
Lightweight training script for laptops without GPU.

This version reduces memory usage and training time for prototype development.
"""
import sys
import json
import pickle
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
)
import xgboost as xgb
from imblearn.over_sampling import SMOTE

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.loader import FraudDataLoader
from src.detectors.baseline import BaselineDetector


def train_lightweight_model(
    sample_size: int = 50000,  # Use 50K instead of 284K for faster training
    test_size: float = 0.2,
    random_state: int = 42
):
    """
    Train a lightweight XGBoost model suitable for CPU laptops.

    Memory usage: ~1-2 GB RAM
    Training time: 5-10 minutes on modest laptop

    Args:
        sample_size: Number of transactions to use (50K is good for prototyping)
        test_size: Fraction for test set
        random_state: Random seed
    """
    print("="*60)
    print("LIGHTWEIGHT FRAUD DETECTOR TRAINING")
    print("Optimized for laptops without GPU")
    print("="*60)
    print()

    # Load data with limited sample size
    print(f"Loading {sample_size:,} transactions...")
    loader = FraudDataLoader()
    df = loader.load_raw(nrows=sample_size)

    print(f"Loaded: {len(df):,} transactions")
    fraud_count = df['Class'].sum()
    print(f"Fraud cases: {fraud_count} ({fraud_count/len(df)*100:.2f}%)")
    print()

    # Prepare features
    print("Preparing features...")
    feature_cols = [col for col in df.columns if col not in ['Class', 'Time']]
    X = df[feature_cols].values
    y = df['Class'].values

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    print(f"Train: {len(X_train):,}, Test: {len(X_test):,}")
    print()

    # Scale features
    print("Scaling features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Handle imbalance with SMOTE (limited to avoid memory issues)
    print("Applying SMOTE for class balance...")
    print("(This may take 2-3 minutes...)")
    smote = SMOTE(random_state=random_state, k_neighbors=3)
    X_train_balanced, y_train_balanced = smote.fit_resample(X_train_scaled, y_train)

    print(f"After SMOTE: {len(X_train_balanced):,} samples")
    print(f"Fraud: {y_train_balanced.sum():,}, Normal: {(~y_train_balanced.astype(bool)).sum():,}")
    print()

    # Train XGBoost with CPU-friendly parameters
    print("Training XGBoost classifier...")
    print("(CPU only - will take 3-5 minutes)")
    print()

    model = xgb.XGBClassifier(
        n_estimators=100,          # Reduced from 300
        max_depth=4,               # Reduced from 6
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=random_state,
        tree_method='hist',        # Faster histogram-based
        n_jobs=-1,                 # Use all CPU cores
        verbosity=1
    )

    model.fit(
        X_train_balanced,
        y_train_balanced,
        eval_set=[(X_test_scaled, y_test)],
        verbose=True
    )

    print()
    print("Training complete!")
    print()

    # Evaluate
    print("Evaluating model...")
    y_pred = model.predict(X_test_scaled)
    y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]

    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_pred_proba)

    print(f"Precision: {precision:.3f}")
    print(f"Recall:    {recall:.3f}")
    print(f"F1 Score:  {f1:.3f}")
    print(f"ROC-AUC:   {roc_auc:.3f}")
    print()

    cm = confusion_matrix(y_test, y_pred)
    print("Confusion Matrix:")
    print(f"  TN: {cm[0,0]:5d}  |  FP: {cm[0,1]:5d}")
    print(f"  FN: {cm[1,0]:5d}  |  TP: {cm[1,1]:5d}")
    print()

    # Save model
    print("Saving model...")
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)

    detector = BaselineDetector()
    detector.model = model
    detector.scaler = scaler
    detector.feature_names = feature_cols

    model_path = models_dir / "baseline_xgboost.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump(detector, f)

    print(f"Model saved to: {model_path}")
    print(f"Model size: {model_path.stat().st_size / 1024:.1f} KB")
    print()

    # Save metrics
    results_dir = Path("results/metrics")
    results_dir.mkdir(parents=True, exist_ok=True)

    metrics = {
        "sample_size": sample_size,
        "training_samples": len(X_train_balanced),
        "test_samples": len(X_test),
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1),
        "roc_auc": float(roc_auc),
        "confusion_matrix": cm.tolist()
    }

    metrics_path = results_dir / "baseline_evaluation.json"
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)

    print(f"Metrics saved to: {metrics_path}")
    print()
    print("="*60)
    print("SUCCESS! Model ready for use.")
    print("="*60)
    print()
    print("Next steps:")
    print("  1. python demo.py")
    print("  2. python run_experiment.py --scenario S4")
    print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--sample-size',
        type=int,
        default=50000,
        help='Number of transactions to use (default: 50000)'
    )
    parser.add_argument(
        '--full',
        action='store_true',
        help='Use full dataset (284K transactions, slower)'
    )

    args = parser.parse_args()

    if args.full:
        sample_size = None  # Load all data
        print("WARNING: Using full dataset will take longer and use more RAM")
    else:
        sample_size = args.sample_size

    train_lightweight_model(sample_size=sample_size)
