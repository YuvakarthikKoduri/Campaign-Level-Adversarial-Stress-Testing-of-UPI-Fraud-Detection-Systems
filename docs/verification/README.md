# Verification evidence

These files describe actual integration-time commands and outcomes. `commands.jsonl` records attempted commands, exit codes and elapsed time; the last regression selection after the export-race fix is `post-race-tests.xml` and its stdout/stderr. The preceding fresh/final selections repeat the same cases and are not additional distinct tests.

Public text logs have absolute sandbox prefixes replaced with labelled placeholders. `NORMALIZATION_RECEIPT.json` preserves both original and normalized hashes, and untouched original logs remain in the integration workspace's `execution-evidence/`; normalization is not a new successful run. Historical retained experiment bytes are distributed separately through the content-addressed archive.

`SHORT_ARCHIVE.json` identifies the archive of fresh short main/repeat/reload records, actual dashboard job logs and cancellation partials. Partial or cancelled jobs must not enter scientific result totals. `PRESERVATION.json` checks the frozen source dashboard workspace; earlier reports' broader preservation counts are historical, not newly rerun counts.

Browser automation failures are separated from application failures. Navigation, responsive widths, actual execution and cancellation were checked; a precision-sensitive scripted wait and attempts to use a selector hidden on the Runner page were automation mistakes, not fabricated passes. A stale-selection export exposed a genuine frontend race; its fix and delayed-response regression are documented separately. See the final verification report for the exact executed scope.
