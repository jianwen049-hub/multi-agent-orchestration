#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from orch_lab.retry import RetryPolicy
from orch_lab.runtime import Orchestrator


def main() -> int:
    ok = Orchestrator(policy=RetryPolicy(max_attempts=3)).run("总结退款政策并指出风险")
    assert ok.status == "ok", ok
    assert ok.blackboard["data"].get("critique.verdict") == "approve"

    bad = Orchestrator(policy=RetryPolicy(max_attempts=2)).run("触发 FAIL_PLEASE")
    assert bad.status == "error", bad
    assert bad.attempts == 2, bad.attempts

    loader = unittest.TestLoader()
    suite = loader.discover(str(ROOT / "tests"))
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful():
        return 1
    print("smoke_check OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
