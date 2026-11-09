"""Retry policy for critique reject loops."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RetryPolicy:
    max_attempts: int = 3


@dataclass
class RetryState:
    attempts: int = 0

    def bump(self) -> None:
        self.attempts += 1


def should_retry(verdict: str, state: RetryState, policy: RetryPolicy) -> bool:
    if verdict != "reject":
        return False
    return state.attempts < policy.max_attempts
