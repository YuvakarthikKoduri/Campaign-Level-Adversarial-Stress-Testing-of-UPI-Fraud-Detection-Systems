# Prototype faculty presentation: team, terminal results and branch comparison

This revision keeps the presentation at eight editable slides and makes `prototype/rl-academic-complete` the explicitly selected final project branch for the faculty presentation. Final selection is a project-delivery decision, not proof of real-world effectiveness or the absence of known research limitations.

## Requested additions

- **Team:** Guide Dr S. KALYANI; students 24BCA7401 - SHAURYA SINGH, 24BCA7167 - K.H.A.Revanth, 24BCA7171 - K Yuva Karthik, 24BCE7026 - Likith R, and 24BCA7040 - Hima Tejaswi. Phone numbers and chat timestamps are excluded.
- **Results and meaning:** Slide 5 explains that 1,077 of 1,152 retained simulated campaigns reached their target, or 93.490% pooled completion. This is attacker campaign completion, not detector accuracy; its chart is explicitly the high-value-burst subset.
- **Straight from the terminal:** Slide 6 shows three exact selected stdout lines from the previously executed 16-campaign demonstration. It explains the one-campaign denominator behind each displayed `success=1.000`, the INR units and simulated-debit meaning of `exposure`, and the limited meaning of `known`.
- **Master versus final prototype:** Slide 8 compares the verified earlier `master` implementation with the selected prototype. The detectors and synthetic simulator were already present; the prototype adds the Q-learning/zero-Q workflow, checkpoint evaluation and richer campaign/policy evidence. This is a source-code comparison, not a controlled performance experiment against master.

## Evidence boundaries

The compared remote heads before this revision were `master` at `1e2ca9e3db4a19bb72e0433f07f10425f74b82fa` and prototype at `25c28300ca738ee2d0a530b99683033668c312ca`. Research code remains at baseline `92a12966ec49fd6dcd147fd4d7411382715bc729`; the `models/` and `data/` trees have no differences between those compared branches.

The new [terminal excerpt record](../research/review_materials/prototype_terminal_excerpt.json) preserves the exact selected strings, original stdout/stderr SHA-256 values, four underlying short-run output hashes, command template and recorded exit code. The original full logs, exact machine-specific argv, raw short-run outputs and prior verification package remain preserved outside this documentation revision. The command template normalizes the interpreter and output location; it is not represented as a literal copy of the original argv.

The short demonstration had 16 evaluation campaigns and four training episodes total, with one campaign in each detector/workload/attacker cell. Its results are not pooled with the retained 1,152-campaign study, and no short or full experiment was rerun for this revision. The original model portability warning remains disclosed; no claim of a clean installation or warning-free execution is made.

## Executed revision checks

- **Historical arithmetic:** `python -B -s scripts/recalculate_prototype_snapshot.py --output NEW_JSON` completed with exit code 0 and 3,508 checks. It recovered 1,152 campaigns, 1,077 completions, 4,189 transactions, 3,229 ALLOW / 885 FLAG / 75 BLOCK decisions and INR 29,196,913.14 gross simulated debit.
- **Presentation acceptance:** Eight presentation-specific tests passed, covering native objects, names and IDs, final-branch comparison, verbatim stdout and hashes, short-record identity, full-record arithmetic, excluded contact data and visible limitations. These are not additional research-engine regressions; the previously reported 47 RL cases were not rerun here.
- **Build and format:** The Node presentation compiler exited 0. The OOXML repair script completed with 37 normalizations on the initial build and 36 on the final build; text extraction and PDF conversion exited 0. All eight slides remain native editable text/shapes, with one native chart and one native comparison table, not full-slide screenshots.
- **PDF and diff:** `qpdf --check` reported no syntax or stream-encoding errors. `git diff --check` passed; raw research outputs, engine source, tests, datasets and models are unchanged.

All eight initial rendered slides were independently reviewed. The review found no critical clipping or missing names, but identified tight lower spacing, adjacent chart labels, an insufficiently explicit one-campaign denominator, and an unclear implementation-versus-performance distinction.

The revision increased lower spacing on slides 3–5 and 8, shortened chart labels to rounded whole percentages while preserving exact native-series values, explicitly labeled the overall pooled results, added “1 campaign per cell” to the terminal caption, and clarified that the branch table is not a controlled performance comparison. The deck was rebuilt, repaired and rendered again; slides 3–6 and 8 were visually rechecked after those corrections. All eight acceptance tests passed again, with no failures or skips; reruns are not counted as additional distinct tests. The final PDF preview contains eight pages and passed `qpdf --check` again.

## Changed files

Changes relative to prototype `25c2830` are limited to:

```text
README.md
docs/PROTOTYPE_PRESENTATION_REVISION.md
research/review_materials/PROTOTYPE_PRESENTATION_README.md
research/review_materials/UPI_PROTOTYPE_FACULTY_8_SLIDES.pptx
research/review_materials/UPI_PROTOTYPE_FACULTY_8_SLIDES.pdf
research/review_materials/prototype_terminal_excerpt.json
research/review_materials/prototype_slides/compile.js
research/review_materials/prototype_slides/slide-01.js
research/review_materials/prototype_slides/slide-03.js
research/review_materials/prototype_slides/slide-04.js
research/review_materials/prototype_slides/slide-05.js
research/review_materials/prototype_slides/slide-06.js
research/review_materials/prototype_slides/slide-08.js
```

The original presentation remains recoverable at `25c2830` and was also copied to the isolated revision evidence before editing. The IEEE paper is unchanged: it concerns a different study version and remains an AI-assisted draft with university-approved AI-content and similarity reports pending external verification. Gate C remains HOLD; no default-branch change, merge, release or Gate C workflow is part of this revision.
