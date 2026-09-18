#!/usr/bin/env python3
"""
Train Random Forest baseline detector for comparison with XGBoost.

Requirements:
- Same dataset as XGBoost
- Same features
- Same train/test split
- Same evaluation protocol
- Same prediction interface
"""

import sys
import pickle
from pathlib import Path
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.detectors.baseline import BaselineDetector
from train_upi_model import generate_synthetic_upi_data


def main():
    print("="*70)
    print("TRAINING RANDOM FOREST BASELINE DETECTOR")
    print("="*70)

    # Generate same synthetic data
    print("\nGenerating synthetic UPI data...")
    df = generate_synthetic_upi_data(50000)

    feature_cols = ['amount', 'hour_of_day', 'velocity_1h', 'is_new_vpa']
    X = df[feature_cols].values
    y = df['is_fraud'].values

    # Same split as XGBoost (seed=42)
    print("Splitting data (same seed as XGBoost)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"Train samples: {len(X_train)}")
    print(f"Test samples: {len(X_test)}")
    print(f"Fraud rate: {y.mean():.1%}")

    # Train Random Forest
    print("\nTraining Random Forest...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=8,
        min_samples_split=10,
        min_samples_leaf=5,
        random_state=42,
        n_jobs=-1
    )

    model.fit(X_train, y_train)

    # Evaluate
    print("\nEvaluating...")
    from sklearn.metrics import (
        roc_auc_score, precision_score, recall_score,
        f1_score, confusion_matrix
    )

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_prob)
    cm = confusion_matrix(y_test, y_pred)

    print(f"\nResults:")
    print(f"  Precision: {precision:.3f}")
    print(f"  Recall:    {recall:.3f}")
    print(f"  F1 Score:  {f1:.3f}")
    print(f"  ROC-AUC:   {roc_auc:.3f}")
    print(f"\nConfusion Matrix:")
    print(f"  TN: {cm[0,0]:5d}  FP: {cm[0,1]:5d}")
    print(f"  FN: {cm[1,0]:5d}  TP: {cm[1,1]:5d}")

    # Feature importance
    print(f"\nFeature Importance:")
    for feat, imp in sorted(zip(feature_cols, model.feature_importances_),
                           key=lambda x: x[1], reverse=True):
        print(f"  {feat:15s}: {imp:.3f}")

    # Save model
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)

    detector = BaselineDetector()
    detector.model = model
    detector.feature_names = feature_cols
    detector.scaler = None  # Random Forest doesn't need scaling

    model_path = models_dir / "baseline_random_forest.pkl"
    with open(model_path, "wb") as f:
        pickle.dump({
            'model': model,
            'feature_names': feature_cols,
            'scaler': None
        }, f)

    print(f"\n✓ Model saved to {model_path}")

    # Save evaluation results
    results_dir = Path("results/metrics")
    results_dir.mkdir(parents=True, exist_ok=True)

    eval_results = {
        'model': 'RandomForest',
        'precision': float(precision),
        'recall': float(recall),
        'f1_score': float(f1),
        'roc_auc': float(roc_auc),
        'confusion_matrix': cm.tolist(),
        'test_samples': len(X_test),
        'fraud_rate': float(y_test.mean()),
        'timestamp': datetime.now().isoformat()
    }

    import json
    with open(results_dir / "random_forest_evaluation.json", 'w') as f:
        json.dump(eval_results, f, indent=2)

    print(f"✓ Evaluation saved to results/metrics/random_forest_evaluation.json")

    # Compare with XGBoost if available
    xgb_eval_path = results_dir / "baseline_evaluation.json"
    if xgb_eval_path.exists():
        with open(xgb_eval_path) as f:
            xgb_results = json.load(f)

        print(f"\n{'='*70}")
        print("COMPARISON: Random Forest vs XGBoost")
        print(f"{'='*70}")
        print(f"{'Metric':<20} {'Random Forest':<15} {'XGBoost':<15} {'Difference'}")
        print(f"{'-'*70}")
        print(f"{'Precision':<20} {precision:>14.3f} {xgb_results['precision']:>14.3f}  {precision - xgb_results['precision']:+.3f}")
        print(f"{'Recall':<20} {recall:>14.3f} {xgb_results['recall']:>14.3f}  {recall - xgb_results['recall']:+.3f}")
        print(f"{'F1 Score':<20} {f1:>14.3f} {xgb_results['f1_score']:>14.3f}  {f1 - xgb_results['f1_score']:+.3f}")
        print(f"{'ROC-AUC':<20} {roc_auc:>14.3f} {xgb_results['roc_auc']:>14.3f}  {roc_auc - xgb_results['roc_auc']:+.3f}")
        print(f"{'='*70}")


if __name__ == "__main__":
    main()
