import sys
import pickle
from pathlib import Path
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import xgboost as xgb
from sklearn.model_selection import train_test_split

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.detectors.baseline import BaselineDetector

def generate_synthetic_upi_data(n_samples=20000):
    """
    Generate realistic UPI transaction data with overlapping distributions.

    Key design: Create REALISTIC overlap between legitimate and fraud:
    - Some legit is high-value (rent, business payments)
    - Some fraud is low-value (testing, avoiding detection)
    - Both classes span full day (fraud not exclusively late-night)
    - Velocity varies within both classes

    Target: ~85-92% AUC (useful detector with genuine blind spots)
    """
    print(f"Generating {n_samples} synthetic UPI transactions...")
    np.random.seed(42)

    n_legit = int(n_samples * 0.95)
    n_fraud = n_samples - n_legit

    # === LEGITIMATE TRANSACTIONS ===
    # Create multi-modal legitimate behavior:
    # - 70% small daily transactions (₹100-3000)
    # - 20% medium transactions (₹3000-15000)
    # - 10% large legitimate (rent, business, ₹15000-50000)

    n_legit_small = int(n_legit * 0.7)
    n_legit_medium = int(n_legit * 0.2)
    n_legit_large = n_legit - n_legit_small - n_legit_medium

    legit_amount = np.concatenate([
        np.random.exponential(scale=800, size=n_legit_small) + 100,
        np.random.exponential(scale=3000, size=n_legit_medium) + 3000,
        np.random.exponential(scale=8000, size=n_legit_large) + 15000
    ])
    np.random.shuffle(legit_amount)

    # Timing: mostly daytime (6am-11pm) but some night-shift/emergency
    legit_hour_day = np.random.normal(loc=14, scale=5, size=int(n_legit * 0.92))
    legit_hour_night = np.random.normal(loc=2, scale=2, size=n_legit - len(legit_hour_day))
    legit_hour = np.concatenate([legit_hour_day, legit_hour_night]).astype(int) % 24
    np.random.shuffle(legit_hour)

    # Velocity: mostly low, occasionally burst (e.g., bill payments)
    legit_velocity = np.concatenate([
        np.random.poisson(lam=0.8, size=int(n_legit * 0.85)),
        np.random.poisson(lam=3, size=n_legit - int(n_legit * 0.85))
    ])
    np.random.shuffle(legit_velocity)

    # New VPA: 10% new (first-time payments)
    legit_new_vpa = np.random.binomial(1, 0.10, size=n_legit)

    # === FRAUD TRANSACTIONS ===
    # Create multi-modal fraud behavior:
    # - 30% high-value (₹20,000-60,000) - traditional "smash and grab"
    # - 40% medium-value (₹5,000-20,000) - avoiding high-value triggers
    # - 30% low-value (₹500-5,000) - testing/slow-drain

    n_fraud_high = int(n_fraud * 0.3)
    n_fraud_medium = int(n_fraud * 0.4)
    n_fraud_low = n_fraud - n_fraud_high - n_fraud_medium

    fraud_amount = np.concatenate([
        np.random.exponential(scale=12000, size=n_fraud_high) + 20000,
        np.random.exponential(scale=4000, size=n_fraud_medium) + 5000,
        np.random.exponential(scale=1200, size=n_fraud_low) + 500
    ])
    np.random.shuffle(fraud_amount)

    # Timing: 60% late night, 40% daytime (compromised office accounts)
    fraud_hour_night = np.random.normal(loc=3, scale=3, size=int(n_fraud * 0.6))
    fraud_hour_day = np.random.normal(loc=13, scale=5, size=n_fraud - len(fraud_hour_night))
    fraud_hour = np.concatenate([fraud_hour_night, fraud_hour_day]).astype(int) % 24
    np.random.shuffle(fraud_hour)

    # Velocity: mostly high, some low (low-velocity fraud exists)
    fraud_velocity = np.concatenate([
        np.random.poisson(lam=6, size=int(n_fraud * 0.7)),
        np.random.poisson(lam=2, size=n_fraud - int(n_fraud * 0.7))
    ])
    np.random.shuffle(fraud_velocity)

    # New VPA: 60% new (still higher than legit, but not 80%)
    fraud_new_vpa = np.random.binomial(1, 0.60, size=n_fraud)

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

    df = pd.concat([df_legit, df_fraud]).sample(frac=1.0, random_state=42).reset_index(drop=True)

    # Print distribution summary for verification
    print("\nData Distribution Summary:")
    print(f"Legitimate transactions: {n_legit} (95%)")
    print(f"  Amount range: ₹{df_legit['amount'].min():.0f} - ₹{df_legit['amount'].max():.0f}")
    print(f"  Amount median: ₹{df_legit['amount'].median():.0f}")
    print(f"Fraud transactions: {n_fraud} (5%)")
    print(f"  Amount range: ₹{df_fraud['amount'].min():.0f} - ₹{df_fraud['amount'].max():.0f}")
    print(f"  Amount median: ₹{df_fraud['amount'].median():.0f}")
    print(f"\nOverlap exists: Legit max ₹{df_legit['amount'].quantile(0.95):.0f}, Fraud min ₹{df_fraud['amount'].min():.0f}")

    return df

def main():
    df = generate_synthetic_upi_data(50000)
    
    feature_cols = ['amount', 'hour_of_day', 'velocity_1h', 'is_new_vpa']
    X = df[feature_cols].values
    y = df['is_fraud'].values
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    print("Training XGBoost...")
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        random_state=42,
        tree_method='hist'
    )
    
    model.fit(X_train, y_train)
    
    print("Evaluating...")
    from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    
    print(f"ROC-AUC: {roc_auc_score(y_test, y_prob):.3f}")
    print(f"F1 Score: {f1_score(y_test, y_pred):.3f}")
    
    # Save model
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    detector = BaselineDetector()
    detector.model = model
    detector.feature_names = feature_cols
    # No scaler needed for trees
    
    model_path = models_dir / "baseline_xgboost.pkl"
    with open(model_path, "wb") as f:
        pickle.dump({
            'model': model,
            'feature_names': feature_cols,
            'scaler': None
        }, f)
        
    print(f"Saved UPI model to {model_path}")

if __name__ == "__main__":
    main()
