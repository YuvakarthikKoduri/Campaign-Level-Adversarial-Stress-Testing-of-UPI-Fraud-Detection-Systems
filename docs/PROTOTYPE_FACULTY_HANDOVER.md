# Prototype branch faculty-review handover

This update adds an eight-slide presentation and clear branch-specific run instructions without changing the historical research engine, detector artifacts, datasets or retained experiment records. The exact requested remote branch is `prototype/rl-academic-complete`; the inspected research-code baseline is `92a12966ec49fd6dcd147fd4d7411382715bc729`.

## Deliverable contract and scope

The audience is a university lecturer. The presentation must explain what the project is, the problem, implemented architecture, four attacker controls, branch-specific results, bounded contribution, terminal demonstration and limitations in exactly eight editable slides; the PDF is a preview, not the editable file.

The README must let a new researcher clone the correct branch, install its pinned dependencies, run a small demo, inspect outputs and evaluate a checkpoint. The IEEE check must inspect the existing draft without claiming human authorship, an AI-free result or an unmeasured similarity score.

The chosen presentation style is a restrained teal/charcoal/white workstation aesthetic with native text, process shapes and one native chart. No later dashboard screenshot or pilot result is presented as a feature/result of the older prototype.

## Newly executed verification

The existing compatible Python 3.11 environment was reused. Commands ran from an isolated Git worktree, with new outputs outside the repository; no full-scale historical experiment was rerun and no clean installation is claimed.

| Check | Actual result |
|---|---|
| `python -B -s run_prototype.py --help` | Exit 0; detector and attacker choices checked against the real CLI |
| `python -B -s -m pytest tests/test_prototype_rl.py -q` | Exit 0; 47 passed, no failures/skips/deselections; one existing model-serialization warning |
| Short main, both detectors, all attackers, seed 101, episodes 2, campaigns 1 | Exit 0; 16 evaluated campaigns |
| Same configuration with `--policy-dir` pointing at short main | Exit 0; 16 evaluated campaigns; campaign JSON equal to main |
| Historical-record recalculation | 3,509 assertions passed; counts/decisions/debit/summary consistency, not a scientific-validation sign-off |
| IEEE source recompilation with Tectonic | Exit 0; five pages; compiler warnings retained |

The first local reconstruction script counted 3,509 assertions, including one assertion pinning the historical input's expected size. The portable `scripts/recalculate_prototype_snapshot.py` uses 3,508 arithmetic assertions without that extra fixed-size assertion; do not combine the counts or call them independent statistical replications.

The short-run manifest reports 16 inherited training updates on reload, because this older implementation carries checkpoint training history. It records zero evaluation updates; neither that counter nor a passing old test suite proves complete persisted Q-table equality. Later audits fixed evaluation-state and other defects on the separate review branch, not here.

## Where to start

- **Run instructions:** [README](../README.md), including Linux/WSL2 setup, CLI options, reload, tests and output definitions.
- **Presentation:** [editable eight-slide PPTX](../research/review_materials/UPI_PROTOTYPE_FACULTY_8_SLIDES.pptx), [PDF preview](../research/review_materials/UPI_PROTOTYPE_FACULTY_8_SLIDES.pdf), [source/build guide](../research/review_materials/PROTOTYPE_PRESENTATION_README.md).
- **Historical source records:** `prototype_evidence/comparison-final/`; the new `prototype_snapshot.json` contains source fingerprints, reconstructed totals and summary cells.
- **Paper status:** [IEEE recheck](IEEE_REPORT_STATUS.md), including the later draft's actual scope and external-check requirements.

Use the README's short configuration for faculty demonstration, not the historical full-run command. A successful small run demonstrates execution but does not reproduce the retained full study's numerical results.

## Important interpretation

The prototype records contain 1,152 campaigns and 4,189 transactions; later corrected legacy records contain 4,161 transactions and the separate matched pilot contains 7,200 campaigns. Those are different evidence versions, not discrepancies to hide by editing the raw outputs.

Three workload families were held out from attacker training, not demonstrably from the old detector training. Legacy attacker comparisons retain action/pacing/clipping/offline-cost confounds, and gross simulated debit is not victim loss or proven savings.

The full dashboard, current evidence package, literature matrix and IEEE draft remain on `review/academic-dashboard-paper-v1`. This documentation update does not make the older prototype scientifically equivalent to that branch.

## Git and preservation boundary

The original prototype commit remains in history. Additions are confined to the faculty documentation, eight-slide presentation/source/snapshot and a read-only arithmetic helper; no research-engine repair is claimed.

The default branch is not a push target, no PR is merged, and no release or Gate C workflow is invoked. Final publication SHA, file inventory, rendering checks and any visual corrections are recorded in `PROTOTYPE_FACULTY_VERIFICATION.md` alongside this handover.
