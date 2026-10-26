# Literature verification scope

This focused search was performed on 26 October 2026 UTC. It is not a systematic review or evidence that no similar system exists; eleven distinct works are compared, with the Fraud-RLA journal article and preprint treated as versions of one work.

## Reading depth and identity

| Work | Verified publication identity and reading depth |
|---|---|
| Dal Pozzolo et al. | IEEE TNNLS 29(8), 3784–3797, 2018; publisher abstract/introduction, not full experimental replication ([publisher DOI](https://doi.org/10.1109/TNNLS.2017.2736643)). |
| Carminati et al. | RAID 2020, 285–300; official proceedings abstract, two banking datasets and knowledge-dependent evasion findings ([USENIX](https://www.usenix.org/conference/raid2020/presentation/carminati)). |
| Lunghi et al., Fraud-RLA | IEEE TDSC 23(3), 7468–7481, 2026; journal metadata/abstract and full 2025 v1 preprint methodology, explicitly distinguished rather than assumed identical ([IEEE record](https://www.computer.org/csdl/journal/tq/2026/03/11434559/2ePhI6GUJI4), [preprint](https://arxiv.org/html/2502.02290v1)). |
| Srivastava et al. | IEEE TDSC 5(1), 37–48, 2008; publisher abstract, sequential HMM detection, no invented dataset or reproduced score ([publisher DOI](https://doi.org/10.1109/TDSC.2007.70228)). |
| Lopez-Rojas et al., PaySim | EMSS 2016, 249–255; full proceedings paper, distinguished from later public dataset variants ([proceedings PDF](https://www.msc-les.org/proceedings/emss/2016/EMSS2016_249.pdf)). |
| Assefa et al. | ICAIF 2020, article 44, pp. 1–8; publisher metadata/abstract on synthetic-data opportunities and pitfalls ([ACM DOI](https://doi.org/10.1145/3383455.3422554)). |
| Gama et al. | ACM Computing Surveys 46(4), article 44, 2014; publisher metadata/abstract plus survey text, not a financial fraud benchmark ([ACM DOI](https://doi.org/10.1145/2523813)). |
| Pendlebury et al., TESSERACT | USENIX Security 2019, 729–746; official abstract on spatial/temporal bias in malware classification, not UPI evidence ([USENIX](https://www.usenix.org/conference/usenixsecurity19/presentation/pendlebury)). |
| Henderson et al. | AAAI 32(1), 2018; official article abstract/metadata, seed/reporting sensitivity, not a detector benchmark ([AAAI](https://aaai.org/papers/11694-deep-reinforcement-learning-that-matters/)). |
| Chen and Guestrin | KDD 2016, 785–794; publisher metadata/abstract for the detector method, not an adversarial-fraud result ([ACM DOI](https://doi.org/10.1145/2939672.2939785)). |
| Breiman | Machine Learning 45, 5–32, 2001; publisher metadata/abstract for Random Forests, not a campaign simulator ([publisher DOI](https://doi.org/10.1023/A:1010933404324)). |

The bibliography contains twelve entries because the Fraud-RLA preprint is cited separately for methods read in that version. Some sources were available only as abstracts; matrix cells explicitly limit detail accordingly. Jurgovsky et al. was considered but insufficient accessible methodology was recovered for detailed matrix claims, and it is not used as an evaluated comparator.

## Search and claim boundaries

Searches covered financial fraud, banking evasion, reinforcement-learning attackers, sequence evaluation, synthetic financial data, distribution shift and experimental reproducibility. Prior work already establishes sequential fraud modelling, adaptive evasion, RL attacks, simulation and bias-aware evaluation; the project does not claim invention of those ideas ([novelty analysis](NOVELTY_ANALYSIS.md)).

The contribution is qualified as an integrated, inspectable academic engineering/evidence package for its declared synthetic mechanisms. Matrix comparisons are conceptual; no paper's benchmark was rerun, and cross-paper numerical superiority is not asserted. Primary-source URLs were opened during research, not verified solely by plausible-looking titles or generated bibliography entries.
