# Results registry

`results_summary.csv` is the full mechanism-pilot main-run table, regenerated from verified raw records by `python scripts/reproduce_paper.py`. It includes denominator, block count/SD, decisions, gross debit and conditional timing/event counts.

`comparison_tables/` contains benign strata, exploratory paired block contrasts and a separate corrected legacy table. Main/repeat/reload are reproduction checks, not additional campaigns or independent replications in paper analysis.

`independent_reconstruction.json` records all main-run source SHA-256s, assertion count, totals and analysis seed. `research/paper/figures/` contains SVG/PDF figures generated only from those raw data; their uncertainty is labeled explicitly.

Large repeated raw trees are not committed separately. Restore the content-addressed artifact under `results/artifacts/` to ignored `.local/retained`. Short new demonstration data are separate and do not replace these retained full-run values.
