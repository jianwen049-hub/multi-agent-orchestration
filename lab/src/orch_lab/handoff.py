"""Handoff protocol between agents."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from orch_lab.blackboard import Blackboard

ALLOWED_ROLES = frozenset({"planner", "worker", "critic", "orchestrator", "user"})


class HandoffError(ValueError):
    pass


@dataclass
class HandoffRequest:
    from_role: str
    to_role: str
    reason: str
    expects: list[str] = field(default_factory=list)
    artifact_keys: list[str] = field(default_factory=list)
    optional_keys: list[str] = field(default_factory=list)

    def to_payload(self) -> dict[str, Any]:
        return {
            "from_role": self.from_role,
            "to_role": self.to_role,
            "reason": self.reason,
            "expects": list(self.expects),
            "artifact_keys": list(self.artifact_keys),
            "optional_keys": list(self.optional_keys),
        }


def validate_handoff(req: HandoffRequest, board: Blackboard) -> None:
    if req.to_role not in ALLOWED_ROLES:
        raise HandoffError(f"invalid to_role: {req.to_role}")
    if req.from_role not in ALLOWED_ROLES:
        raise HandoffError(f"invalid from_role: {req.from_role}")
    if not req.expects:
        raise HandoffError("expects must be non-empty")
    missing = [k for k in req.artifact_keys if not board.has(k)]
    if missing:
        raise HandoffError(f"missing artifact_keys on blackboard: {missing}")
