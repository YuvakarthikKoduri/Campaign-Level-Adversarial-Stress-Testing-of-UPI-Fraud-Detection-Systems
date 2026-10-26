# Browser automation attempt record

This is a retrospective summary of the tool traces, not a manufactured runtime log. The application remained available during these automation failures.

- Two scripts tried selecting `#run-select` while the Runner page intentionally hid the filter bar, producing 30-second locator timeouts. The correction was to navigate to Results before choosing the evidence run.
- A scripted wait for a particular formatted percentage was not bounded explicitly and stalled while requests/rendering were in flight. The pending orchestration calls were cancelled; the final checks instead waited for current export/filter state.
- A first CSV download was taken before the final filter request had rendered its updated export URL. That file is retained as `filtered-ui.csv`, not the final selection evidence. Further source review correctly classified this as a genuine export race, subsequently fixed with a loading guard and delayed-response browser regression.
- Corrected final downloads are `filtered-ui-final.csv`, `.md` and `.svg`; `browser-exports.json` identifies the exact intended filters. Explanations, campaign drill-down and sorting then completed, and the test browser was closed.
