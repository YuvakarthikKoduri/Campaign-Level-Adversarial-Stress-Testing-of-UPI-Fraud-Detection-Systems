# Review CI template: activation pending

The [review verification definition](review-ci.yml.example) runs only evidence restoration, the selected software tests and independent arithmetic. It does not run Gate C, train a full study, publish or merge.

GitHub rejected the initial feature push because its OAuth app lacks `workflow` scope. The exact rejection is preserved in `../verification/feature-push.stderr`; the complete unpublished commit with an active workflow is preserved locally on `review/academic-dashboard-paper-with-ci-local` at `59730cf8d307f1319f106a52dc03b3f52346fd15`.

The PR therefore includes the unchanged definition outside `.github/workflows/`, where it cannot execute. No GitHub Actions success is claimed. An authorized maintainer may review and add it as `.github/workflows/review-ci.yml` using an approved account/interface after deciding to activate CI; do not grant extra permissions or publish anything merely to bypass the rejected scope.
