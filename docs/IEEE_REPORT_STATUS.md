# IEEE paper recheck and external-verification status

The existing IEEE conference draft is on `review/academic-dashboard-paper-v1`, not in the historical prototype code baseline. It describes the corrected legacy study, separate nine-block matched pilot, dashboard and their limitations; its pilot results must not be presented as outputs of `prototype/rl-academic-complete`.

## Actual report files

- [Compiled PDF](https://github.com/YuvakarthikKoduri/Campaign-Level-Adversarial-Stress-Testing-of-UPI-Fraud-Detection-Systems/blob/review/academic-dashboard-paper-v1/research/paper/main.pdf): five-page review draft.
- [Editable LaTeX, bibliography, figures and tables](https://github.com/YuvakarthikKoduri/Campaign-Level-Adversarial-Stress-Testing-of-UPI-Fraud-Detection-Systems/tree/review/academic-dashboard-paper-v1/research/paper): `main.tex`, `references.bib`, unmodified `IEEEtran.cls`, generated results and build instructions.
- [External-check instructions](https://github.com/YuvakarthikKoduri/Campaign-Level-Adversarial-Stress-Testing-of-UPI-Fraud-Detection-Systems/blob/review/academic-dashboard-paper-v1/research/review_materials/EXTERNAL_CHECKS.md): authorship review and university-approved reporting.

The class came from the [official IEEE template selector](https://template-selector.ieee.org/). The source uses `\documentclass[conference]{IEEEtran}` and the IEEEtran bibliography style; it does not replace class margins or columns with a homemade layout.

## Recheck on 2026-10-28

The exact existing source package was copied to an isolated directory and compiled with Tectonic 0.17.0 using `tectonic main.tex --keep-logs`. Compilation exited 0 and generated five US-letter pages; the source and existing published PDF were not silently replaced.

The engine reported underfull-line warnings and font-shape substitution warnings. `pdffonts` showed embedded Nimbus Roman body fonts, a Times-compatible TeX family, and embedded mathematical fonts; the output is not a claim that every conference's final font/accessibility preflight has passed.

The prior repository PDF SHA-256 is `fe85917e66fca8068c2285f312684ec3a1b1971b1c9f089ea9a6ef07a52ec9e3`. A fresh compilation has different PDF metadata and must be identified by its own hash rather than presented as byte-identical evidence.

## AI content and similarity: pending, not certified

The draft is explicitly AI-assisted. Installing a presentation skill, using an IEEE template or paraphrasing text cannot truthfully turn it into “a report without AI content”; AI-detection scores are also not measurements of plagiarism or authorship.

No university-approved checker name, authorized checker access or genuine report has been supplied for this document. A check of the available skill library found no IEEE/academic-writing skill matching that query, and connector discovery returned no Turnitin connection candidate; these checks do not establish that the university lacks such a service.

| Requirement | Status |
|---|---|
| IEEE-style editable draft and compiled PDF | Available; compilation rechecked |
| Correct researcher names, institution and venue rules | Pending researcher approval |
| Human authorship/substantive review and AI-use disclosure | Pending |
| AI-content percentage below the university threshold | PENDING EXTERNAL VERIFICATION |
| Similarity percentage below the university threshold | PENDING EXTERNAL VERIFICATION |
| Genuine checker reports for the exact final PDF | Not obtained |

The researcher must identify the tools the university actually accepts and its policy on AI-assisted drafting. Then verify and substantively author the final argument, approve attribution and identity, compile the final document, and submit that exact file through authorized university access.

Save each genuine report with checker name, date, document hash and measured score. Review citation/originality issues legitimately, rerun checks after substantive revisions, and bring the final reports to the review; do not fabricate reports or use detector-evasion techniques.

Until those steps are complete, the paper is a review draft, not an AI-free or submission-certified manuscript. Gate C remains HOLD.
