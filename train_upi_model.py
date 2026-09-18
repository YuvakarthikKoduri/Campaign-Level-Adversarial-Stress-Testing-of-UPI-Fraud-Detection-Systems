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
    print(f"Generating {n_samples} synthetic UPI transactions...")
    np.random.seed(42)
    
    # Legit transactions 
    n_legit = int(n_samples * 0.95)
    legit_amount = np.random.exponential(scale=1500, size=n_legit)
    # usually done during day (6am to 10pm)
    legit_hour = (np.random.normal(loc=14, scale=4, size=n_legit).astype(int) % 24)
    legit_velocity = np.random.poisson(lam=1, size=n_legit) # few txns per hour
    legit_new_vpa = np.random.binomial(1, 0.05, size=n_legit) # 5% new VPAs
    
    # Fraud transactions
    n_fraud = n_samples - n_legit
    fraud_amount = np.random.exponential(scale=35000, size=n_fraud)
    # often late night or early morning
    fraud_hour = (np.random.normal(loc=3, scale=3, size=n_fraud).astype(int) % 24)
    fraud_velocity = np.random.poisson(lam=8, size=n_fraud) # high volume quickly
    fraud_new_vpa = np.random.binomial(1, 0.8, size=n_fraud) # 80% new VPAs
    
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
