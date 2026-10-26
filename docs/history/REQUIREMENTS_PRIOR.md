# Final Requirement Audit

COMPLETE means the scoped action was executed and evidenced, not universal scientific validation. PARTIAL identifies narrower evidence; BLOCKED identifies missing required evidence; NOT IMPLEMENTED records deliberately absent work.

| Requirement | Status | Evidence / boundary |
|---|---|---|
| Repository, branch, HEAD, Git state and artifact audit | COMPLETE | Initial/final Git logs; `artifact-audit.stdout`; before/after inventories |
| Preserve original candidate and prior closeout | COMPLETE | `preservation-final-02.json`; unchanged old package SHA; no source/model/data overwrite |
| Existing RL, terminal/reward, limits, checkpoints and frozen evaluation | COMPLETE | 364 baseline cases, final regression, fresh legacy triplet; legacy implementation unchanged |
| Five matched controls | COMPLETE | `mechanism_pilot.py`, frozen design, common action masks/resources/outcomes; offline learning cost not matched |
| Four existing family implementations | PARTIAL | Legacy generator/suite covers all four; new mechanism-pure pilot covers HVB/GE only |
| Historical detector-training exclusion | BLOCKED | Old model/data metadata lack artifact-bound family ancestry; not repaired by new fits |
| New GE mechanism-level fitting exclusion | COMPLETE | Registered fit/validation/calibration roles, quarantine/prefix checks, fit bindings and independent verifier; not feature-support OOD |
| Matched holdout tests for slow drain and hopping | NOT IMPLEMENTED | No new holdout study for these mechanisms |
| Benign calibration and operating-point reporting | COMPLETE | Per-model calibration, declared empirical caps, ordinary/mimic tests |
| Useful unseen-fraud discrimination / benign robustness | PARTIAL | Evaluated, but high GE-mimic false BLOCK is a substantial negative result |
| Multiple independent seeds/models | COMPLETE | Nine independent blocks, 18 model fits, seed/model inventory; repeats not extra replications |
| Powered confirmation / independent lockbox | NOT IMPLEMENTED | Exploratory variance pilot only |
| Complete feasible explicit regression selection | COMPLETE | 410 passed, zero skips/deselections; 47 RL overlap, not extra cases |
| End-to-end fitting, learning, save/reload, output checking | COMPLETE | Main/repeat/reload with 7,200 campaigns each; reload zero fitting/training |
| Raw config, dataset/model/source identities and logs | COMPLETE | `evidence/pilot-*`, fit bindings, command journal, seed inventory |
| Independent metric and TD reconstruction | COMPLETE | 1,012,666 checks; all 30,985 TD updates replayed |
| Money/exposure/timing distinctions | COMPLETE | Independent metric tables separate gross debit, BLOCK-proposed amount and conditional timing; not victim loss |
| Reconciled current documentation and academic handover | COMPLETE | Current reports and current-authority headers; old claims explicitly historical |
| Real-world robustness / production readiness | BLOCKED | No external data or live payment validation; not supported by synthetic evidence |
| Gate C / downstream release | NOT IMPLEMENTED | HOLD; no workflow run/prepared, commit, push, merge, publication or release |

The final disposition is qualified academic-review readiness for a synthetic engineering case study. Major scientific limitations remain visible; this is not an all-research-objectives-complete sign-off.
