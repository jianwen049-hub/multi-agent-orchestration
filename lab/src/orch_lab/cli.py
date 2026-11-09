"""CLI for orchestration demos."""
from __future__ import annotations

import argparse
import json

from orch_lab.retry import RetryPolicy
from orch_lab.runtime import Orchestrator


def cmd_run(task: str, max_attempts: int) -> int:
    orch = Orchestrator(policy=RetryPolicy(max_attempts=max_attempts))
    result = orch.run(task)
    print(
        json.dumps(
            {
                "status": result.status,
                "attempts": result.attempts,
                "blackboard": result.blackboard,
                "history_kinds": [h.get("kind") for h in result.history],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if result.status == "ok" else 1


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="orch_lab")
    sub = p.add_subparsers(dest="cmd", required=True)
    rp = sub.add_parser("run")
    rp.add_argument("task")
    rp.add_argument("--max-attempts", type=int, default=3)
    args = p.parse_args(argv)
    if args.cmd == "run":
        return cmd_run(args.task, args.max_attempts)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
