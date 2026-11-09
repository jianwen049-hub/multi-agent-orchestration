"""Typed message envelopes for the agent bus."""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Literal

Kind = Literal["task", "plan", "work", "critique", "handoff", "error", "info"]


@dataclass
class Envelope:
    sender: str
    recipient: str
    kind: Kind
    payload: dict[str, Any]
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    ts: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def make_envelope(
    sender: str,
    recipient: str,
    kind: Kind,
    payload: dict[str, Any] | None = None,
) -> Envelope:
    return Envelope(
        sender=sender,
        recipient=recipient,
        kind=kind,
        payload=payload or {},
    )
