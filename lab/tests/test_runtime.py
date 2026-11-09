import unittest

from orch_lab.handoff import HandoffError, HandoffRequest, validate_handoff
from orch_lab.blackboard import Blackboard
from orch_lab.retry import RetryPolicy, RetryState, should_retry
from orch_lab.runtime import Orchestrator


class TestRuntime(unittest.TestCase):
    def test_happy_path(self):
        orch = Orchestrator(policy=RetryPolicy(max_attempts=3))
        result = orch.run("总结退款政策并指出风险")
        self.assertEqual(result.status, "ok")
        self.assertGreaterEqual(result.attempts, 1)
        self.assertIn("plan.steps", result.blackboard["data"])
        self.assertEqual(result.blackboard["data"].get("critique.verdict"), "approve")

    def test_reject_exhausted(self):
        orch = Orchestrator(policy=RetryPolicy(max_attempts=2))
        result = orch.run("请处理 FAIL_PLEASE 文档")
        self.assertEqual(result.status, "error")
        self.assertEqual(result.attempts, 2)

    def test_handoff_validation(self):
        board = Blackboard()
        board.set("plan.steps", ["1"], updated_by="planner")
        req = HandoffRequest(
            from_role="planner",
            to_role="worker",
            reason="go",
            expects=["work.outputs"],
            artifact_keys=["plan.steps"],
        )
        validate_handoff(req, board)
        bad = HandoffRequest(
            from_role="planner",
            to_role="worker",
            reason="go",
            expects=["work.outputs"],
            artifact_keys=["missing.key"],
        )
        with self.assertRaises(HandoffError):
            validate_handoff(bad, board)

    def test_should_retry(self):
        policy = RetryPolicy(max_attempts=2)
        state = RetryState(attempts=1)
        self.assertTrue(should_retry("reject", state, policy))
        state.attempts = 2
        self.assertFalse(should_retry("reject", state, policy))
        self.assertFalse(should_retry("approve", state, policy))


if __name__ == "__main__":
    unittest.main()
