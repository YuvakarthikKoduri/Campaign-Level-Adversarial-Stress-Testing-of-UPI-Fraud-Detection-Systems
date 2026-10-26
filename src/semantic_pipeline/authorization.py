"""Explicit execution gate. No approval is bundled with implementation code."""
from dataclasses import dataclass
from pathlib import Path
import re

from src.features.schema import parse_json

PHASES = frozenset({"preflight", "collect", "prepare", "validate-dataset", "train", "calibrate",
                    "validate-model", "validate-readiness", "verify-preservation",
                    "compare-repeats", "close-review"})


class ExecutionDenied(PermissionError):
    pass


def safe_name(value):
    if type(value) is not str or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,95}", value):
        raise ValueError("Unsafe execution/artifact name")
    return value


@dataclass(frozen=True)
class ExecutionPermit:
    config_digest: str
    execution_ids: tuple
    phases: tuple
    approval_reference: str

    def __post_init__(self):
        if (not re.fullmatch(r"[0-9a-f]{64}", self.config_digest)
                or type(self.execution_ids) is not tuple or not self.execution_ids
                or type(self.phases) is not tuple or not self.phases
                or set(self.phases) - PHASES
                or not self.approval_reference.strip()):
            raise ValueError("Malformed execution approval")
        for value in self.execution_ids:
            safe_name(value)

    def require(self, config, execution_id, phase):
        if (phase not in self.phases or execution_id not in self.execution_ids
                or config.digest != self.config_digest):
            raise ExecutionDenied("Separate matching execution approval is required")

    @classmethod
    def load(cls, path):
        d = parse_json(Path(path).read_text(encoding="utf-8"))
        if (type(d) is not dict or set(d) != {"gate", "approved_for_execution", "config_digest",
                "execution_ids", "phases", "approval_reference"}
                or d["gate"] != "C" or d["approved_for_execution"] is not True):
            raise ExecutionDenied("Invalid explicit execution approval file")
        return cls(d["config_digest"], tuple(d["execution_ids"]), tuple(d["phases"]),
                   d["approval_reference"])


def require_permission(permit, config, execution_id, phase):
    if type(permit) is not ExecutionPermit:
        raise ExecutionDenied("Separate explicit execution approval is required; implementation is not approval")
    safe_name(execution_id)
    permit.require(config, execution_id, phase)
