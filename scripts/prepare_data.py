#!/usr/bin/env python3
"""
Data Preparation Script for UPI Fraud Stress Lab

This script:
1. Loads the raw dataset
2. Validates data quality
3. Engineers features
4. Splits into train/test sets
5. Saves processed data for model training
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data.loader import FraudDataLoader
from data.preprocessor import (
    prepare_train_test_data,
    save_processed_data
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main data preparation pipeline"""

    logger.info("=" * 60)
    logger.info("UPI Fraud Stress Lab - Data Preparation")
    logger.info("=" * 60)

    # Step 1: Load raw data
    logger.info("\n[1/5] Loading raw dataset...")
    loader = FraudDataLoader(data_dir="data/raw")

    try:
        df = loader.load_raw()
    except FileNotFoundError as e:
        logger.error(f"Dataset not found: {e}")
        logger.error("Run: python data/raw/download_dataset.py")
        sys.exit(1)

    # Step 2: Validate dataset
    logger.info("\n[2/5] Validating dataset...")
    stats = loader.validate_dataset(df)

    logger.info(f"  Total transactions: {stats['total_transactions']:,}")
    logger.info(f"  Fraud cases: {stats['fraud_count']:,}")
    logger.info(f"  Legitimate cases: {stats['legitimate_count']:,}")
    logger.info(f"  Fraud rate: {stats['fraud_rate']:.4%}")
    logger.info(f"  Features: {len(stats['features'])} columns")

    # Check for missing values
    missing = {k: v for k, v in stats['missing_values'].items() if v > 0}
    if missing:
        logger.warning(f"  Missing values detected: {missing}")
    else:
        logger.info("  ✓ No missing values")

    # Step 3: Feature engineering and preprocessing
    logger.info("\n[3/5] Engineering features and preprocessing...")
    X_train, X_test, y_train, y_test, preprocessor = prepare_train_test_data(
        df,
        test_size=0.2,
        random_state=42,
        scaling_method='standard',
        engineer_features=True
    )

    logger.info(f"  Train set: {len(X_train):,} samples")
    logger.info(f"  Test set: {len(X_test):,} samples")
    logger.info(f"  Features after engineering: {X_train.shape[1]}")
    logger.info(f"  Train fraud rate: {y_train.mean():.4%}")
    logger.info(f"  Test fraud rate: {y_test.mean():.4%}")

    # Step 4: Save processed data
    logger.info("\n[4/5] Saving processed data...")
    save_processed_data(X_train, X_test, y_train, y_test, output_dir="data/processed")

    # Step 5: Save preprocessor
    logger.info("\n[5/5] Saving preprocessor...")
    preprocessor_path = Path("models/preprocessor.pkl")
    preprocessor_path.parent.mkdir(parents=True, exist_ok=True)
    preprocessor.save(str(preprocessor_path))

    logger.info("\n" + "=" * 60)
    logger.info("✓ Data preparation complete!")
    logger.info("=" * 60)
    logger.info("\nProcessed data saved to:")
    logger.info("  - data/processed/X_train.parquet")
    logger.info("  - data/processed/X_test.parquet")
    logger.info("  - data/processed/y_train.parquet")
    logger.info("  - data/processed/y_test.parquet")
    logger.info("  - models/preprocessor.pkl")
    logger.info("\nReady for model training!")


if __name__ == "__main__":
    main()
