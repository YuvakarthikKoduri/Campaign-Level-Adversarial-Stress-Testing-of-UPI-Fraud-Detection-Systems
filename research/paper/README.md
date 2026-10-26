# IEEE conference review draft

`main.tex` uses the unmodified IEEEtran class from the official IEEE conference LaTeX template downloaded through the [IEEE template selector](https://template-selector.ieee.org/secure/templateSelector/downloadTemplate?publicationTypeId=3&titleId=1&articleId=1&fileId=540). The selector path was Conferences → Original Research → LaTeX; downloaded filename: `conference-latex-template_10-17-19.zip`.

The class prescribes margins, columns, spacing and fonts; these are not overridden. The official instructions say to preserve those designations, remove template guidance and respect the target conference's page limit; no target conference has been supplied. Numeric IEEE citations are generated with IEEEtran BibTeX style and references include stable URLs.

## Rebuild

From repository root:

```sh
python scripts/restore_evidence.py
python scripts/reproduce_paper.py --figures
cd research/paper
tectonic main.tex --keep-logs
# Or use a compatible TeX Live installation:
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

The figures flag requires Matplotlib in a separate analysis environment; the metric reconstruction without that flag uses only Python's standard library. See `requirements-research.txt`. No training is invoked. Generated tables and plots derive from verified `pilot-main` records, never short demos or pooled legacy runs.

## Required human review

This is an AI-assisted editable draft, not an accepted paper or a declaration of student authorship. Replace the explicit author/institution placeholder with authorized details, choose a venue and check its page/AI-disclosure rules, inspect all references and technical claims, then obtain genuine university-approved reports for the exact final PDF.

AI-content and similarity requirements are **PENDING EXTERNAL VERIFICATION**. No university-approved checker, account or report was supplied; a local string comparison or an unapproved web score cannot satisfy them. See [external verification instructions](../review_materials/EXTERNAL_CHECKS.md).

Figures show block variability, not population confidence guarantees. Tables/intervals are exploratory and unadjusted; model, context, training and evaluation identities are retained in the restored archive.
