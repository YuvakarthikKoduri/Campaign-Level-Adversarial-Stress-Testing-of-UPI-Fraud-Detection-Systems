"""Package local verification for review, without altering original logs or studies.

Run only in the integration workspace whose sibling execution-evidence exists.
This is a handover utility, not part of the simulator or dashboard command allowlist.
"""
from pathlib import Path
import hashlib
import json
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT.parent/"execution-evidence"
PUBLIC=ROOT/"docs/verification"

def sha(data):return hashlib.sha256(data).hexdigest()

def main():
    PUBLIC.mkdir(parents=True,exist_ok=True)
    replacements=[
        (str(ROOT),"REPOSITORY_ROOT"),
        (str(ROOT.parent/"fresh-python311"),"FRESH_ENV_ROOT"),
        ("/home/user/workspace/upi-independent-reproduction/.venv-independent","PRIOR_ENV_ROOT"),
        (str(ROOT.parent),"INTEGRATION_WORKSPACE_ROOT"),
        ("/home/user/workspace","WORKSPACE_ROOT"),
    ]
    receipt=[]
    for source in sorted(EVIDENCE.iterdir()):
        if not source.is_file() or (source.suffix not in (".json",".jsonl",".xml",".stdout",".stderr",".csv",".md",".svg")
            and source.name not in ("server-final.log","server-02.log","server.log")):
            continue
        if source.name in ("dashboard-before.json","integration-inherited-files.json"):
            continue
        raw=source.read_bytes()
        try:text=raw.decode()
        except UnicodeDecodeError:continue
        for old,new in replacements:text=text.replace(old,new)
        data=text.encode()
        (PUBLIC/source.name).write_bytes(data)
        receipt.append(dict(file=source.name,original_sha256=sha(raw),public_sha256=sha(data),
                            path_normalized=data!=raw))
    (PUBLIC/"NORMALIZATION_RECEIPT.json").write_text(json.dumps(receipt,indent=2)+"\n")
    # Short-run records and job logs remain untouched inside this archive.
    # There are no environment dumps, cookies, tokens or credentials in the selection.
    archive=ROOT/"results/artifacts/review-short-workflows.zip"
    members=[]
    for base,prefix in ((ROOT/".local/review-demo","fresh-demo"),
                        (ROOT/".local/dashboard-state","dashboard")):
        for path in sorted(base.rglob("*")):
            if not path.is_file() or "cache" in path.parts:continue
            if path.suffix in (".pyc",):continue
            name=prefix+"/"+path.relative_to(base).as_posix()
            members.append((path,name))
    with zipfile.ZipFile(archive,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for path,name in members:z.write(path,name)
    with zipfile.ZipFile(archive) as z:assert z.testzip() is None
    (PUBLIC/"SHORT_ARCHIVE.json").write_text(json.dumps(dict(
        path="results/artifacts/"+archive.name,sha256=sha(archive.read_bytes()),
        files=len(members),bytes=archive.stat().st_size,
        note="New short demonstrations, cancellation partials and exact job logs; not additional full-pilot replication."
    ),indent=2)+"\n")
    frozen=json.loads((EVIDENCE/"dashboard-before.json").read_text())
    prior=ROOT.parent.parent/"upi-dashboard-01"
    mismatches=[name for name,digest in frozen.items()
                if not (prior/name).is_file() or sha((prior/name).read_bytes())!=digest]
    preservation=dict(checked=len(frozen),mismatches=mismatches,
                      source_workspace="upi-dashboard-01",read_only=True)
    (PUBLIC/"PRESERVATION.json").write_text(json.dumps(preservation,indent=2)+"\n")
    assert not mismatches,preservation
    inherited=json.loads((EVIDENCE/"integration-inherited-files.json").read_text())
    (PUBLIC/"INHERITED_FILES.json").write_text(json.dumps(inherited,indent=2)+"\n")
    print(json.dumps({"public_logs":len(receipt),"short_files":len(members),
                      "preservation":preservation}))

if __name__=="__main__":main()
