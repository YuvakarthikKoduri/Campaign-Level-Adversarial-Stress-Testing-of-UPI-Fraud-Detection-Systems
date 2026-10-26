# Faculty demonstration

Use the installed Python 3.11 checkout and keep the presentation/paper available. This is a live synthetic demonstration, not a production payment service.

1. Explain the question: whether a simulated campaign reaches its target before intervention, and why FLAG differs from BLOCK. Show `docs/images/architecture.svg`.
2. Run `python scripts/restore_evidence.py`, then `python -B -s run_dashboard.py --port 8765`; open localhost. Identify branch/commit and the persistent synthetic warning.
3. Select retained `pilot-main`. Show attempted/completed campaign counts, transaction decisions, gross debit definition and raw-record links. Do not mix the legacy selector into this table.
4. In Run Experiments choose a new short legacy name, both detectors, all attackers, one seed, six training episodes and two campaign contexts. Preview the actual command, then run. Show live stdout/stderr, active job, exit code and resulting records.
5. For a short pilot use one block, two learned episodes and two contexts; the pilot CLI fixes both detectors, five arms and two mechanisms. Do not advertise unsupported individual pilot-arm execution.
6. Inspect Results Explorer filters/sorting and a campaign transaction sequence. Identify target, proposed/transferred amount, simulated time, FLAG and first BLOCK/termination.
7. Compare detectors/attackers only within the selected version. Explain block SD versus exploratory paired intervals.
8. Show benign GE mimic rates, 48.278%/12.806%, then ordinary-benign results. Explain why zero observed ordinary BLOCK is not a population guarantee or a real-world claim.
9. Export CSV, Markdown summary and SVG; inspect identifiers/limitations and underlying records. Open model hashes and registered lineage.
10. Show Validation & Tests and the current verification report. Distinguish software cases, raw-record checks, reproduced jobs and scientific claims.
11. Present the literature matrix and qualified novelty statement: RL banking attacks and sequence detection already exist; the contribution is the implemented auditable combination and synthetic failure analysis.
12. Close with limitations and pending author/venue/AI-policy/external-check approvals. Gate C remains HOLD.

If faculty need a scripted fallback, `python scripts/review_smoke.py` runs both short triplets/checkers and preserves commands/logs under `.local/review-demo/`; it refuses an existing directory. The screenshots in `docs/images/` are from the running application, not a mockup.
