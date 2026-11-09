"""Planner / Worker / Critic agents."""
from __future__ import annotations

from typing import Any

from orch_lab.blackboard import Blackboard
from orch_lab.handoff import HandoffRequest
from orch_lab.llm_stub import LLMStub
from orch_lab.messages import Envelope, make_envelope


class BaseAgent:
    role: str = "base"

    def __init__(self, llm: LLMStub, board: Blackboard) -> None:
        self.llm = llm
        self.board = board

    def handle(self, envelope: Envelope) -> list[Envelope]:
        raise NotImplementedError


class PlannerAgent(BaseAgent):
    role = "planner"

    def handle(self, envelope: Envelope) -> list[Envelope]:
        task = envelope.payload.get("task") or envelope.payload.get("text") or ""
        plan = self.llm.complete("planner", task)
        steps = [ln.strip() for ln in plan.splitlines() if ln.strip() and ln.strip()[0].isdigit()]
        if not steps:
            steps = ["1. analyze", "2. draft"]
        self.board.set("plan.raw", plan, updated_by=self.role)
        self.board.set("plan.steps", steps, updated_by=self.role)
        self.board.set("task.text", task, updated_by=self.role)
        handoff = HandoffRequest(
            from_role=self.role,
            to_role="worker",
            reason="plan ready",
            expects=["work.outputs"],
            artifact_keys=["plan.steps", "task.text"],
        )
        return [
            make_envelope(self.role, "orchestrator", "plan", {"plan": plan, "steps": steps}),
            make_envelope(self.role, "orchestrator", "handoff", handoff.to_payload()),
        ]


class WorkerAgent(BaseAgent):
    role = "worker"

    def handle(self, envelope: Envelope) -> list[Envelope]:
        steps = self.board.get("plan.steps") or []
        critique = self.board.get("critique.reasons") or ""
        prompt = f"steps={steps}; critique={critique}; task={self.board.get('task.text')}"
        raw = self.llm.complete("worker", prompt)
        outputs = {"raw": raw, "steps_done": list(steps)}
        self.board.set("work.outputs", outputs, updated_by=self.role)
        handoff = HandoffRequest(
            from_role=self.role,
            to_role="critic",
            reason="work ready for review",
            expects=["critique.verdict"],
            artifact_keys=["work.outputs"],
        )
        return [
            make_envelope(self.role, "orchestrator", "work", outputs),
            make_envelope(self.role, "orchestrator", "handoff", handoff.to_payload()),
        ]


class CriticAgent(BaseAgent):
    role = "critic"

    def handle(self, envelope: Envelope) -> list[Envelope]:
        work = self.board.get("work.outputs") or {}
        raw = ""
        if isinstance(work, dict):
            raw = str(work.get("raw", ""))
        review = self.llm.complete("critic", raw)
        verdict = "approve"
        reasons = review
        for line in review.splitlines():
            if line.upper().startswith("VERDICT:"):
                v = line.split(":", 1)[1].strip().lower()
                if v in {"approve", "reject"}:
                    verdict = v
            if line.upper().startswith("REASONS:"):
                reasons = line.split(":", 1)[1].strip()
        self.board.set("critique.verdict", verdict, updated_by=self.role)
        self.board.set("critique.reasons", reasons, updated_by=self.role)
        self.board.set("critique.raw", review, updated_by=self.role)
        payload: dict[str, Any] = {"verdict": verdict, "reasons": reasons, "raw": review}
        out = [make_envelope(self.role, "orchestrator", "critique", payload)]
        if verdict == "reject":
            handoff = HandoffRequest(
                from_role=self.role,
                to_role="worker",
                reason="critique rejected work",
                expects=["work.outputs"],
                artifact_keys=["critique.reasons"],
            )
            out.append(make_envelope(self.role, "orchestrator", "handoff", handoff.to_payload()))
        return out
