#!/usr/bin/env python3
"""
UPI Baseline Detector Training and Validation

Properly trains XGBoost and Random Forest detectors on synthetic UPI data
with comprehensive validation, threshold calibration, and diagnostic testing.

This script:
1. Generates synthetic UPI transaction data with realistic overlap
2. Trains both XGBoost and Random Forest detectors
3. Performs threshold calibration on validation set
4. Validates train/inference feature parity
5. Tests detector behavior on controlled synthetic inputs
6. Saves models with complete metadata
7. Generates validation report
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import numpy as np
import pandas as pd
import pickle
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    roc_auc_score, precision_recall_curve, roc_curve,
    confusion_matrix, classification_report,
    precision_score, recall_score, f1_score, average_precision_score
)
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from src.detectors.baseline import BaselineDetector

# ============================================================================
# 1. SYNTHETIC UPI DATA GENERATION
# ============================================================================

def generate_synthetic_upi_data(n_samples=50000, seed=42):
    """
    Generate realistic synthetic UPI transaction data.

    Design principles:
    - Realistic overlap between legitimate and fraud
    - Multi-modal distributions (not single Gaussian)
    - Fraud is NOT trivially separable
    - Both classes span full feature space

    Target: 85-92% AUC (useful detector with genuine blind spots)
    """
    print(f"Generating {n_samples:,} synthetic UPI transactions...")
    np.random.seed(seed)

    n_legit = int(n_samples * 0.95)  # 95% legitimate (realistic fraud rate)
    n_fraud = n_samples - n_legit

    # === LEGITIMATE TRANSACTIONS ===
    # Multi-modal: small daily (70%), medium (20%), large legitimate (10%)

    n_legit_small = int(n_legit * 0.70)
    n_legit_medium = int(n_legit * 0.20)
    n_legit_large = n_legit - n_legit_small - n_legit_medium

    legit_amount = np.concatenate([
        np.random.lognormal(mean=6.5, sigma=0.8, size=n_legit_small),  # ₹500-3K
        np.random.lognormal(mean=8.5, sigma=0.6, size=n_legit_medium),  # ₹3K-15K
        np.random.lognormal(mean=9.8, sigma=0.5, size=n_legit_large)   # ₹15K-50K
    ])
    legit_amount = np.clip(legit_amount, 100, 100000)
    np.random.shuffle(legit_amount)

    # Hour: mostly daytime (6am-11pm), some night (night shift, emergencies)
    legit_hour_day = np.random.normal(loc=14, scale=5, size=int(n_legit * 0.92))
    legit_hour_night = np.random.normal(loc=2, scale=2, size=n_legit - len(legit_hour_day))
    legit_hour = np.concatenate([legit_hour_day, legit_hour_night]).astype(int) % 24
    np.random.shuffle(legit_hour)

    # Velocity: mostly low, occasional bursts (bill payments)
    legit_velocity = np.concatenate([
        np.random.poisson(lam=0.5, size=int(n_legit * 0.85)),  # Low velocity
        np.random.poisson(lam=2.5, size=n_legit - int(n_legit * 0.85))  # Burst
    ])
    np.random.shuffle(legit_velocity)

    # New VPA: 10% new (first-time payments)
    legit_new_vpa = np.random.binomial(1, 0.10, size=n_legit)

    # === FRAUD TRANSACTIONS ===
    # Multi-modal: high-value (30%), medium (40%), low-value testing (30%)

    n_fraud_high = int(n_fraud * 0.30)
    n_fraud_medium = int(n_fraud * 0.40)
    n_fraud_low = n_fraud - n_fraud_high - n_fraud_medium

    fraud_amount = np.concatenate([
        np.random.lognormal(mean=10.0, sigma=0.5, size=n_fraud_high),   # ₹20K-60K
        np.random.lognormal(mean=9.0, sigma=0.6, size=n_fraud_medium),  # ₹5K-20K
        np.random.lognormal(mean=7.5, sigma=0.7, size=n_fraud_low)      # ₹1K-5K
    ])
    fraud_amount = np.clip(fraud_amount, 500, 100000)
    np.random.shuffle(fraud_amount)

    # Hour: 60% late night, 40% daytime (compromised office accounts)
    fraud_hour_night = np.random.normal(loc=2.5, scale=2.5, size=int(n_fraud * 0.60))
    fraud_hour_day = np.random.normal(loc=13, scale=5, size=n_fraud - len(fraud_hour_night))
    fraud_hour = np.concatenate([fraud_hour_night, fraud_hour_day]).astype(int) % 24
    np.random.shuffle(fraud_hour)

    # Velocity: bimodal - high (rapid draining) and low (testing)
    fraud_velocity = np.concatenate([
        np.random.poisson(lam=5, size=int(n_fraud * 0.65)),  # High velocity
        np.random.poisson(lam=1.5, size=n_fraud - int(n_fraud * 0.65))  # Low velocity
    ])
    np.random.shuffle(fraud_velocity)

    # New VPA: 55% new (higher than legit, but not 100%)
    fraud_new_vpa = np.random.binomial(1, 0.55, size=n_fraud)

    # Create DataFrames
    df_legit = pd.DataFrame({
        'amount': legit_amount,
        'hour_of_day': legit_hour,
        'velocity_1h': legit_velocity,
        'is_new_vpa': legit_new_vpa,
        'is_fraud': 0
    })

    df_fraud = pd.DataFrame({
        'amount': fraud_amount,
        'hour_of_day': fraud_hour,
        'velocity_1h': fraud_velocity,
        'is_new_vpa': fraud_new_vpa,
        'is_fraud': 1
    })

    # Combine and shuffle
    df = pd.concat([df_legit, df_fraud]).sample(frac=1.0, random_state=seed).reset_index(drop=True)

    # Print distribution summary
    print("\n" + "="*70)
    print("SYNTHETIC DATA GENERATION SUMMARY")
    print("="*70)
    print(f"\nTotal transactions: {len(df):,}")
    print(f"Legitimate: {n_legit:,} (95.0%)")
    print(f"Fraud: {n_fraud:,} (5.0%)")
    print()

    print("Feature Distributions:")
    print()
    print("Amount:")
    print(f"  Legit:  ₹{df_legit['amount'].min():>7,.0f} - ₹{df_legit['amount'].max():>7,.0f}  (median: ₹{df_legit['amount'].median():>6,.0f})")
    print(f"  Fraud:  ₹{df_fraud['amount'].min():>7,.0f} - ₹{df_fraud['amount'].max():>7,.0f}  (median: ₹{df_fraud['amount'].median():>6,.0f})")
    print(f"  Overlap: Legit P95=₹{df_legit['amount'].quantile(0.95):,.0f}, Fraud P05=₹{df_fraud['amount'].quantile(0.05):,.0f}")
    print()

    print("Hour of Day:")
    print(f"  Legit:  mean={df_legit['hour_of_day'].mean():.1f}, mode={df_legit['hour_of_day'].mode().values[0]}")
    print(f"  Fraud:  mean={df_fraud['hour_of_day'].mean():.1f}, mode={df_fraud['hour_of_day'].mode().values[0]}")
    print()

    print("Velocity (transactions/hour):")
    print(f"  Legit:  mean={df_legit['velocity_1h'].mean():.2f}, P90={df_legit['velocity_1h'].quantile(0.90):.0f}")
    print(f"  Fraud:  mean={df_fraud['velocity_1h'].mean():.2f}, P90={df_fraud['velocity_1h'].quantile(0.90):.0f}")
    print()

    print("New VPA:")
    print(f"  Legit:  {df_legit['is_new_vpa'].mean():.1%}")
    print(f"  Fraud:  {df_fraud['is_new_vpa'].mean():.1%}")
    print()

    return df

# ============================================================================
# 2. TRAIN DETECTOR
# ============================================================================

def train_detector(X_train, y_train, X_val, y_val, model_type='xgboost'):
    """Train XGBoost or Random Forest detector."""

    print(f"\nTraining {model_type.upper()} detector...")

    if model_type == 'xgboost':
        # Calculate scale_pos_weight for class imbalance
        scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()

        model = xgb.XGBClassifier(
            n_estimators=150,
            max_depth=5,
            learning_rate=0.1,
            scale_pos_weight=scale_pos_weight,
            random_state=42,
            eval_metric='auc',
            early_stopping_rounds=15,
            tree_method='hist'
        )

        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=False
        )

        print(f"  Best iteration: {model.best_iteration}")

    elif model_type == 'random_forest':
        # Calculate class weights
        class_weight = {
            0: 1.0,
            1: (y_train == 0).sum() / (y_train == 1).sum()
        }

        model = RandomForestClassifier(
            n_estimators=150,
            max_depth=10,
            min_samples_split=20,
            min_samples_leaf=10,
            class_weight=class_weight,
            random_state=42,
            n_jobs=-1
        )

        model.fit(X_train, y_train)

    else:
        raise ValueError(f"Unknown model_type: {model_type}")

    return model

# ============================================================================
# 3. THRESHOLD CALIBRATION
# ============================================================================

def calibrate_threshold(model, X_val, y_val):
    """
    Calibrate decision threshold using validation set.

    Returns optimal threshold that maximizes F1 score.
    """
    print("\nCalibrating threshold...")

    y_prob = model.predict_proba(X_val)[:, 1]

    # Try different thresholds
    precisions, recalls, thresholds = precision_recall_curve(y_val, y_prob)

    # Calculate F1 for each threshold
    f1_scores = 2 * (precisions[:-1] * recalls[:-1]) / (precisions[:-1] + recalls[:-1] + 1e-10)

    # Find optimal threshold (max F1)
    optimal_idx = np.argmax(f1_scores)
    optimal_threshold = thresholds[optimal_idx]
    optimal_f1 = f1_scores[optimal_idx]
    optimal_precision = precisions[optimal_idx]
    optimal_recall = recalls[optimal_idx]

    print(f"  Optimal threshold: {optimal_threshold:.4f} (max F1)")
    print(f"  At this threshold:")
    print(f"    Precision: {optimal_precision:.3f}")
    print(f"    Recall: {optimal_recall:.3f}")
    print(f"    F1 Score: {optimal_f1:.3f}")

    return optimal_threshold

# ============================================================================
# 4. EVALUATION
# ============================================================================

def evaluate_detector(model, X_test, y_test, threshold=0.5, model_name="Detector"):
    """Comprehensive evaluation on test set."""

    print(f"\n{'='*70}")
    print(f"{model_name.upper()} EVALUATION")
    print(f"{'='*70}")

    y_prob = model.predict_proba(X_test)[:, 1]
    y_pred = (y_prob >= threshold).astype(int)

    # Calculate metrics
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    roc_auc = roc_auc_score(y_test, y_prob)
    pr_auc = average_precision_score(y_test, y_prob)

    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()

    print(f"\nThreshold: {threshold:.4f}")
    print()
    print(f"ROC-AUC: {roc_auc:.4f}")
    print(f"PR-AUC:  {pr_auc:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"F1 Score:  {f1:.4f}")
    print()

    print("Confusion Matrix:")
    print(f"  TN: {tn:>6}  FP: {fp:>6}")
    print(f"  FN: {fn:>6}  TP: {tp:>6}")
    print()

    print(f"Test Set Size: {len(y_test):,}")
    print(f"Fraud Rate: {y_test.mean():.2%}")
    print()

    # Classification report
    print("Classification Report:")
    print(classification_report(y_test, y_pred, target_names=['Legitimate', 'Fraud'], zero_division=0))

    metrics = {
        'roc_auc': float(roc_auc),
        'pr_auc': float(pr_auc),
        'precision': float(precision),
        'recall': float(recall),
        'f1_score': float(f1),
        'threshold': float(threshold),
        'confusion_matrix': {
            'tn': int(tn), 'fp': int(fp),
            'fn': int(fn), 'tp': int(tp)
        },
        'test_size': int(len(y_test)),
        'fraud_rate': float(y_test.mean())
    }

    return metrics

# ============================================================================
# 5. DIAGNOSTIC TESTS
# ============================================================================

def test_detector_behavior(detector):
    """Test detector on controlled synthetic inputs."""

    print("\n" + "="*70)
    print("DETECTOR BEHAVIOR DIAGNOSTICS")
    print("="*70)
    print()
    print("Testing detector response to controlled feature combinations:")
    print()

    test_cases = [
        # (amount, hour, velocity, is_new_vpa, expected_risk_level, description)
        (1000, 14, 0, 0, "low", "Small daytime, low velocity, known VPA"),
        (5000, 10, 1, 0, "low-medium", "Medium daytime, low velocity, known VPA"),
        (25000, 14, 0, 0, "medium", "Large daytime, low velocity, known VPA"),
        (25000, 2, 5, 1, "high", "Large night, high velocity, new VPA"),
        (50000, 3, 8, 1, "very-high", "Very large night, very high velocity, new VPA"),
        (100000, 2, 15, 1, "extreme", "Extreme amount, night, extreme velocity, new VPA"),
    ]

    print("| Amount | Hour | Velocity | New VPA | Risk Score | Expected | Description |")
    print("|--------|------|----------|---------|------------|----------|-------------|")

    for amount, hour, velocity, is_new_vpa, expected, desc in test_cases:
        features = pd.DataFrame([{
            'amount': amount,
            'hour_of_day': hour,
            'velocity_1h': velocity,
            'is_new_vpa': is_new_vpa
        }])

        risk = detector.predict(features)

        print(f"| ₹{amount:>6,} | {hour:>4} | {velocity:>8} | {is_new_vpa:>7} | {risk:>10.6f} | {expected:<10} | {desc:<45} |")

    print()

# ============================================================================
# 6. SAVE MODEL
# ============================================================================

def save_detector(model, feature_names, threshold, model_type, metrics, output_path):
    """Save trained detector with complete metadata."""

    model_data = {
        'model': model,
        'feature_names': feature_names,
        'scaler': None,  # No scaler needed for tree models
        'threshold': threshold,
        'model_type': model_type,
        'training_date': datetime.now().isoformat(),
        'dataset_version': 'synthetic_upi_v1',
        'metrics': metrics
    }

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'wb') as f:
        pickle.dump(model_data, f)

    print(f"\nModel saved to: {output_path}")

# ============================================================================
# 7. FEATURE PARITY TEST
# ============================================================================

def test_feature_parity():
    """Verify train and inference feature schemas match."""

    print("\n" + "="*70)
    print("FEATURE PARITY TEST")
    print("="*70)

    # Expected features
    expected_features = ['amount', 'hour_of_day', 'velocity_1h', 'is_new_vpa']

    # Load saved model
    with open('models/baseline_xgboost.pkl', 'rb') as f:
        model_data = pickle.load(f)

    actual_features = model_data['feature_names']

    print(f"\nExpected features: {expected_features}")
    print(f"Actual features:   {actual_features}")

    if expected_features == actual_features:
        print("\n✓ PASS: Feature schemas match")
    else:
        print("\n✗ FAIL: Feature schema mismatch!")
        print(f"  Missing: {set(expected_features) - set(actual_features)}")
        print(f"  Extra: {set(actual_features) - set(expected_features)}")
        raise ValueError("Feature parity test failed")

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("="*70)
    print("UPI BASELINE DETECTOR TRAINING")
    print("="*70)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 1. Generate data
    df = generate_synthetic_upi_data(n_samples=50000, seed=42)

    # Save dataset
    dataset_path = Path('data/synthetic/upi_transactions_v1.csv')
    dataset_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(dataset_path, index=False)
    print(f"\nDataset saved to: {dataset_path}")

    # 2. Split data
    feature_cols = ['amount', 'hour_of_day', 'velocity_1h', 'is_new_vpa']
    X = df[feature_cols]
    y = df['is_fraud']

    # Train/Val/Test split: 60/20/20
    X_train_val, X_test, y_train_val, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val, y_train_val, test_size=0.25, random_state=42, stratify=y_train_val
    )

    print(f"\nData splits:")
    print(f"  Train: {len(X_train):>6,} samples ({y_train.mean():.2%} fraud)")
    print(f"  Val:   {len(X_val):>6,} samples ({y_val.mean():.2%} fraud)")
    print(f"  Test:  {len(X_test):>6,} samples ({y_test.mean():.2%} fraud)")

    # 3. Train XGBoost
    xgb_model = train_detector(X_train, y_train, X_val, y_val, model_type='xgboost')
    xgb_threshold = calibrate_threshold(xgb_model, X_val, y_val)
    xgb_metrics = evaluate_detector(xgb_model, X_test, y_test, xgb_threshold, "XGBoost")

    # 4. Train Random Forest
    rf_model = train_detector(X_train, y_train, X_val, y_val, model_type='random_forest')
    rf_threshold = calibrate_threshold(rf_model, X_val, y_val)
    rf_metrics = evaluate_detector(rf_model, X_test, y_test, rf_threshold, "Random Forest")

    # 5. Save models
    save_detector(xgb_model, feature_cols, xgb_threshold, 'xgboost', xgb_metrics, 'models/baseline_xgboost.pkl')
    save_detector(rf_model, feature_cols, rf_threshold, 'random_forest', rf_metrics, 'models/baseline_random_forest.pkl')

    # 6. Diagnostic tests
    xgb_detector = BaselineDetector('models/baseline_xgboost.pkl')
    test_detector_behavior(xgb_detector)

    # 7. Feature parity test
    test_feature_parity()

    print("\n" + "="*70)
    print("TRAINING COMPLETE")
    print("="*70)
    print(f"\nXGBoost:       ROC-AUC={xgb_metrics['roc_auc']:.4f}, F1={xgb_metrics['f1_score']:.4f}, Threshold={xgb_threshold:.4f}")
    print(f"Random Forest: ROC-AUC={rf_metrics['roc_auc']:.4f}, F1={rf_metrics['f1_score']:.4f}, Threshold={rf_threshold:.4f}")
    print()
    print("Next step: Run full test suite to verify detector integration")
    print("  python -m pytest tests/test_core.py -v")
    print()

if __name__ == "__main__":
    main()
