# Experimental methodology

Two versions are intentionally separate. The corrected legacy study evaluates all four legacy campaign families through asymmetric attacker interfaces; its three seeds and historical detector ancestry limit inference. The matched mechanism-pilot v1 evaluates only HVB and GE, with nine independent data/model/policy blocks and 40 paired contexts per detector/arm/family/block.

## Registered pilot contract

- **Data roles:** Per block, 1,000 balanced-by-episode fit episodes, 400 allowed-family validation episodes, 1,000 ordinary-benign calibration episodes and 400 each ordinary/GE-mimic benign test episodes. Episode registries and actual fit rows are preserved.
- **Holdout:** GE generator ancestry and nontrivial matching prefixes are excluded from fit/validation/calibration; matching benign candidates are quarantined, not relabeled. This is a narrow grammar/lineage claim, not feature-value separation or all-unseen fraud.
- **Detectors:** XGBoost 100 trees/depth 4 and RF 150 trees/depth 8; fixed hyperparameters; amount/hour/source-hour velocity/new-beneficiary features; no fitted scaler or SMOTE.
- **Controls:** Static and rule share a kernel with neutral/actual last label. Trained RL and label-blind RL use common training contexts/quota/rewards; blind masks the explicit label, not detector-dependent rewards. Zero-Q does not load trained values.
- **Online matching:** Same legal grammar, four nominal amount bands, final clipping, 300/1,200-second choices, target-sized gross budget, 30 proposals, 86,400 seconds and 20,000–40,000 INR targets. Offline training costs are unequal across learned versus nonlearned policies.
- **Thresholds:** Ordinary-benign episode maxima with deterministic order-statistic/tie handling; nominal empirical budgets 0.5% BLOCK/2.5% any-alert. Calibration data do not certify population behavior.
- **Learning:** 300 HVB training episodes per learned arm/detector/block; alpha 0.25, gamma 0.95, legal TD bootstrap, zero terminal bootstrap, decaying exploration and zero evaluation exploration. Seeded ties remain possible.
- **Evaluation:** 7,200 attack campaigns and 10,800 learned-policy training episodes in the retained full main run. Repeat is same-seed reproduction; reload performs no fitting/training. Neither adds independent statistical replication.

## Analysis and provenance

The independent unit is the block. Six GE paired completion contrasts use exploratory, unadjusted block-resampling intervals; the current paper reconstruction fixes seed 20261026 and 10,000 draws. Do not treat campaigns or transactions as independent model replications. Nine blocks are not a prospective power calculation, and five percentage points is only a sensitivity reference.

`docs/MECHANISM_PILOT_DESIGN.md` remains byte-preserved because its hash is bound into the retained run. Full registries, quarantine, fit rows, manifests, models, policies, training transitions and scored benign episodes are under restored `.local/retained/pilot-main/`. The independent verifier checks recorded lineage and replays TD updates. There is no untouched final confirmatory lockbox or real-world validation.

Protocol v2 is preserved under `docs/history/RESEARCH_PROTOCOL_V2.md` as future design, not fully executed work. This integration ran short demonstrations and reanalyses, not a new full study or new threshold search.
