# Reproducibility and provenance

Start from the dedicated review branch, install the locked Python 3.11 environment and run `python scripts/restore_evidence.py`. Read `results/artifacts/manifest.json` for the archive SHA-256 and size, and the archive's `manifest.json` for every path-to-object digest. Restoring is idempotent only when existing bytes match; changed files are never overwritten.

`python scripts/reproduce_paper.py` rechecks main-run file hashes, integer-paise transfers, target completion, transaction counts, cell rates, benign peaks and thresholds, and legacy gross arithmetic. It regenerates the paper tables and machine-readable summaries, including six block-paired exploratory contrasts with fixed bootstrap seed 20261026. Add `--figures` in the optional analysis environment to reproduce SVG/PDF figures.

`python scripts/review_smoke.py` creates fresh short legacy/pilot main/repeat/reload outputs and runs both checkers. It refuses an existing `.local/review-demo` directory so failed attempts are not silently overwritten. To keep another attempt, use another checkout; do not remove evidence merely to obtain a clean success.

Full pilot verification:

```sh
python verify_mechanism_pilot.py \
 --reference .local/retained/pilot-main --repeat .local/retained/pilot-repeat \
 --reload .local/retained/pilot-reload --output .local/pilot-check-new.json
```

The checker requires distinct directories, correct fit/reload roles, matching configurations, bound source hashes and zero reload training; it independently reconstructs ledger features/rewards/TD updates. The reference design/source files remain unchanged, preserving their source binding. Running after a research-engine change requires new versioned evidence, not editing an old manifest.

Historical legacy full evidence can be read and reconstructed by the separate arithmetic script. Do not assume a later checker can establish historical source coverage that did not exist when the old run was produced; prior checker evidence is preserved with its identity.

Within-environment deterministic repeats are not universal cross-platform guarantees. Pickle/library versions, operating system, numerical libraries and Git metadata matter. Record your versions, exact command, exit code and hashes; never call a repeat an additional independent study block.
## Evidence of new short demonstrations

`results/artifacts/review-short-workflows.zip` contains the fresh-install short main/repeat/reload/check workflows and the dashboard execution records, including cancellation partials. Its checksum, size and member count are in `verification/SHORT_ARCHIVE.json`; these records are separate from the retained full-study archive and must not be counted as new independent pilot blocks.
