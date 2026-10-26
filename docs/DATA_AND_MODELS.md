# Data and model inventory

Legacy models/data are inherited tracked repository artifacts. Their historical detector-family training exclusion is unverified; existing predictions do not reconstruct ancestry. This integration neither retrains nor relabels them.

The matched pilot uses registered synthetic data in `.local/retained/pilot-main/block-XX/`: `episodes.json`, `fit_rows.json`, `validation_rows.json`, `quarantined.json` and an evaluation plan. Detector subdirectories retain model bytes, policies, benign score traces, training transitions and attack campaigns. Top-level `config.json`, `source.json` and `manifest.json` bind configuration, relevant source, role streams, model digests and fit-input fingerprints.

GE lineage and matching prefixes are excluded from registered development roles. HVB and screened ordinary benign data remain available. Benign GE mimics are a distinct final-test stratum; they must not be used to tune the retained detector or thresholds and then reported as untouched test evidence.

The evidence archive deduplicates identical bytes across retained main/repeat/reload sets. Deduplication is storage, not a statement that the underlying runs are independent. All reconstruction paths verify the original recorded file hashes.

The dashboard's Data & Models page lists registered models, data/config/source artifacts and hashes. Inspect the original rows before claiming membership. No real UPI data, production account or victim-loss dataset has been validated here; no real-person data should be added casually.

Only load trusted hash-verified pickle model artifacts. Hashes establish identity/integrity relative to the supplied manifest, not that an arbitrary third-party model is safe or that the manifest is externally signed.
