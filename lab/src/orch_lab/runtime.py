"""Orchestrator runtime: bus + blackboard + retry loop."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from orch_lab.agents import CriticAgent, PlannerAgent, WorkerAgent
from orch_lab.blackboard import Blackboard
from orch_lab.bus import MessageBus
from orch_lab.handoff import HandoffError, HandoffRequest, validate_handoff
from orch_lab.llm_stub import LLMStub
from orch_lab.messages import Envelope, make_envelope
from orch_lab.retry import RetryPolicy, RetryState, should_retry


@dataclass
class RunResult:
    status: str
    attempts: int
    blackboard: dict[str, Any]
    history: list[dict[str, Any]] = field(default_factory=list)


class Orchestrator:
    def __init__(self, policy: RetryPolicy | None = None, llm: LLMStub | None = None) -> None:
        self.bus = MessageBus()
        self.board = Blackboard()
        self.llm = llm or LLMStub()
        self.policy = policy or RetryPolicy(max_attempts=3)
        self.planner = PlannerAgent(self.llm, self.board)
        self.worker = WorkerAgent(self.llm, self.board)
        self.critic = CriticAgent(self.llm, self.board)
        self._inbox: list[Envelope] = []
        self.bus.subscribe("orchestrator", self._on_orchestrator)

    def _on_orchestrator(self, env: Envelope) -> None:
        self._inbox.append(env)

    def _dispatch_to_role(self, role: str, env: Envelope) -> list[Envelope]:
        if role == "planner":
            return self.planner.handle(env)
        if role == "worker":
            return self.worker.handle(env)
        if role == "critic":
            return self.critic.handle(env)
        return []

    def run(self, task: str) -> RunResult:
        self._inbox.clear()
        state = RetryState()
        # seed task
        user_env = make_envelope("user", "orchestrator", "task", {"task": task})
        self.bus.publish(user_env)
        self.bus.drain()

        # kick planner
        for out in self._dispatch_to_role("planner", user_env):
            self.bus.publish(out)
        self.bus.drain()

        status = "running"
        while status == "running":
            # process inbox handoffs / critiques
            batch = list(self._inbox)
            self._inbox.clear()
            if not batch:
                status = "error"
                self.bus.publish(make_envelope("orchestrator", "user", "error", {"reason": "empty inbox"}))
                break

            progressed = False
            # Critiques first so exhausted reject can stop before consuming handoff.
            batch.sort(key=lambda e: 0 if e.kind == "critique" else 1)
            for env in batch:
                if status != "running":
                    break
                if env.kind == "handoff":
                    req = HandoffRequest(
                        from_role=str(env.payload.get("from_role")),
                        to_role=str(env.payload.get("to_role")),
                        reason=str(env.payload.get("reason", "")),
                        expects=list(env.payload.get("expects") or []),
                        artifact_keys=list(env.payload.get("artifact_keys") or []),
                        optional_keys=list(env.payload.get("optional_keys") or []),
                    )
                    try:
                        validate_handoff(req, self.board)
                    except HandoffError as e:
                        self.bus.publish(
                            make_envelope("orchestrator", "user", "error", {"reason": str(e)})
                        )
                        status = "error"
                        break
                    # deliver synthetic envelope to target role
                    target_env = make_envelope(
                        "orchestrator",
                        req.to_role,
                        "info",
                        {"handoff": req.to_payload()},
                    )
                    if req.to_role == "worker":
                        state.bump()
                    for out in self._dispatch_to_role(req.to_role, target_env):
                        self.bus.publish(out)
                    self.bus.drain()
                    progressed = True
                elif env.kind == "critique":
                    verdict = str(env.payload.get("verdict", "")).lower()
                    if verdict == "approve":
                        status = "ok"
                        progressed = True
                    elif verdict == "reject":
                        if should_retry(verdict, state, self.policy):
                            # handoff already queued by critic; continue
                            progressed = True
                        else:
                            self.bus.publish(
                                make_envelope(
                                    "orchestrator",
                                    "user",
                                    "error",
                                    {
                                        "reason": "retry exhausted",
                                        "attempts": state.attempts,
                                        "critique": env.payload,
                                    },
                                )
                            )
                            status = "error"
                            progressed = True
                    else:
                        status = "error"
                        progressed = True
                elif env.kind in {"plan", "work", "info"}:
                    progressed = True
                elif env.kind == "error":
                    status = "error"
                    progressed = True

            if status == "running" and not progressed:
                status = "error"
                break
            # safety: if approve path already set ok, exit
            if status != "running":
                break
            # if critic approved in same drain, loop checks status

        # final drain for any trailing msgs
        self.bus.drain()
        return RunResult(
            status=status,
            attempts=state.attempts,
            blackboard=self.board.snapshot(),
            history=[e.to_dict() for e in self.bus.history],
        )
