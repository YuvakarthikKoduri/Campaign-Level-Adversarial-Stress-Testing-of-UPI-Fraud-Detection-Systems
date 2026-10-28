# Prototype faculty presentation

The audience is a university lecturer evaluating what this project implements, why campaign-level stress testing is useful, what the retained records actually show and how to run a small demonstration. The deliverable is exactly eight native, editable PowerPoint slides, with speaker notes and an eight-page PDF preview.

## Content and scope

The source is `prototype/rl-academic-complete`, research-code baseline `92a12966ec49fd6dcd147fd4d7411382715bc729`. Counts, chart values and limitations describe that older implementation; no later corrected legacy or matched-pilot totals are presented as its results.

| Slide | Main point |
|---|---|
| Project pitch | A synthetic campaign laboratory, not deployed payment protection |
| Why campaigns | ALLOW/FLAG/BLOCK have different consequences |
| Architecture | Workload, attacker, ledger/detector and raw outcomes |
| Attacker controls | Static, rule-adaptive, trained RL and zero Q |
| Retained results | 1,152 campaigns; 4,189 transactions; three seeds |
| Contribution | A bounded engineering combination, not priority or superiority |
| Terminal demonstration | Supported small CLI configuration and output locations |
| Review conclusion | What is implemented, limited and pending human approval |

`prototype_snapshot.json` contains a fresh read-only reconstruction of the historical record counts and summary cells, source SHA-256 values and the experiment identity. It is not a new full-scale experiment or a scientific-validation certificate.

## Rebuild

The presentation build is optional and separate from the Python research environment. It uses the MIT-licensed PptxGenJS library, version 4.0.1 in the verification environment; install that version locally if it is not already available.

```bash
npm install --no-save pptxgenjs@4.0.1
node research/review_materials/prototype_slides/compile.js
```

Run the build from the repository root. Text, process diagrams and the comparison chart are native editable objects, not screenshots of rendered slides; speaker notes include metric scope, seed variability and source locations.

The GitHub-hosted PowerPoint skill used is [MiniMax's MIT-licensed pptx-generator](https://github.com/MiniMax-AI/skills/tree/60aaae52bb2af8162732751a4332f62a5fef518b/skills/pptx-generator), imported at commit `60aaae52bb2af8162732751a4332f62a5fef518b` and saved in the user's personal skills library. Its instructions and bundled references were locally validated before saving; no proprietary Anthropic skill was redistributed.

The rendered PDF is a preview, not an editable replacement for the PowerPoint file. See [the handover](../../docs/PROTOTYPE_FACULTY_HANDOVER.md) for executed checks and known limitations.
