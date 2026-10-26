# Installation and environment

Use Linux or WSL2 with Python 3.11, Git and an isolated virtual environment. The locked runtime uses NumPy, pandas, scikit-learn, XGBoost, SciPy and pytest; the dashboard itself uses standard-library HTTP plus vendored frontend assets, not a new web framework.

```sh
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-milestone1.lock
python scripts/restore_evidence.py
python -B -s run_dashboard.py --port 8765
```

A fresh Python 3.11.17 environment was created during integration with `uv venv` and populated with `uv pip sync --python <fresh-environment>/bin/python requirements-milestone1.lock`; the entire 478-case selection and the short workflow passed there. The `venv`/pip commands above are the equivalent documented public setup, not a claim that native Windows/macOS or every resolver invocation was tested. Record your interpreter and installed versions if results differ.

Restore before opening retained results. The restorer verifies archive and object SHA-256s, refuses changed existing files and rejects unsafe names/symlink restore roots. It does not download models or train anything. The source checkout already includes the trusted legacy model files; never unpickle an arbitrary uploaded artifact.

Optional paper figures use `requirements-research.txt` in a separate analysis environment. A compatible TeX toolchain is needed to rebuild the supplied PDF; Tectonic 0.17.0 was tested, with its initial TeX bundle downloaded on first compilation. No TeX or presentation software is needed to run the dashboard.

If a port is occupied, choose another valid `--port`. Keep service access on loopback. A complete filesystem copy without `.git` is insufficient for the legacy runner's Git-context recording; clone the branch or preserve the repository metadata.
