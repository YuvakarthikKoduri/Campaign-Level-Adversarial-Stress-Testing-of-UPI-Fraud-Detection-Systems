"""Temporary literal-artifact tests, not generated data or production executions."""
import json
import pytest

from src.semantic_pipeline.storage import ImmutableArtifact, verify_artifact
from src.semantic_pipeline.authorization import ExecutionDenied, ExecutionPermit
from src.semantic_pipeline.config import load_config, DEFAULT_CONFIG
from src.semantic_pipeline.cli import main


def test_literal_atomic_artifact_and_corrupt_hash(tmp_path):
    target = tmp_path / "literal"
    with ImmutableArtifact(target) as writer:
        writer.json("example.json", {"literal": True})
        writer.finish({"kind": "unit_fixture"})
    verify_artifact(target)
    assert (target / "COMPLETE").is_file()
    with pytest.raises(FileExistsError):
        with ImmutableArtifact(target):
            pass
    (target / "example.json").write_text('{"literal":false}')
    with pytest.raises(ValueError):
        verify_artifact(target)


def test_partial_write_no_complete_marker_and_no_resume(tmp_path):
    target = tmp_path / "literal"
    with pytest.raises(RuntimeError):
        with ImmutableArtifact(target) as writer:
            writer.json("example.json", {"literal": True})
            raise RuntimeError("injected partial failure")
    assert not target.exists()
    assert list(tmp_path.glob(".literal.incomplete-*"))
    with pytest.raises(FileExistsError):
        with ImmutableArtifact(target):
            pass


@pytest.mark.parametrize("path", ["../escape", "/absolute", "nested/../../escape"])
def test_path_traversal_is_rejected(tmp_path, path):
    with ImmutableArtifact(tmp_path / "literal") as writer:
        with pytest.raises(ValueError):
            writer.json(path, {})


def test_approval_scope_is_config_and_execution_bound():
    c = load_config(DEFAULT_CONFIG)
    permit = ExecutionPermit(c.digest, ("pilot",), ("collect",), "review-fixture-only")
    permit.require(c, "pilot", "collect")
    for execution, phase in [("production", "collect"), ("pilot", "train")]:
        with pytest.raises(ExecutionDenied):
            permit.require(c, execution, phase)


@pytest.mark.parametrize("command", [
    "preflight", "collect", "prepare", "validate-dataset", "train", "calibrate",
    "validate-model", "validate-readiness", "verify-preservation", "close-review",
])
def test_cli_denies_execution_before_any_workflow(command, capsys, tmp_path):
    args = [command, "--config", str(DEFAULT_CONFIG), "--execution-id", "unapproved",
            "--root", str(tmp_path)]
    assert main(args) == 2
    assert "approval" in capsys.readouterr().err.lower()
    assert list(tmp_path.iterdir()) == []
