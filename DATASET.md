> HISTORICAL SCOPE RECORD: The body below retains earlier claims and workspace paths, not current acceptance. Use the [current README](README.md), [verification report](docs/VERIFICATION_REPORT.md) and [handover](docs/HANDOVER.md) for present commands, counts and limitations. Historical completion/AUC/novelty/production claims are not adopted. Gate C remains HOLD.

# Dataset Documentation

## Historical dataset description

The older ULB/Kaggle description below does not establish the data used to
fit the supplied detector pickles. The inspected current synthetic CSV has
50,000 rows and its fingerprint is in `../evidence/artifact-audit.stdout`.
Historical model-to-dataset/family ancestry remains unverified.
The new matched pilot uses separately generated registered synthetic episodes,
not this claimed credit-card corpus; see `../FINAL_ACADEMIC_REPORT.md`.

## Overview

**Dataset**: Credit Card Fraud Detection Dataset  
**Source**: Kaggle / Machine Learning Group - ULB  
**Size**: ~284,807 transactions  
**File Size**: 98 MB  
**Format**: CSV  
**Fraud Rate**: ~0.17% (highly imbalanced)

## Description

This dataset contains credit card transactions made by European cardholders in September 2013. It presents transactions that occurred over two days, with 492 frauds out of 284,807 transactions.

This dataset is well-suited for the UPI Fraud Stress Lab as it:
- Contains real-world transaction patterns
- Has fraud labels for supervised learning
- Includes temporal information (Time)
- Has transaction amounts (Amount)
- Features privacy-preserving PCA transformations
- Represents realistic class imbalance

## Features

### Core Features
- **Time**: Seconds elapsed between each transaction and the first transaction in the dataset
- **Amount**: Transaction amount (currency not specified)
- **Class**: Target variable (1 = fraud, 0 = legitimate)

### PCA-Transformed Features (V1-V28)
The dataset contains 28 PCA-transformed features (V1 through V28) which are:
- Principal components obtained with PCA
- Protect confidential cardholder information
- Capture the most important patterns in the original features
- Already normalized and anonymized

**Note**: Due to confidentiality, the original features and background information about V1-V28 are not provided.

## Statistics

### Class Distribution
```
Legitimate transactions: 284,315 (99.83%)
Fraudulent transactions: 492 (0.17%)
Imbalance ratio: ~577:1
```

### Transaction Amounts
```
Mean:     88.35
Median:   22.00
Min:      0.00
Max:      25,691.16
Std Dev:  250.12
```

### Temporal Coverage
```
Duration: 2 days (172,792 seconds)
Time range: 0 to 172,792 seconds
```

## Data Quality

- **Missing Values**: None
- **Duplicates**: None detected
- **Outliers**: Present in Amount (expected for fraud detection)
- **Data Types**: All numeric (float64)

## Feature Engineering

The preprocessing pipeline (`src/data/preprocessor.py`) adds the following engineered features:

### Temporal Features
1. **Hour**: Hour of day (0-23) derived from Time
2. **Day**: Day number in the dataset
3. **Hour_sin**: Sine encoding of hour (captures cyclical nature)
4. **Hour_cos**: Cosine encoding of hour (captures cyclical nature)

### Amount-Based Features
1. **Amount_log**: Log-transformed amount (log1p for zeros)
2. **Amount bins**: Categorical bins (micro, small, medium, large, xlarge)
   - Micro: 0-10
   - Small: 10-50
   - Medium: 50-100
   - Large: 100-500
   - XLarge: 500+

### Scaling
- All features are standardized using StandardScaler
- Mean = 0, Standard Deviation = 1
- Applied after train/test split to prevent data leakage

## Usage

### Download Dataset
```bash
cd data/raw
python download_dataset.py
```

### Load Raw Data
```python
from src.data.loader import FraudDataLoader

loader = FraudDataLoader(data_dir="data/raw")
df = loader.load_raw()

# Get dataset info
info = loader.get_dataset_info()
print(info)
```

### Prepare Processed Data
```python
from src.data.preprocessor import prepare_train_test_data

# Load and preprocess
X_train, X_test, y_train, y_test, preprocessor = prepare_train_test_data(
    df,
    test_size=0.2,
    random_state=42,
    scaling_method='standard',
    engineer_features=True
)
```

### Run Full Pipeline
```bash
python scripts/prepare_data.py
```

This will:
1. Load raw data
2. Validate data quality
3. Engineer features
4. Split into train/test (80/20)
5. Apply scaling
6. Save processed data to `data/processed/`

## Processed Data Format

After running `prepare_data.py`, the following files are created:

```
data/processed/
├── X_train.parquet      # Training features (227,846 samples)
├── X_test.parquet       # Test features (56,961 samples)
├── y_train.parquet      # Training labels
└── y_test.parquet       # Test labels

models/
└── preprocessor.pkl     # Fitted preprocessor for inference
```

## Challenges & Considerations

### 1. Class Imbalance
- **Problem**: Only 0.17% of transactions are fraudulent
- **Impact**: Model may achieve 99.8% accuracy by predicting all legitimate
- **Solutions**: 
  - Use SMOTE or ADASYN for oversampling
  - Class weights in model training
  - Focus on precision, recall, F1-score, and AUC-ROC
  - Campaign-level evaluation (not just transaction-level)

### 2. Temporal Dependency
- **Problem**: Fraud patterns may evolve over time
- **Impact**: Train/test split must respect temporal ordering
- **Solutions**:
  - Current split is random (acceptable for initial baseline)
  - For production: implement time-based split
  - For stress testing: evaluate on future time periods

### 3. Feature Anonymization
- **Problem**: PCA features lack interpretability
- **Impact**: Difficult to explain model decisions
- **Solutions**:
  - Use SHAP values for feature importance
  - Focus on Amount and Time for interpretable features
  - Document model behavior through extensive testing

### 4. Dataset Age
- **Problem**: Data from 2013 may not reflect current fraud patterns
- **Impact**: Real-world performance may differ
- **Solutions**:
  - Treat as benchmark/baseline dataset
  - Focus on methodology validation
  - Note limitations in research documentation

## UPI Adaptation

While this is a credit card dataset, it serves as a proxy for UPI fraud detection:

### Similarities
- Transaction-based structure
- Binary classification (fraud/legitimate)
- Temporal patterns
- Amount-based features
- Class imbalance

### Differences
- UPI has instant settlement vs. credit authorization
- Different fraud vectors (account takeover, SIM swap, etc.)
- Different transaction limits and patterns
- Real-time detection requirements

### Research Validity
This dataset is suitable for the UPI Fraud Stress Lab because:
1. **Methodology Focus**: Testing adversarial resilience, not UPI-specific patterns
2. **Baseline Establishment**: Standard benchmark for fraud detection research
3. **Reproducibility**: Publicly available for verification
4. **Scale**: Large enough for meaningful experiments (284K transactions)

## References

1. **Original Paper**: Andrea Dal Pozzolo, Olivier Caelen, Reid A. Johnson and Gianluca Bontempi. "Calibrating Probability with Undersampling for Unbalanced Classification." In Symposium on Computational Intelligence and Data Mining (CIDM), IEEE, 2015

2. **Dataset Source**: https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud

3. **Citation**:
   ```
   Machine Learning Group - ULB. (2018). Credit Card Fraud Detection [Dataset]. 
   Kaggle. https://doi.org/10.34740/KAGGLE/DSV/27
   ```

## License

The dataset is made available under the Database Contents License (DbCL) v1.0.

**For Research Use**: This dataset is suitable for academic research and methodology validation. Not for production fraud detection systems.

---

**Last Updated**: 2026-09-16  
**Prepared By**: Data Agent - UPI Fraud Stress Lab
