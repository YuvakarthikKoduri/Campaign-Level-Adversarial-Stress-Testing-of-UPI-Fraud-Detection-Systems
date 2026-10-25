"""Bundle project source, unchanged models and evidence, excluding Git/cache state."""
import hashlib
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parent
destination = Path(sys.argv[1]).resolve()
if destination.exists():
    raise FileExistsError(destination)
tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
files = {ROOT / p for p in tracked if p}
files.update(ROOT / p for p in [
    "run_prototype.py", "build_prototype_delivery.py", "verify_prototype_outputs.py",
    "PROTOTYPE_COMPLETION_REPORT.md", "docs/PROTOTYPE_GUIDE.md",
    "docs/PRESENTATION_BRIEF.md", "docs/architecture.svg",
    "src/attackers/q_learning.py", "src/experiments/prototype.py",
    "src/experiments/prototype_plots.py", "tests/test_prototype_rl.py",
    "models/baseline_xgboost.pkl", "models/baseline_random_forest.pkl",
    "data/synthetic/upi_transactions_v1.csv"])
files.update(p for p in (ROOT / "prototype_evidence").rglob("*")
             if p.is_file() and "package-check" not in p.parts)
files = sorted(p for p in files if p.is_file() and "__pycache__" not in p.parts)
with zipfile.ZipFile(destination, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    records = []
    for path in files:
        data = path.read_bytes()
        relative = path.relative_to(ROOT).as_posix()
        z.writestr("upi-fraud-stress-lab-prototype/" + relative, data)
        records.append(f"{hashlib.sha256(data).hexdigest()}  {relative}")
    z.writestr("upi-fraud-stress-lab-prototype/DELIVERY_SHA256SUMS.txt", "\n".join(records) + "\n")
print(f"{len(files)} files; {destination.stat().st_size} bytes; "
      f"SHA256 {hashlib.sha256(destination.read_bytes()).hexdigest()}")
