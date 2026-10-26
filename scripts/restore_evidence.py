"""Verify and restore the bundled immutable evidence into ignored local storage."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import zipfile

REPO=Path(__file__).resolve().parents[1]
def safe_name(name):
    p=PurePosixPath(name)
    if not name or name in (".","..") or p.is_absolute() or any(x in ("","..",".") for x in p.parts) or "\\" in name:
        raise ValueError("Unsafe evidence member name")
    return p

def restore(archive=None,destination=None):
    archive=Path(archive or REPO/"results/artifacts/verified-evidence-v1.zip")
    destination=Path(destination or REPO/".local/retained")
    expected=json.loads((archive.parent/"manifest.json").read_text())["sha256"]
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=expected:
        raise ValueError("Evidence archive SHA-256 mismatch")
    if destination.is_symlink():raise ValueError("Symlink restore root forbidden")
    destination.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        manifest=json.loads(z.read("manifest.json"))
        if manifest["format"]!="upi-evidence-cas-v1":raise ValueError("Unsupported evidence format")
        imported={}
        writes=[]
        for run,record in manifest["runs"].items():
            safe_name(run)
            if "/" in run:raise ValueError("Run name must be one component")
            imported[run]=dict(kind=record["kind"],files=record["files"],verification=record["verification"])
            writes.extend((run+"/"+name,digest) for name,digest in record["files"].items())
        writes.extend(manifest["extra"].items())
        for name,digest in writes:
            safe_name(name)
            if not re.fullmatch("[0-9a-f]{64}",digest):raise ValueError("Malformed evidence digest")
            target=destination/name
            if any(p.is_symlink() for p in [target,*target.parents] if p!=destination.parent):
                raise ValueError("Symlink evidence destination forbidden")
            raw=z.read("objects/"+digest)
            if hashlib.sha256(raw).hexdigest()!=digest:raise ValueError("Evidence object digest mismatch")
            if target.exists():
                if target.read_bytes()!=raw:raise ValueError("Refusing to overwrite different evidence: "+name)
            else:
                target.parent.mkdir(parents=True,exist_ok=True)
                with target.open("xb") as f:f.write(raw)
        index=destination/"index.json"
        raw=(json.dumps(imported,sort_keys=True,indent=2)+"\n").encode()
        if index.exists() and index.read_bytes()!=raw:raise ValueError("Existing registry differs")
        if not index.exists():
            with index.open("xb") as f:f.write(raw)
    return dict(destination=str(destination),files=len(writes),runs=len(imported))

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    print(json.dumps(restore(),indent=2))
