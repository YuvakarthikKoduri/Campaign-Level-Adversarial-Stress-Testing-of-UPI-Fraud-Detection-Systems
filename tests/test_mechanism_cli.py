"""Real CLI equality cannot override malformed prospective pilot content."""
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


def command(args):
    return subprocess.run([sys.executable,"-B","-s",*args],cwd=ROOT,capture_output=True,text=True)


@pytest.fixture(scope="module")
def triplet(tmp_path_factory):
    root=tmp_path_factory.mktemp("pilot-cli")
    for name in ("main","repeat","reload"):
        args=["-m","src.experiments.mechanism_pilot","--output",str(root/name),
              "--blocks","1","--episodes","2","--contexts","2","--seed-base","61000"]
        if name=="reload":
            args+=["--reload-from",str(root/"main")]
        run=command(args)
        (root/(name+".stdout")).write_text(run.stdout)
        (root/(name+".stderr")).write_text(run.stderr)
        assert run.returncode==0,run.stderr
    return root


def verify(root,output):
    return command(["verify_mechanism_pilot.py","--reference",str(root/"main"),
        "--repeat",str(root/"repeat"),"--reload",str(root/"reload"),"--output",str(output)])


def test_valid_triplet_and_zero_training_reload(triplet,tmp_path):
    out=tmp_path/"check.json"
    result=verify(triplet,out)
    assert result.returncode==0,result.stdout+result.stderr
    assert json.loads(out.read_text())["evidence_complete"]
    assert json.loads((triplet/"reload/manifest.json").read_text())["training_episodes_executed"]==0


def test_same_directory_cannot_prove_three_runs(triplet,tmp_path):
    out=tmp_path/"self-check.json"
    result=command(["verify_mechanism_pilot.py","--reference",str(triplet/"main"),
        "--repeat",str(triplet/"main"),"--reload",str(triplet/"main"),"--output",str(out)])
    assert result.returncode!=0
    payload=json.loads(out.read_text())
    assert payload["evidence_complete"] is False
    assert any("Distinct run directories" in x for x in payload["errors"])


def test_fit_evidence_cannot_masquerade_as_reload(triplet,tmp_path):
    for name in ("main","repeat","reload"):
        shutil.copytree(triplet/name,tmp_path/name)
    path=tmp_path/"reload/manifest.json";manifest=json.loads(path.read_text())
    manifest["mode"]="fit";path.write_text(json.dumps(manifest))
    out=tmp_path/"mode-check.json";result=verify(tmp_path,out)
    assert result.returncode!=0
    payload=json.loads(out.read_text())
    assert payload["evidence_complete"] is False
    assert any("reload manifest mode" in x for x in payload["errors"])


@pytest.mark.parametrize("fault,diagnostic",[
    ("gross","Gross/target money"),("missing","Full arm/context coverage"),
    ("summary","Summary success"),("source","Source coverage"),
])
def test_identically_corrupt_triplets_fail_content(triplet,tmp_path,fault,diagnostic):
    root=tmp_path/"bad"
    for name in ("main","repeat","reload"):
        shutil.copytree(triplet/name,root/name)
        path=root/name
        if fault in ("gross","missing"):
            file=path/"block-00/xgboost/campaigns.jsonl"
            rows=[json.loads(line) for line in file.read_text().splitlines()]
            if fault=="gross":
                rows[0]["gross_paise"]+=1
            else:
                rows.pop()
            file.write_text("".join(json.dumps(r,sort_keys=True)+"\n" for r in rows))
        elif fault=="summary":
            file=path/"summary.json"
            rows=json.loads(file.read_text())
            rows[0]["success"]=.123456789
            file.write_text(json.dumps(rows))
        else:
            (path/"source.json").write_text("{}")
    out=tmp_path/"check.json"
    result=verify(root,out)
    assert result.returncode!=0
    payload=json.loads(out.read_text())
    assert payload["evidence_complete"] is False
    assert diagnostic in "\n".join(payload["errors"])
