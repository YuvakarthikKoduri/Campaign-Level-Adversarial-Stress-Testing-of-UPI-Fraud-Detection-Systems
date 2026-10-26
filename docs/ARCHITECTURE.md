# Architecture and source map

![Implemented architecture](images/architecture.svg)

The legacy path is `run_prototype.py` → `src/experiments/prototype.py` → campaign executor/environment, detector adapters and policies. The additive matched path is `src/experiments/mechanism_pilot.py`; it does not rewrite legacy reward or models. `src/attackers/q_learning.py` contains tabular updates, legal masks, terminal handling and frozen evaluation; `src/money.py` supplies integer-paise bookkeeping.

The dashboard separates `dashboard/server.py` (loopback HTTP and request controls), `dashboard/runner.py` (fixed argv, job serialization, timeout/cancellation and logs), `dashboard/records.py` (registered evidence and derived views), and `dashboard/static/` (presentation). `run_dashboard.py` is the startup entry.

`scripts/restore_evidence.py` rebuilds a local evidence catalog from the versioned content-addressed ZIP. `verify_prototype_outputs.py` and `verify_mechanism_pilot.py` perform protocol-aware record checks. `scripts/reproduce_paper.py` is a separate raw-record arithmetic/analysis path, not a call into the dashboard's result parser.

Evaluation does not update policies or refit detectors. Training and reload mode are explicit in manifests, and persisted state/model hashes bind outputs. A successful UI job is distinct from a passed protocol checker, which is distinct from a scientifically generalizable result.

Gate C is unchanged and HOLD. This integration does not expose or execute its workflows.
