# UPI Fraud Stress Lab Dashboard: Implementation and Verification

The working local dashboard is complete within the verified Linux/WSL research-workstation scope. It executes the real project, displays recorded evidence, streams subprocess output and exports scoped results; this delivery does not certify an internet-facing production service or improve the scientific validity of the underlying synthetic study.

## Repository identity and preservation

- **Workspace:** `/home/user/workspace/upi-dashboard-01/`, with the runnable repository in `repository/`.
- **Branch:** `dashboard/local-research-workstation`, created only in the isolated copy.
- **HEAD:** `92a12966ec49fd6dcd147fd4d7411382715bc729`; no new commit.
- **Baseline:** The frozen `upi-scientific-strengthening-01/` workspace, including its existing uncommitted remediation, F5 and matched-pilot work.
- **Preservation:** All 16,523 baseline workspace files, including its Git files, matched the pre-work SHA-256 snapshot. `qa/final-preservation.json` contains the comparison, exact Git status and command results.
- **Research changes:** None. Existing source, tests, datasets, detector artifacts, prior reports and raw outputs were not edited. Imported evidence is a separate copied inventory with fingerprints.

There are 16 additive dashboard source/documentation/vendor files relative to that frozen workspace. Eight generated cache files are separately inventoried as runtime artifacts; `FILE_CHANGES.md` lists every difference, while inherited Git modifications are not misrepresented as dashboard changes.

The incremental patch is `DASHBOARD_INCREMENTAL.patch`, SHA-256 `4100914ee42a39ff9b74ae9ead1f1cff3db02ec08bfea9dfdf7909296eb3c4ac`. Both `git diff --check` and the incremental patch reverse-apply check exited 0; the patch contains only the 16 additive files, including binary font assets.

## Implementation

- **Backend:** Python standard-library HTTP server, strict record parser/catalog and separate allowlisted process adapter. `dashboard/server.py`, `dashboard/records.py` and `dashboard/runner.py` separate transport, evidence calculation and execution.
- **Frontend:** Local vanilla JavaScript/CSS with Lucide icons and IBM Plex fonts. Assets and licenses are vendored; no dashboard-specific Python or npm runtime dependency was added.
- **Design:** Charcoal research workstation, compact tables, restrained teal/amber, persistent sidebar and synthetic limitation notice. Guidance was read from the requested [Anthropic frontend-design skill](https://github.com/anthropics/skills/tree/main/skills/frontend-design); asset sources/licenses are recorded in `dashboard/THIRD_PARTY_NOTICES.md`.
- **Pages:** All eleven requested navigation sections are implemented. Actual branch/commit, package presence, active job, latest software validation, protocol scope and Gate C HOLD are visible rather than invented health values.
- **Controls:** Actual CLI capabilities constrain the form. Unsupported per-family/pilot-arm/budget/time selectors are explained and read-only instead of pretending to alter the protocol.
- **Evidence:** Legacy and pilot runs remain separate. Tables, completion bars, benign controls, model/dataset/policy inventories, deterministic explanations and campaign transaction drill-down use original records and opaque source downloads.
- **Exports:** Filtered CSV, Markdown evidence snapshots, comparison SVG and original report/log downloads are functional. Money is consistently simulated gross debit, not victim loss.

## Executed verification

| Selection | Actual result | Evidence | Counting |
| --- | --- | --- | --- |
| Existing regression selection | 410 passed, 0 failed/skipped/deselected; 1 warning | `qa/regression-410.xml`, `.stdout`, `.stderr` | Distinct existing cases |
| Final dashboard suite | 57 passed, 0 failed/errors/skipped/deselected | `qa/dashboard-tests-delivery.xml` and corresponding logs | Distinct new cases |
| Dashboard suite through live UI | 57 passed, exit 0 | `dashboard-state/runs/qa-browser-dashboard-final/tests.xml` and job log | Repeat of the same 57 |
| Separate RL suite through live UI | 47 passed, exit 0 | `dashboard-state/runs/qa-browser-rl/tests.xml` and job log | Overlapping subset of the 410 |
| Earlier dashboard iterations | 51 passed, then 55 passed | `qa/dashboard-tests-01.*`, `qa/dashboard-tests-final.*` | Earlier subsets, not additional cases |
| JavaScript syntax | Exit 0 | `qa/javascript-final.*` | Not a pytest count |

The executed distinct pytest total is **467**, not a sum of overlapping/repeated runs. The regression warning concerns historical XGBoost pickle serialization compatibility, preserved in `qa/regression-410.stdout`; it is not suppressed or presented as a new dashboard defect.

The 410-case regression selection ran before the last dashboard-only refinements. The final 57-case selection was rerun after backend hardening and the guide, while the subsequent presentation-only labels/header changes received JavaScript syntax and browser checks; no existing engine/test assertion changed.

The 57 dashboard cases exercise path traversal, shell/executable/environment injection, unsupported flags, bounds and types, symlink roots, duplicate/expensive jobs, reference inheritance, malformed/nonfinite records, independent totals, CSV injection handling, model/policy/data inventories, Host/Origin/token enforcement, real stdout/stderr/redaction/clean environments, timeout/cancel/failure handling, partial JUnit and log retention. A real process-control fixture verifies that cancellation terminates a descendant that ignores TERM; these fixture subprocesses are not research experiments.

## Real end-to-end runs

| New run | Executed configuration | Result |
| --- | --- | --- |
| `qa-legacy-main` | Both detectors, four arms, seed 101, 60 training episodes, 6 campaigns per cell, 30 max steps | 96 campaigns; exit 0 |
| `qa-legacy-repeat` | Inherited same configuration | 96 campaigns; exit 0 |
| `qa-legacy-reload` | Saved checkpoint evaluation | 96 campaigns; exit 0 |
| `qa-pilot-main` | Both detectors, five arms, one block, 10 policy episodes, 3 contexts/mechanism; fit/validation/calibration/benign sizes 1000/400/1000/400; seed base 51000 | 60 campaigns; exit 0 |
| `qa-pilot-repeat` | Inherited same qualification configuration | 60 campaigns; exit 0 |
| `qa-pilot-reload` | Saved checkpoint evaluation from the repeat | 60 campaigns; exit 0, no policy training/detector fitting |
| `qa-verify-fresh-legacy` | Actual legacy checker on the new three directories | Exit 0; completeness/equality pass |
| `qa-verify-fresh-pilot` | Actual independent pilot checker | Exit 0; 11,465 checks; 112 TD updates replayed |
| `qa-verify-retained-pilot` | Actual checker on copied retained full main/repeat/reload | Exit 0; 1,012,666 checks; 30,985 TD updates replayed |

These are newly executed qualification runs and fresh analyses of retained full evidence. No expensive full experiment was rerun, and no new research experiment or seed-level replication is inferred from identical repeats.

Every dashboard job has its exact argv, cwd, output directory, start/end, elapsed time, status, exit code and timestamped JSONL streams in `dashboard-state/jobs/`. Test/check commands outside the dashboard are recorded with stdout/stderr and environment overrides in `qa/commands.jsonl`; early inspection/download/syntax work was conducted interactively and is not claimed to be a complete machine-readable shell journal.

## Independent arithmetic and provenance

`qa/independent_metrics.py` does not import dashboard or experiment helpers. It recomputes raw JSONL totals, all 20 pilot cells, sample block SDs, benign thresholds/denominators and the downloaded CSV; it also hashes all registered imported files, producing **746 checks, zero discrepancies** in `qa/independent_metrics.json`.

| Retained pilot measurement | Raw-derived value |
| --- | --- |
| Campaigns / completed | 7,200 / 3,539 |
| Campaign completion | 49.152777…% |
| Transactions | 28,895 |
| ALLOW / FLAG / BLOCK transactions | 24,634 / 600 / 3,661 |
| Gross simulated debit | INR 192,300,996.32 |
| XGBoost benign GE-mimic blocks | 1,738 / 3,600 = 48.278% rounded |
| Random Forest benign GE-mimic blocks | 461 / 3,600 = 12.806% rounded |
| Example filtered cell, XGBoost rule GE | 271 / 360 = 75.278% rounded |

The all-arm completion total is an inventory indicator, not a scientific cross-arm effect estimate. The UI explicitly separates benign episode denominators, campaign completion, evaluated transactions and outcome-conditioned filters.

Evidence completeness, selected-artifact byte equality and scientific validity remain different concepts. Verifier output is visible separately from process exit and software tests; successful verification does not authenticate independent execution or detector ancestry.

## Browser and visual verification

`qa/browser-qa.json` records 19 grouped functional scenarios and a final eleven-page navigation pass. Chromium headless produced no page-console errors; captures include desktop, comparisons, campaign detail, empty results, live validation, cancellation/failure, confirmation and light/dark states.

The actual desktop browser executed both engines and their repeats/reloads, started fixed RL/dashboard tests, downloaded CSV/Markdown/SVG and terminal logs, copied log text, sorted numeric results, inspected original campaigns, and opened then cancelled the expensive-run confirmation. The scope did not execute the full legacy/pilot presets.

Responsive checks at widths 375, 390, 768 and 1512 found document width equal to viewport width after the mobile layout fix. Tables intentionally scroll within their containers; keyboard focus received a visible solid outline, and mobile navigation was exercised.

Representative captures are `qa/DASHBOARD_OVERVIEW.png`, `qa/DASHBOARD_MOBILE.png` and `qa/DASHBOARD_COMPARISON.png`. Full-page and per-section captures remain available, including preliminary images, but browser/keyboard checks are not a formal WCAG certification or cross-browser test.

## Findings, failed attempts and corrections

- **Self-reused evidence:** The underlying pilot checker accepted the same directory in main/repeat/reload slots, exit 0 with complete evidence. That preserved job is intentionally still named `qa-expected-verifier-failure`; its unexpected success is disclosed, not renamed away. The dashboard now rejects reuse before execution, with a permanent test. This does not establish authenticated independent lineage for distinct directories.
- **Expected CLI failure:** `qa-incompatible-verifier` deliberately mixed retained full reference with qualification repeat/reload evidence. It exited 1 with `evidence_complete=false`, and the terminal displayed the diagnostic instead of a success state.
- **Safe cancellation:** `qa-cancel-regression` exited −15 and is recorded cancelled, not failed or passed. No test count is inferred from that partial run.
- **Preset and navigation races:** Repeat/reload initially defaulted to legacy irrespective of the selected run; a subsequent rapid-navigation form reset was also found. Protocol inheritance, stale render guards and pending presets were fixed; actual legacy and pilot repeats/reloads subsequently succeeded.
- **Process cleanup:** Review found that a parent exiting on TERM could leave a TERM-ignoring child. The new adapter now kills remaining process-group members, with a passing real-descendant regression.
- **Incomplete JUnit:** Partial XML no longer leaves the job manager active; counts are unavailable with an explicit note, rather than invented.
- **Large logs:** Retention is bounded with an explicit marker. A 12 MB fixture tested the limit; the UI displays the latest 3,000 loaded lines, with the retained log downloadable.
- **Visual issues:** A narrow-screen grid min-content overflow was reproduced and corrected. Light/dark and responsive screenshots were repeated after the fix.
- **Preview capture timing:** Final image inspection caught preview filenames containing the previously visible SPA page. Those images are preserved with `MISCAPTURE_` prefixes; the delivered three previews were recaptured after explicit page/chart readiness and visually inspected. The first archive and its receipt are preserved; the corrected delivery archive is `UPI_DASHBOARD_LOCAL_WORKSTATION_FINAL.tar.gz`.
- **Harness/setup attempts:** Premature asynchronous job snapshots, an invalid relative Playwright request URL, and an initially incorrect assumption that a chosen cell had no successes caused browser-harness failures. Final job metadata and an actually zero-record filter resolved the checks; no scientific assertion was weakened. Initial vendored assets were mechanically moved from an accidentally nested disposable directory before use; no original source was affected.

No failing pytest assertion was removed or weakened to obtain the reported pass results. Browser-harness errors are summarized in `qa/browser-qa.json`; exact completed job logs, negative-check output, cancelled-run output and all saved test attempts remain in the package.

## Security and deployment limits

The service binds only 127.0.0.1 and uses fixed argv, validated arguments, approved output roots, non-overwrite checks, one active process group, clean child environments, timeouts, cancellation and common-secret redaction. Browser writes require same-origin Host/Origin validation and a random session token; file reads use registered opaque IDs and approved types/roots rather than browser-supplied paths.

No arbitrary shell, user-selected executable, arbitrary pytest, environment input, destructive command, Git mutation, publication or Gate C endpoint exists. Runtime metadata indicates package presence, not health certification; no secret environment dump appears in the UI.

Remaining limits are local trusted-user operation, POSIX/WSL-only cancellation, historical pickle portability, no newly verified clean installation, no formal security penetration test, no multi-user authentication/TLS, and Chromium-only visual execution. Malformed-record parsing is a presentation guard, not an independent proof of every protocol invariant; use the actual protocol checkers for full evidence validation.

Scientific limitations are unchanged: synthetic data, high benign-shift false blocking, historically unverified detector-family provenance, limited mechanism coverage, exploratory comparisons and no powered confirmatory lockbox or real-world validation. The dashboard makes those limits visible rather than claiming to solve them.

## Handover and disposition

Start with `DASHBOARD_HANDOVER.md` and `repository/docs/DASHBOARD_GUIDE.md`. The complete package includes the runnable repository with Git context, imported evidence, new qualification outputs, tests, logs, screenshots, incremental patch and file manifests; `PACKAGE_RECEIPT.json` supplies archive verification separately.

The local verification server was shut down gracefully after testing, and port 8765 was checked closed. Start your own local instance using the documented command; a sandbox localhost address is not a public hosted dashboard.

**Disposition:** Local dashboard implementation PASS; executed software verification PASS; raw-metric consistency PASS; scientific validity limited to the retained exploratory evidence, not newly validated; external production readiness NOT ESTABLISHED; Gate C HOLD. No commit, push, merge, publication, release or downstream research phase was performed.
