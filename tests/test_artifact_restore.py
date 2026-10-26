"""Portable evidence restoration fails closed without modifying trusted sources."""
import json
from pathlib import Path
import shutil
import pytest
from scripts.restore_evidence import REPO,restore,safe_name

@pytest.mark.parametrize("name",["../x","/tmp/x","x\\y",".",".."])
def test_unsafe_member_names(name):
    with pytest.raises(ValueError,match="Unsafe"):safe_name(name)

def test_corrupt_archive_rejected(tmp_path):
    src=REPO/"results/artifacts"
    shutil.copy2(src/"manifest.json",tmp_path/"manifest.json")
    archive=tmp_path/"verified-evidence-v1.zip"
    raw=bytearray((src/archive.name).read_bytes());raw[0]^=1;archive.write_bytes(raw)
    with pytest.raises(ValueError,match="SHA-256"):
        restore(archive,tmp_path/"output")
    assert not (tmp_path/"output").exists()

def test_symlink_restore_root_rejected(tmp_path):
    root=tmp_path/"link";root.symlink_to(tmp_path/"outside",target_is_directory=True)
    with pytest.raises(ValueError,match="Symlink"):restore(destination=root)

def test_restore_idempotently_checks_all_registered_bytes():
    result=restore()
    assert result["runs"]==9 and result["files"]==715
    index=json.loads((REPO/".local/retained/index.json").read_text())
    assert len(index["pilot-main"]["files"])>200
