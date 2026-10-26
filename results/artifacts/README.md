# Byte-preserved evidence archive

`verified-evidence-v1.zip` is a 10,523,806-byte content-addressed ZIP. SHA-256: `fb50e89d46f82a729b218b4bc2776e210f1bc2d1a69b340b713bf729bf13e04b`. Its `manifest.json` maps nine retained run directories and verification/test-proof files onto 249 unique byte objects, restoring 715 files without duplicate object storage.

Included runs: pilot-main/repeat/reload; prior legacy-short/repeat/reload; corrected legacy-full/repeat/reload. The archive does not include virtual environments, caches, credentials or new short-review output directories.

Run `python scripts/restore_evidence.py` from repository root. It validates archive/object hashes and unsafe paths before writing approved local evidence, refuses differing existing bytes and writes a portable catalog. The original raw records are unchanged; catalog metadata is newly generated to avoid undocumented private execution paths.

The manifest proves integrity relative to the supplied versioned archive, not an external signature or independent scientific validation. Identical repeated objects are deduplicated for storage only; repeats are not statistical replication.
