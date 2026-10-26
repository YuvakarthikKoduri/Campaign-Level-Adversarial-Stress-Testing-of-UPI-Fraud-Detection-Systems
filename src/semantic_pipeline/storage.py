"""No-replace local artifacts; failures retain reservations and incomplete evidence."""
import hashlib
import os
from pathlib import Path
import uuid
import re

from src.features.schema import canonical_json, parse_json


def sha256_file(path):
    with open(path, "rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def _relative(name):
    p = Path(name)
    if p.is_absolute() or not p.parts or any(part in ("..", ".") for part in p.parts):
        raise ValueError("Artifact path traversal")
    return p


class ImmutableArtifact:
    def __init__(self, target):
        self.target = Path(target)
        self.stage = None
        self.finished = False

    def __enter__(self):
        if self.target.exists() or self.target.is_symlink():
            raise FileExistsError(self.target)
        self.target.parent.mkdir(parents=True, exist_ok=True)
        if any(p.is_symlink() for p in (self.target.parent, *self.target.parents)):
            raise ValueError("Symlinked artifact parent")
        self.reservation = self.target.parent / ("." + self.target.name + ".reservation")
        fd = os.open(self.reservation, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(fd)
        self.stage = self.target.parent / ("." + self.target.name + ".incomplete-" + uuid.uuid4().hex)
        self.stage.mkdir()
        return self

    def bytes(self, name, value):
        if self.finished or self.stage is None:
            raise ValueError("Inactive artifact writer")
        path = self.stage / _relative(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "xb") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())

    def json(self, name, value):
        self.bytes(name, (canonical_json(value) + "\n").encode())

    def finish(self, metadata):
        paths = sorted(p for p in self.stage.rglob("*") if p.is_file())
        if any(p.is_symlink() for p in paths):
            raise ValueError("Symlinked payload")
        files = {str(p.relative_to(self.stage)): sha256_file(p) for p in paths}
        self.json("artifact_manifest.json", {"format": "upi_immutable/1", "metadata": metadata, "files": files})
        manifest_hash = sha256_file(self.stage / "artifact_manifest.json")
        all_files = dict(files, **{"artifact_manifest.json": manifest_hash})
        checksums = "".join(f"{value}  {key}\n" for key, value in sorted(all_files.items()))
        self.bytes("checksums.sha256", checksums.encode())
        try:
            self.bytes("COMPLETE", (manifest_hash + "\n").encode())
            verify_artifact(self.stage)
            if self.target.exists():
                raise FileExistsError(self.target)
            directory = os.open(self.stage, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
            os.rename(self.stage, self.target)  # exclusive reservation is retained
        except Exception:
            # Retain all payload/failure evidence but revoke the staged marker.
            marker = self.stage / "COMPLETE"
            if marker.exists():
                marker.unlink()
            raise
        self.finished = True
        # No fallible application operation after publication. This promises
        # process-failure isolation, not full machine/power-loss durability.
        return self.target

    def __exit__(self, exc_type, exc, traceback):
        # Never erase failure evidence or automatically resume an incomplete run.
        return False


def verify_artifact(path):
    path = Path(path)
    if path.is_symlink() or not path.is_dir():
        raise ValueError("Missing/untrusted artifact directory")
    all_paths = list(path.rglob("*"))
    if any(p.is_symlink() for p in all_paths):
        raise ValueError("Symlink in artifact")
    manifest_path = path / "artifact_manifest.json"
    if not manifest_path.is_file() or not (path / "COMPLETE").is_file():
        raise ValueError("Incomplete artifact")
    manifest = parse_json(manifest_path.read_text(encoding="utf-8"))
    if set(manifest) != {"format", "metadata", "files"} or manifest["format"] != "upi_immutable/1":
        raise ValueError("Unknown artifact format")
    files = manifest["files"]
    if type(files) is not dict or type(manifest["metadata"]) is not dict:
        raise ValueError("Missing payload hash map")
    for name, expected in files.items():
        if type(name) is not str or type(expected) is not str or not re.fullmatch("[0-9a-f]{64}", expected):
            raise ValueError("Malformed payload hash entry")
        _relative(name)
        if name in ("artifact_manifest.json", "checksums.sha256", "COMPLETE"):
            raise ValueError("Self-referential manifest")
        if not (path / name).is_file() or sha256_file(path / name) != expected:
            raise ValueError("Artifact checksum mismatch")
    expected_names = set(files) | {"artifact_manifest.json", "checksums.sha256", "COMPLETE"}
    if {str(p.relative_to(path)) for p in all_paths if p.is_file()} != expected_names:
        raise ValueError("Unlisted payload or missing file")
    mh = sha256_file(manifest_path)
    if (path / "COMPLETE").read_text() != mh + "\n":
        raise ValueError("Complete marker/manifest mismatch")
    hashes = dict(files, **{"artifact_manifest.json": mh})
    text = "".join(f"{value}  {name}\n" for name, value in sorted(hashes.items()))
    if (path / "checksums.sha256").read_text() != text:
        raise ValueError("Checksum index mismatch")
    return manifest
