# Academic review handover

Read the repository README, then `docs/VERIFICATION_REPORT.md` and `research/paper/README.md`. The review branch integrates the verified local implementation on published prototype commit `92a12966ec49fd6dcd147fd4d7411382715bc729`, which already contains the remote default-branch tip inspected at integration.

## Install, run and inspect

```sh
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-milestone1.lock
python scripts/restore_evidence.py
python -B -s run_dashboard.py --port 8765
```

Use localhost only. Retained evidence lives under `.local/retained`, new dashboard outputs/logs under `.local/dashboard-state`, and scripted short demos under `.local/review-demo`. Versioned paper tables/figures are in `results/` and `research/paper/`; history reports are explicitly marked in `docs/history/`.

Run the exact selection in README for 478 integrated cases; dashboard regression and dashboard-only presets correspond to 420 and 58 cases respectively. The separate 47-case RL selection overlaps and is not additive. Reconstruct paper outputs without experiments using `python scripts/reproduce_paper.py`, and use the retained full-pilot checker command in `docs/REPRODUCIBILITY.md`.

New source changes beyond inherited work are portable artifact restoration, path-root handling, safe regression selection, stronger verifier triplet validation, reproduction scripts and regression tests; research engine/model/data bytes were not retuned. Inspect the committed changed-file inventory and Git diff against the recorded base rather than assuming all files are newly authored.

## Before university submission

Supply authorized author/institution details, choose venue/page limit and approve the substantially AI-assisted draft. Obtain genuine university-approved AI-content and similarity reports for the exact final PDF; both are pending, not claimed below 10%. Select a project license with the copyright holders. Read faculty Q&A and rehearse the short live demonstration.

Scientific limitations remain: high benign-shift false blocking, historical detector ancestry unavailable, narrow mechanism coverage, unequal offline costs, exploratory block count and no real-world validation. A successful test/PR does not remove them. Gate C stays HOLD; no default push or PR merge is authorized.
