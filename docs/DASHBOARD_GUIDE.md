# UPI Fraud Stress Lab Dashboard

This is a local, single-user research workstation over the existing synthetic engines and recorded evidence. It is not an internet-facing service or a real-world payment-security product. Gate C remains HOLD.

## Start here

From the repository root run `python scripts/restore_evidence.py`. Retained records are restored into ignored `.local/retained/`; new jobs write only beneath `.local/dashboard-state/runs/`. Portable catalog metadata is generated from the bundled archive, not linked to an earlier private workspace.

On Linux or WSL2, use Python 3.11 and the project's existing compatible environment. From `repository/`:

```sh
python -B -s run_dashboard.py --port 8765
```

Open [the local dashboard](http://127.0.0.1:8765). Chromium is the executed browser target; other browsers are not certified. Activate your compatible Python 3.11 environment rather than using a private workspace's interpreter path.

For environment reconstruction, the existing Linux lockfile is:

```sh
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-milestone1.lock
python scripts/restore_evidence.py
python -B -s run_dashboard.py --port 8765
```

The integrated delivery tested a fresh Python 3.11.17 environment with the lock using uv sync, in addition to the older reused environment. The lock contains platform-specific packages, including NVIDIA NCCL; do not infer native Windows/macOS portability. Native Windows process-group cancellation is not implemented: use WSL2. No dashboard-specific Python or npm runtime dependency was added.

Stop the service with Ctrl+C; the server attempts to cancel its active process group. A different port may be selected, but the server cannot bind a public address. Do not place it behind a public reverse proxy.

## Workspace pages

- **Overview:** Select one recorded run and inspect campaign completion, evaluated transactions, ALLOW/FLAG/BLOCK counts, gross simulated transfer, local execution activity and benign-shift limitations. Expand each metric's definition to inspect its denominator and original records.
- **Run Experiments:** Choose a supported workflow and a fresh restricted output name. Read the exact command preview before Run. Larger workloads require a separate confirmation; cancelling the dialog executes nothing.
- **Terminal & Logs:** Select a job to inspect timestamped stdout/stderr, command, elapsed time, status and exit code. Copy copies the loaded log; Download retrieves the preserved JSONL log. Stop sends TERM and kills remaining descendants in the isolated process group.
- **Results Explorer:** Filter one version by detector, strategy, mechanism, seed/block and outcome. Sort column headings and select a row for a deterministic explanation, raw configuration and campaign drill-down.
- **Detector Comparison:** Inspect full 0–100% completion axes and the separate ordinary-benign and GE-mimic false-block denominators. Hover for sample size and block SD; uncertainty is not a confidence interval.
- **Attacker Comparison:** Compare recorded cells within one protocol. Five matched pilot arms still have different offline training costs; legacy comparisons retain their documented asymmetries.
- **Campaign Analysis:** Inspect original campaign identity, termination, target, transaction timing/gaps, proposed amount, actual debit, detector decision and terminal marker. Each source download and row number identifies the original record.
- **Data & Models:** Inspect model hashes, fit bindings, membership roles, evaluation contexts, dataset fingerprints and policy JSON hashes. The dashboard hashes pickle bytes but never unpickles them to render a page.
- **Validation & Tests:** Run fixed RL, existing regression or dashboard selections through the runner. Passed, failed, errors, skipped and deselected counts are separate. Imported prior reports are explicitly different from local runs.
- **Reports & Export:** Download filtered CSV, a generated Markdown evidence snapshot, comparison SVG or preserved reports. Exports identify the selected protocol; Markdown includes filters, evidence and limitations.
- **Settings:** Inspect package presence, local execution limits and security boundaries. Switch the complete light/dark theme without changing research data.

## Supported commands and choices

The adapter builds argv lists and never accepts shell commands. The terminal presets are editable supported configurations, not unrestricted command inputs.

| Workflow | Supported choices |
| --- | --- |
| Legacy | XGBoost, Random Forest or both; static, adaptive, RL, untrained RL or all; 1–9 distinct integer seeds; 1–300 training episodes; 1–40 campaigns per cell; 1–30 steps |
| Pilot | Both detectors, all five arms, HVB and GE, fixed by the CLI; 1–9 blocks; 1–300 policy episodes; 1–40 contexts per mechanism; bounded development-data sizes |
| Repeat | Inherits all supported configuration values from the selected reference; it is not an independent replication |
| Checkpoint reload | Inherits the reference configuration and uses its saved policies/models; does not train policies in reload mode |
| Verification | Three distinct registered runs from one protocol, passed to that protocol's existing checker |
| Tests | Fixed 47-case overlapping RL subset, integrated 420-case regression selection, or 58 dashboard cases |

Pilot development sizes are fit episodes 4–1,000, validation episodes 1–400, calibration episodes 2–1,000 and each benign test stratum 1–400. Not every very small calibration sample guarantees a feasible operating point: genuine engine failures remain failures with logs.

The pilot CLI fixes both detectors, five arms, two mechanisms and 30 steps. Its time limit is 86,400 simulated seconds and its budget is target-sized. Legacy has no family, budget or duration CLI flag. Those controls are deliberately read-only; the dashboard does not silently change the scientific protocol.

The short demonstration preset requests 60 training episodes, six campaigns per legacy cell, seed 101 and both detectors. The pilot preset requests one block, ten policy episodes and three contexts per mechanism. These are qualification runs, not new full studies. Workload previews derive episode/campaign counts; they are not runtime predictions.

## Metric definitions

- **Campaign completion:** Completed simulated campaigns divided by selected attempted campaigns. Filtering on outcome changes the denominator and cannot be read as an unconditional success estimate.
- **Evaluated transactions:** Rows that reached detector evaluation, not all rejected pre-execution proposals. Mean attempts in the table is evaluated transactions per campaign.
- **FLAG:** An alert, which can still transfer under the simulator's policy. It is not synonymous with a rejected transaction.
- **BLOCK:** A detector decision that stops this simulator's campaign. Proposed blocked money is not actual debit or proven savings.
- **Gross simulated transfer:** Sum of actual `amount_transferred`, in INR. It is not unrecovered victim loss.
- **Benign false-block rate:** Legitimate test episodes with peak score at or above the registered block threshold divided by legitimate episodes. Only detector/block filters apply to this separate stratum.
- **Block SD:** Sample SD of completion percentages across selected blocks/seeds; nullable for one replication. It is not a confidence interval and campaigns are not asserted independent.
- **Held-out mechanism:** Declared GE generator/ancestry/prefix excluded from the new registered development data. Historical detector-training family exclusion remains unverified.

## Evidence and safety boundaries

Imported campaign files are checked against their registered hashes when loaded; record parsing rejects malformed amounts, identities, decisions, timestamps, counts and inconsistent gross debit. File-stat signatures invalidate the parsed cache when inputs change. These checks are not a replacement for the protocol checker. A local verifier result is attached only to its exact named run and is not reused after newer run-file timestamps.

One job may run at a time. Output names cannot traverse directories or overwrite existing outputs; requests cannot choose executables, shell strings, environment variables or pytest arguments. Write requests require the local origin and a session token, with Host validation and a restrictive content-security policy. Logs redact common secret assignment forms; child processes receive a clean environment rather than inherited secrets.

Ordinary jobs time out after 30 minutes; larger jobs after two hours. A larger job means more than 600 policy-training episodes or more than 1,000 evaluation campaigns. Logs retain approximately 10 MB with an explicit truncation marker; the terminal renders the latest 3,000 loaded lines and downloads the retained log. Interrupted/cancelled jobs preserve partial output and are not counted as completed.

The prior underlying pilot checker accepted one evidence directory reused in every slot. This integration corrects it as well as the already guarded dashboard: directories must differ, roles/configurations must match and reload must execute zero training. Even distinct directories and byte equality do not authenticate independent execution by themselves. Failed jobs remain preserved rather than being deleted.

This is a trusted-local-user tool, not a formal security-certified multi-user service. Do not load untrusted pickle artifacts into the underlying experiment runner; existing project model loading still uses pickle. The server is POSIX-only and no cross-platform installation certification is claimed.

## Tests and evidence

```sh
python -B -m pytest dashboard/test_dashboard.py -q
python -B -m pytest tests/test_prototype_rl.py -q
```

Use the fixed regression preset for the integrated 420-case selection. The 47 RL cases overlap that selection. The integrated dashboard selection contains 58 cases, so the executed distinct total is 478. Prior 410/57/467 counts are historical scopes, not additional independent cases.

See [current verification](VERIFICATION_REPORT.md), `docs/verification/` and local `.local/dashboard-state/jobs/`. Every job records argv, cwd, start/end, exit code and preserved timestamped output. Prior reports in `docs/history/` are explicitly historical.

The first screen uses retained pilot evidence, not invented values. Integrated short runs use `review-*` names and remain separate from the full study. The review feature branch includes the dashboard in a broader integration/paper package; no full-scale study or Gate C workflow is performed. Feature-branch commits/PR status are recorded in the handover, not inferred from the earlier dashboard report.
