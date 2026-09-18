"""
Quick script to prepare creditcard.csv for training.
Converts raw data to the format expected by train.py.
"""

import pandas as pd
from pathlib import Path

# Paths
project_root = Path(__file__).parent
raw_data = project_root / 'data' / 'raw' / 'creditcard.csv'
processed_data = project_root / 'data' / 'processed' / 'transactions.csv'

print("Loading raw creditcard.csv...")
df = pd.read_csv(raw_data)

print(f"Loaded {len(df)} transactions")
print(f"Columns: {df.columns.tolist()}")
print(f"Fraud rate (Class): {df['Class'].mean():.2%}")

# Rename Class column to is_fraud
df = df.rename(columns={'Class': 'is_fraud'})

# Add transaction_id if not present
if 'transaction_id' not in df.columns:
    df.insert(0, 'transaction_id', range(1, len(df) + 1))

print(f"\nProcessed columns: {df.columns.tolist()}")
print(f"Fraud rate (is_fraud): {df['is_fraud'].mean():.2%}")

# Save processed data
processed_data.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(processed_data, index=False)

print(f"\nSaved processed data to: {processed_data}")
print("Ready for training!")
