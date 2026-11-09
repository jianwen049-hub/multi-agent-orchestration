"""Deterministic fake LLM — no network."""
from __future__ import annotations


class LLMStub:
    """Role-aware stub completions for offline demos and tests."""

    def complete(self, role: str, prompt: str) -> str:
        role = role.lower()
        text = prompt or ""
        if role == "planner":
            return (
                "PLAN\n"
                "1. 提炼用户任务中的目标与约束\n"
                "2. 给出可执行步骤并标出风险点\n"
                f"SOURCE: {text[:120]}"
            )
        if role == "worker":
            # Inject a stable failure marker when asked
            if "FAIL_PLEASE" in text:
                return "WORK_RESULT FAIL_PLEASE: incomplete draft without citations"
            return f"WORK_RESULT: completed step based on → {text[:160]}"
        if role == "critic":
            if "FAIL_PLEASE" in text:
                return "VERDICT: reject\nREASONS: missing citations; contains FAIL_PLEASE marker"
            return "VERDICT: approve\nREASONS: structure ok; risks noted"
        return f"STUB({role}): {text[:80]}"
