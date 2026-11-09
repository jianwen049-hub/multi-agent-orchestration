# 03 · 失败与重试：critic 否决之后怎么办

## 当时我怎么看这个问题

Critic 说「不行」之后，常见翻车有两种：无限打回把账单打爆；或者直接放弃、把半成品当成功返回。还有一种「智能重试」——同一 prompt 再打一次，却不告诉 worker **错在哪**，于是同款错误循环。

## 试过什么

1. **无上限 while True 重试**：成本与延迟失控。
2. **固定再试 1 次且不改输入**：几乎必再败。
3. **失败就重启整个 planner**：丢掉已有黑板资产。
4. **把 exception 字符串拼进下一 prompt 末尾**：无结构，模型偶尔理睬。

## 为什么否决

否决无界重试与「空白重试」。需要：**最大尝试次数**、**退避（玩具仓用计数即可）**、**把 critique 理由写入黑板再 handoff 回 worker**、**耗尽后显式 error 信封**。Stub 可用关键词稳定触发失败，保证测试不 flaky。

## 最终怎么解

`retry.py`：`RetryPolicy(max_attempts=3)` + `RetryState`；`should_retry(verdict, state)`。  
`runtime.py`：critic 返回 `reject` 时，若 `should_retry`，则 handoff 回 worker 并附 `critique.reasons`；否则发布 `kind=error` 结束。

Smoke 覆盖两条路径：普通任务一次通过；含 `FAIL_PLEASE` 的任务在耗尽后拿到 error，且尝试次数等于 `max_attempts`。

## 用到的具体 skill / 技巧清单

| Skill | 用法 |
|-------|------|
| **显式 RetryPolicy** | max_attempts 可测 |
| **critique 回灌** | 理由进黑板 |
| **耗尽 → error envelope** | 禁止假成功 |
| **稳定失败注入** | stub 关键词 |
| **不重置黑板** | 保留已完成 steps |
| **CLI 打印 attempt** | 演示可见 |

## 代码解析（按文件路径）

### `lab/src/orch_lab/retry.py`

纯策略对象，不碰 LLM。

### `lab/src/orch_lab/runtime.py`

`Orchestrator.run(task)` 主循环；返回 `RunResult(status, attempts, blackboard, history)`。

### `lab/tests/test_runtime.py`

断言 happy path `status==ok`；失败路径 `status==error` 且 `attempts==max_attempts`。

### `lab/scripts/smoke_check.py`

跑两条路径 + unittest，最后打印 `smoke_check OK`。
