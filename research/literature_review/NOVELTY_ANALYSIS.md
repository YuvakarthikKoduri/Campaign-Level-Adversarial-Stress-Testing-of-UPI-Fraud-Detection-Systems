# Literature scope and qualified contribution

This is a focused scoping review, not a systematic review or proof that no similar work exists. Searches on 26 October 2026 UTC covered financial fraud, banking evasion, RL fraud attacks, synthetic financial data, sequences, drift and reproducibility; selection favored primary proceedings, publisher abstracts and accessible papers.

## Prior work and reading depth

- **Closest overlap:** Fraud-RLA already studies learning attackers against credit-card fraud detectors. The 2026 journal article is verified on the [IEEE Computer Society page](https://www.computer.org/csdl/journal/tq/2026/03/11434559/2ePhI6GUJI4); detailed methods were read in its [2025 v1 preprint](https://arxiv.org/html/2502.02290v1), not silently attributed to an unread journal full text.
- **Banking attacks:** [Carminati et al.](https://www.usenix.org/conference/raid2020/presentation/carminati) already evaluate evasion on real bank datasets. This project cannot claim that attacking a financial detector or varying attacker information is new.
- **Sequential fraud:** [Srivastava et al.](https://doi.org/10.1109/TDSC.2007.70228) model cardholder transaction sequences. Campaign-level evaluation is useful here because first BLOCK truncates later actions and FLAG can still transfer funds, not because sequences are a new research idea.
- **Synthetic finance:** [PaySim](https://www.msc-les.org/proceedings/emss/2016/EMSS2016_249.pdf) and [Assefa et al.](https://doi.org/10.1145/3383455.3422554) precede this simulator. PaySim's 2016 paper explicitly places fraud injection/detector evaluation outside its scope; do not substitute claims from later dataset versions.
- **Evaluation discipline:** [Dal Pozzolo et al.](https://doi.org/10.1109/TNNLS.2017.2736643), [Gama et al.](https://doi.org/10.1145/2523813), [TESSERACT](https://www.usenix.org/conference/usenixsecurity19/presentation/pendlebury) and [Henderson et al.](https://doi.org/10.1609/aaai.v32i1.11694) motivate operational metrics, distribution-aware evaluation, split integrity and replication, respectively.

The full PaySim paper, Fraud-RLA v1 methods/results and a concept-drift survey extract were available. Other rows are deliberately limited to fetched publisher/proceedings abstracts and verified metadata; unspecified datasets, exact algorithms and metrics remain explicitly unspecified. Jurgovsky et al. (2018), DOI 10.1016/j.eswa.2018.01.037, was discovered and metadata verified, but full-text/abstract access attempts were insufficient; it is not used to support methodological claims.

## What this implementation adds

The defensible contribution is an academic engineering artifact combining a synthetic ledger, first-BLOCK campaign termination, five matched pilot controls, artifact-bound exclusion of one declared synthetic mechanism, benign mechanism-shift controls, checkpoint/frozen-state verification, independent record reconstruction and a safe local dashboard. Inspect `src/experiments/mechanism_pilot.py`, `verify_mechanism_pilot.py`, `scripts/reproduce_paper.py`, `dashboard/` and `results/artifacts/`.

This combination is implemented and reproducible within the recorded environment. It is not established as the first such combination, a new RL algorithm, a superior detector, or an externally validated UPI system.

## Research gap and supported finding

A useful bounded question is whether a declared synthetic fraud-mechanism exclusion, by itself, yields useful discrimination when legitimate episodes share that mechanism. The retained pilot supplies an adverse case: legitimate gradual-escalation mimics are frequently blocked, despite no observed ordinary-benign BLOCK. This is evidence about the registered generator and four-feature representation, not proof that the same cause or rate holds in real financial systems.

The empirical contribution is an auditable case study of the mismatch between mechanism exclusion and useful discrimination, with matched-policy contrasts whose direction varies by detector. Literature comparisons are qualitative because datasets, budgets, features, units and threat models differ. No published method was reimplemented or benchmarked head-to-head here.

## Demonstrated, unverified and future

- **Demonstrated:** Recorded execution, narrow synthetic holdout provenance, policy freeze, simulator outcomes and benign-shift failures. The source-bound verifier and independent reconstruction provide the evidence.
- **Unverified:** Historical detector ancestry; broad detector-unseen fraud; realistic UPI population behavior; universal RL gains; causal explanations for false blocking; confirmatory statistical power.
- **Future:** Approved external data, independently custodied lockbox, pre-registered operating points, richer features, query-cost-matched policies and powered replication. These are proposals, not completed features or results.

The review covers eleven distinct works, counting the Fraud-RLA preprint and journal as one line of work. It is intentionally bounded; missing terminology, inaccessible full texts and publication coverage leave novelty uncertainty.
