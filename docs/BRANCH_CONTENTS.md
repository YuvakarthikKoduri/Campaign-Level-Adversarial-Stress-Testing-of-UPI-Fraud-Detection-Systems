> HISTORICAL SCOPE RECORD: The body below retains earlier claims and workspace paths, not current acceptance. Use the [current README](../README.md), [verification report](VERIFICATION_REPORT.md) and [handover](HANDOVER.md) for present commands, counts and limitations. Historical completion/AUC/novelty/production claims are not adopted. Gate C remains HOLD.

# Academic prototype branch contents

## Historical branch description

The body describes the previous candidate, not the new private branch.
Current branch is `research/mechanism-holdout-pilot` at uncommitted base HEAD
`92a12966ec49fd6dcd147fd4d7411382715bc729`. See `../../FILE_CHANGES.md`,
`../../HANDOVER.md` and `../../FINAL_AUDIT_REPORT.md`.
No Gate C workflow is authorized; its existing documents are retained
historical specifications, not readiness or execution approval.

This branch packages the completed ordinary-development prototype from
`/home/user/workspace/upi-prototype-dev`. Its parent is the inspected prototype
baseline commit `c2634021a1979c912755bfef7987e35d03e8b78e`; the existing
`prototype/rl-academic` branch and original Gate C checkout are not rewritten.

## Included

- RL attacker, simulator lifecycle integration and independent prototype CLI.
- Existing baseline XGBoost and Random Forest models and synthetic legacy CSV,
  inherited unchanged from the parent commit.
- Core/milestone/Gate B and RL test source, with executed baseline and final
  logs/JUnit evidence. The selected expanded suite reported 201 passes.
- Saved Q policies, per-seed metrics, campaign/transaction traces, learning
  curves and figures under `prototype_evidence/comparison-final/`.
- Full repeat and checkpoint-only evaluation directories, plus the reusable
  reproducibility verifier and its successful JSON comparison evidence.
- Completion report, setup/run guide, presentation/demo brief and architecture
  diagram. Earlier failed baseline evidence remains preserved.

## Excluded

The extracted `prototype_evidence/package-check/` duplicate, virtual environments,
caches, local Git configuration/credentials and delivery ZIP files are excluded.
The transaction records and VPA identifiers in the included experiment outputs
are synthetic controlled-account fixtures, not personal financial records.

Gate C production, staging, approval and execution paths are not part of this
development snapshot. No Gate C pilot workflow is invoked by creating or
publishing this branch, and the pilot remains on HOLD.

Read `PROTOTYPE_COMPLETION_REPORT.md` for exact experiment/test commands and
limitations, and `docs/PROTOTYPE_GUIDE.md` to reproduce the demonstration.
