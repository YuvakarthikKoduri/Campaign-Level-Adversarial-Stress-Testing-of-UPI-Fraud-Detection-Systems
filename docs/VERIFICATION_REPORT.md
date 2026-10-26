# Academic integration verification and readiness report

The integrated prototype is suitable for an exploratory synthetic engineering demonstration within the tested scope. It is not yet an unqualified university submission: author/venue approval, approved AI-content and similarity reports, and a copyright-holder license decision remain outstanding.

## Repository identity and integration

- **Remote**: `YuvakarthikKoduri/Campaign-Level-Adversarial-Stress-Testing-of-UPI-Fraud-Detection-Systems`; inspected default branch `master`, tip `1e2ca9e3db4a19bb72e0433f07f10425f74b82fa`.
- **Appropriate base**: published `prototype/rl-academic-complete`, `92a12966ec49fd6dcd147fd4d7411382715bc729`. The default tip is its ancestor, verified initially and after refetch. The separate repair branch was inspected; there were no tags.
- **Integration branch**: `review/academic-dashboard-paper-v1`. Verified local dashboard/research work was copied into a fresh clone, not over the original workspaces. Inspect the PR commit list and `git rev-parse HEAD` for final identity; a document cannot include the hash of a commit containing itself.
- **Inheritance**: `verification/INHERITED_FILES.json` records the 42 initial inherited paths; the preserved F5 schema test was also copied. `verification/CHANGED_FILES.csv` separates files byte-identical to the inherited snapshot, subsequently modified inherited files and new work against the base.
- **Workflow permission blocker**: the first feature push was rejected because the OAuth app lacks `workflow` scope. Unpublished commit `59730cf8d307f1319f106a52dc03b3f52346fd15` is preserved on local branch `review/academic-dashboard-paper-with-ci-local`; the integration branch was reconstructed from its implementation parent with the unchanged CI definition stored as a non-executing `docs/ci/review-ci.yml.example`. No source/evidence was discarded, no published history was rewritten and no active CI success is claimed.
- **Preservation**: `verification/PRESERVATION.json` compares all 1,269 frozen files in `upi-dashboard-01`. No original study, dataset, model or prior closeout was overwritten. Historic broader entry counts belong to their dated reports and are not misrepresented as new checks.

## What changed

The working legacy and matched-pilot engines and local dashboard were integrated from their verified sources. Integration-specific implementation changes strengthen triplet verification, restore portable byte-verified evidence, correct nested local artifact-root handling, update fixed regression selections and add reproduction/authoring/handover utilities. Research rewards, historical model artifacts and datasets were not retuned.

A final frontend correction prevents CSV/Markdown/SVG exports while selected evidence is loading and ignores stale failed responses. A controlled delayed-response browser regression proves that a pending selection cannot download the previous records; export resumes with the expected 271/360 selected cell after loading (`verification/browser-race-regression.json`).

The pilot verifier now rejects one directory reused for main/repeat/reload, requires proper fit/reload modes and consistent configurations, and checks zero reload training. The dashboard also rejects reused verification slots for either engine; the standalone legacy checker retains its historical limitation. The dashboard root-selection fix permits approved `.local/dashboard-state` records without permitting `.git` access. Regression tests cover those defects and archive corruption/path/symlink/idempotence behavior.

New documentation, figures and tables replace unsupported current claims; dated historical bodies are explicitly scoped. All eleven dashboard sections remain implemented, with no unrestricted shell, Git mutation, publication or Gate C endpoint. The workstation remains localhost-only and single-user, not security-certified for the internet.

## Actual software verification

| Execution | Actual result | Evidence |
|---|---|---|
| Initial integrated selection | 477 passed; before the extra nested-state case | `verification/integrated-tests-01.*` |
| Dashboard portability selection | 58 passed | `verification/dashboard-portability.*`, where present; original log retained |
| Fresh Python 3.11 environment | Created separately; locked dependencies installed successfully | `verification/fresh-environment.stderr`, command journal |
| Fresh integrated selection | 478 passed, one warning, no failures/skips/deselections | `verification/fresh-integrated-tests.xml`, stdout/stderr |
| Final integrated rerun after source changes | 478 passed, one warning, no failures/skips/deselections | `verification/final-integrated-tests.xml`, stdout/stderr |
| Post-export-race final selection | 478 passed, one warning, no failures/skips/deselections | `verification/post-race-tests.xml`, stdout/stderr |
| Real dashboard jobs | Both engines: main, repeat, checkpoint reload and checker all exit zero | `verification/http-workflows.json`, short-workflow archive |
| Fresh-environment scripted smoke | Both engines: main/repeat/reload/check all exit zero | `verification/fresh-short-demo.*`, archive `fresh-demo/commands.jsonl` |
| Retained full pilot checker | 1,012,673 checks, 30,985 TD updates replayed, no discrepancies | `verification/retained-full-pilot.json` |
| Independent paper reconstruction | 44,608 source-hash/arithmetic/record checks | `results/independent_reconstruction.json`, `verification/paper-figures-final.*` |

The 478 distinct cases consist of 420 selected regression and 58 dashboard cases. The 47-case RL selection overlaps and must not be added; repeated 477/478 runs and eight short workflow commands are not additional distinct cases or independent study replications. The single warning concerns loading historically serialized XGBoost artifacts and is preserved, not suppressed.

The final selected command, from repository root with the fresh environment active, is:

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -B -m pytest \
 tests/test_core.py tests/test_milestone1.py tests/test_gate_b.py \
 tests/test_prototype_rl.py tests/test_mechanism_pilot.py tests/test_mechanism_cli.py \
 tests/test_artifact_restore.py test_timing.py test_vpa_strategies.py \
 examples/test_environment.py closeout-tests/test_independent.py \
 f5-evidence/test_schema.py dashboard/test_dashboard.py -q
python -B scripts/review_smoke.py
python scripts/reproduce_paper.py
```

The wrapper journal additionally records UTC start/end, exact interpreter, thread/environment controls, cwd, exit and elapsed duration. The short smoke refuses existing output directories; use a clean ignored output root rather than overwriting evidence.

## Dashboard and presentation verification

Navigation was exercised across all eleven pages on the actual localhost server. Browser screenshots at desktop and mobile sizes were inspected, and widths 1,512, 768 and 390 pixels had no page-level horizontal overflow. A real short pilot launched from the UI and automatically opened results; a further real pilot job was cancelled through the Stop control with partial records preserved. Larger-run confirmation was shown and dismissed without authorizing the full workload.

The dashboard was also started from the freshly installed environment for the delayed-response regression. After checks, both service instances were stopped and localhost port closure verified; the idle background restart required SIGTERM after SIGINT did not close it. Screenshots reflect their actual capture-time checkout and execution ledger, before the final review commits, not a fabricated final hash.

The dashboard tests exercise command allowlists, malformed records, filtering, numeric consistency, CSV/Markdown export, process cancellation/timeout and security boundaries. Final browser checks completed filtered CSV/Markdown/SVG downloads, sorting, deterministic explanation and campaign transaction drill-down; evidence is in `verification/browser-exports.json`, `verification/browser-details.json` and the downloaded files. Earlier unfinished automation is not treated as a passing check. Prior historical browser coverage remains separately labelled.

The IEEE conference draft was built using official IEEEtran and Tectonic 0.17.0, with five pages, IEEE references and embedded fonts. `qpdf --check` returned zero; all pages were inspected, and an initially clipped benign-chart title/axis was wrapped and rechecked. The editable nine-slide deck was repaired/validated by the Office utility, rendered with LibreOffice, independently visually reviewed and corrected for chart/link contrast, screenshot size, explicit campaign total and footer spacing. Rendered PDF previews are provided; no claim of university checker compliance follows from rendering.

## Verified results and their limits

The retained pilot has 7,200 attack campaigns, 3,539 complete, 28,895 evaluated transactions, 24,634 ALLOW, 600 FLAG and 3,661 BLOCK decisions. Gross simulated debit is INR 192,300,996.32, not actual victim loss or money saved. `results/independent_reconstruction.json` and the referenced raw-record hashes support each total.

Legitimate GE mimics were blocked in 1,738/3,600 XGBoost episodes (48.278%) and 461/3,600 Random Forest episodes (12.806%); zero BLOCK was observed on ordinary benign episodes, not guaranteed in a population. Nine independent pilot blocks support exploratory summaries, not powered confirmatory findings. The stronger checker adds verification assertions, not experimental observations; its count differs from the historical 1,012,666.

Legacy and pilot results remain separate. Historical detector-family exclusion is unverified; new pilot provenance supports only the registered synthetic development/mechanism exclusion. No universal RL superiority, proven adaptation paradox, general unseen-fraud detection, validated AUC, production readiness or real-world UPI effectiveness is claimed.

## Failed attempts and corrections

- **Nested-path failure**: the first HTTP workflow completed legacy main, then repeat submission failed with HTTP 400 because the repository root captured an approved hidden local-state path first. Root order was fixed, a regression added, and the completed main was reused in the successful continuation; both attempt logs remain.
- **Paper build failures**: the first build used a wrong relative Tectonic path (127); another failed on table placement/encoding (1). Corrected generated table structure and T1 font encoding built successfully; logs are retained, not recast as successes.
- **Visual issues**: the first deck review found low contrast and a small screenshot; later PDF inspection found clipped benign-figure labels. Presentation-only corrections were rendered and inspected.
- **Browser-script failures**: attempts to select a run while its selector was intentionally hidden on Runner timed out; an overly precise percentage wait stalled. These are automation errors, not passed controls or evidence of model failure.
- **Export race**: the first CSV download preceded completion of its filter refresh and contained the earlier selection. This exposed a genuine frontend race, not just an automation mistake; loading guards were added and a delayed-response regression passed. The incorrect earlier-selection file is retained separately, never used for reported metrics.

The broad whitespace check reports preserved compiler/test-output whitespace, official IEEE class/license whitespace and Matplotlib-generated SVG formatting. Those bytes are intentionally retained. A CR-aware check of implementation/current prose excluding those generated/evidence/vendor paths passes; no test failure or assertion is waived by this formatting distinction.

## Acceptance and remaining actions

`REQUIREMENT_STATUS.csv` records each mission part. Software/reproduction checks establish exercised behavior and record integrity only; they do not establish scientific generalization or external deployment validity. Read the [handover](HANDOVER.md), [paper instructions](../research/paper/README.md) and [external checks](../research/review_materials/EXTERNAL_CHECKS.md) before submission.

Required human actions are approval of authors/institution, venue/page limit and the AI-assisted draft; use of university-approved checkers on the exact final document; an appropriate copyright-holder license decision; and review of the comprehensive PR without merging it automatically. Scientific validity is assessed only to the extent supported by the audit and recorded evidence. Gate C remains HOLD.

## GitHub outcome

[PR #1](https://github.com/YuvakarthikKoduri/Campaign-Level-Adversarial-Stress-Testing-of-UPI-Fraud-Detection-Systems/pull/1) is open from the feature branch into `master`. No merge or automatic merge was requested, and the default branch was not pushed. The creation-time receipt, successful feature push and rejected workflow-scope attempt are preserved in `verification/`; there is no active GitHub CI result.
