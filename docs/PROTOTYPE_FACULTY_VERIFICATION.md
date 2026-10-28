# Prototype faculty package: final verification

This is a documentation/presentation update for `prototype/rl-academic-complete`, not a research-engine remediation or a new full study. The baseline is `92a12966ec49fd6dcd147fd4d7411382715bc729`; the local preparation branch is `docs/prototype-faculty-eight-slides`, with the same final commit pushed by fast-forward to the requested remote prototype branch.

## Actual checks

The reused Python 3.11 environment passed 47 existing RL cases, with one known XGBoost serialization warning and no failures, skips or deselections. A new main/reload demonstration used both detectors, all four controls, seed 101, two training episodes per detector and one campaign per workload/strategy/detector cell.

Both commands exited 0 and produced 16 evaluation campaigns. The main and reload campaign JSON records were equal; this does not establish complete persisted-policy immutability for the older implementation.

```bash
python -B -s run_prototype.py --help
python -B -s -m pytest tests/test_prototype_rl.py -q
python -B -s run_prototype.py --detector both --attacker all \
  --seeds 101 --episodes 2 --campaigns 1 --output NEW_MAIN
python -B -s run_prototype.py --detector both --attacker all \
  --seeds 101 --episodes 2 --campaigns 1 \
  --policy-dir NEW_MAIN --output NEW_RELOAD
python -B scripts/recalculate_prototype_snapshot.py --output NEW_CHECK.json
```

`NEW_MAIN`, `NEW_RELOAD` and `NEW_CHECK.json` stand for fresh paths, not literal previously populated directories. The private execution journal retains the exact resolved paths, commands, elapsed durations, exit codes, stdout/stderr and JUnit XML; public instructions avoid dependence on a private sandbox environment path.

The initial local record-reconstruction script passed 3,509 assertions. The portable helper passed 3,508 arithmetic assertions and independently reproduced the same counts: 1,152 campaigns, 1,077 completed, 4,189 transactions, 3,229 ALLOW, 885 FLAG, 75 BLOCK and INR 29,196,913.14 gross simulated debit.

The count difference between the two scripts is one additional fixed historical-size assertion in the initial script. They inspect the same data, not independent experiment replications.

## PowerPoint and PDF

The deck has exactly eight slides, one native comparison chart and no raster slide pictures. XML parsing, ZIP integrity, internal relationships, content read-back and an eight-page PDF preview were checked; these checks are not a full Office XSD certification or a test in Microsoft PowerPoint itself.

An independent visual reviewer inspected all eight initial slide images and all five IEEE draft page images. No clipping or overlaps were found; suggested refinements included chart-scope labeling, caption/terminal size, arrow contrast, spacing and alignment.

The source was revised, rebuilt, repaired and rendered again. Final visual reinspection checked the eight-slide contact sheet and the detailed results slide; the high-value-burst subset is now explicit, process arrows are stronger, text is larger and the two contribution columns align.

PptxGenJS 4.0.1 generated the file. The Office OOXML repair applied 38 normalizations to the final build; the PDF passed `qpdf --check` with exit 0.

The final chart shows historical known/high-value-burst completion only, 72 campaigns per arm/detector across three seeds. Seed standard deviations are retained in speaker notes; no confidence intervals or causal advantage are claimed.

## IEEE report recheck

The existing later-study source compiled with Tectonic 0.17.0, exit 0, to five US-letter pages. Its PDF passed `qpdf --check`; compiler underfull-line and font-shape warnings were retained, and embedded Times-compatible body fonts were inspected with `pdffonts`.

The author/institution placeholder is intentionally unresolved, not an authorized researcher identity. The official class specifies bold abstract text; it was not restyled to evade AI detection, and the sparse final references column was not filled with invented content.

No approved AI-content or similarity report was obtained. The IEEE draft is AI-assisted and both requirements remain PENDING EXTERNAL VERIFICATION; see [the exact status and human steps](IEEE_REPORT_STATUS.md).

## Changes and preservation

The modified file is `README.md`. Additions are:

- `docs/IEEE_REPORT_STATUS.md`
- `docs/PROTOTYPE_FACULTY_HANDOVER.md`
- `docs/PROTOTYPE_FACULTY_VERIFICATION.md`
- `research/review_materials/PROTOTYPE_PRESENTATION_README.md`
- `research/review_materials/UPI_PROTOTYPE_FACULTY_8_SLIDES.pptx`
- `research/review_materials/UPI_PROTOTYPE_FACULTY_8_SLIDES.pdf`
- `research/review_materials/prototype_snapshot.json`
- `research/review_materials/prototype_slides/common.js`
- `research/review_materials/prototype_slides/compile.js`
- `research/review_materials/prototype_slides/slide-01.js` through `slide-08.js`
- `scripts/recalculate_prototype_snapshot.py`

The code/data/model/original-record paths are unchanged against the baseline, and selected source-record SHA-256 fingerprints are rechecked. The old README remains available in Git history; historical raw outputs were not “corrected” to agree with newer studies.

The user-requested MiniMax MIT PowerPoint skill was installed in the personal skill library after package validation. Its source commit and license are documented in the presentation build guide; no runtime dependency was added to the research engine's lock.

No default-branch push, merge, release, expensive full experiment or Gate C action is part of this update. The final pushed SHA and the working-tree result are recorded in the delivery receipt; scientific and external-check limitations remain explicit.
