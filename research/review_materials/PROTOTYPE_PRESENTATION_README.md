# Prototype faculty presentation

The audience is a university lecturer evaluating what this project implements, why campaign-level stress testing is useful, what the retained records actually show and how to run a small demonstration. The deliverable is exactly eight native, editable PowerPoint slides, with speaker notes and an eight-page PDF preview.

## Content and scope

The source is `prototype/rl-academic-complete`, selected by the project owner as the final project branch for this faculty presentation, research-code baseline `92a12966ec49fd6dcd147fd4d7411382715bc729`. Counts, chart values and limitations describe that implementation; no later corrected legacy or matched-pilot totals are presented as its results. The cover credits guide Dr S. KALYANI and the five supplied student names/IDs; no phone numbers or chat timestamps are included.

| Slide | Main point |
|---|---|
| Project pitch | A synthetic campaign laboratory, not deployed payment protection |
| Why campaigns | ALLOW/FLAG/BLOCK have different consequences |
| Architecture | Workload, attacker, ledger/detector and raw outcomes |
| Attacker controls | Static, rule-adaptive, trained RL and zero Q |
| Retained results | 1,152 campaigns; 4,189 transactions; three seeds |
| Terminal results | Exact saved stdout, with success, exposure and workload labels explained |
| Terminal demonstration | Supported small CLI configuration and output locations |
| Master comparison | Earlier baseline versus the selected final prototype; reused core and actual additions |

`prototype_snapshot.json` contains a fresh read-only reconstruction of the historical record counts and summary cells, source SHA-256 values and the experiment identity. It is not a new full-scale experiment or a scientific-validation certificate.

`prototype_terminal_excerpt.json` records the previously executed short demo's exact selected stdout lines, original log hashes and underlying output-file hashes. Its 16 campaigns are separate from the 1,152-campaign retained study. Slide 5 explains pooled completion (1,077 / 1,152 = 93.490%); its chart is explicitly only the high-value-burst subset. Slide 8 compares `master` at `1e2ca9e` with prototype at `25c2830`, before this documentation revision; there is no controlled master-versus-prototype performance experiment.

## Rebuild

The presentation build is optional and separate from the Python research environment. It uses the MIT-licensed PptxGenJS library, version 4.0.1 in the verification environment; install that version locally if it is not already available.

```bash
npm install --no-save pptxgenjs@4.0.1
node research/review_materials/prototype_slides/compile.js
```

Run the build from the repository root. Text, process diagrams and the comparison chart are native editable objects, not screenshots of rendered slides; speaker notes include metric scope, seed variability and source locations.

The GitHub-hosted PowerPoint skill used is [MiniMax's MIT-licensed pptx-generator](https://github.com/MiniMax-AI/skills/tree/60aaae52bb2af8162732751a4332f62a5fef518b/skills/pptx-generator), imported at commit `60aaae52bb2af8162732751a4332f62a5fef518b` and saved in the user's personal skills library. Its instructions and bundled references were locally validated before saving; no proprietary Anthropic skill was redistributed.

The rendered PDF is a preview, not an editable replacement for the PowerPoint file. See [the handover](../../docs/PROTOTYPE_FACULTY_HANDOVER.md) for executed checks and known limitations.

The [presentation revision record](../../docs/PROTOTYPE_PRESENTATION_REVISION.md) covers the subsequent team credits, exact terminal excerpts, plain-English results interpretation and verified master-to-prototype comparison. The earlier verification report remains preserved as a historical execution record.
