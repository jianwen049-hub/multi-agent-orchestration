# 02 · 交接与黑板：状态别只塞进 prompt

## 当时我怎么看这个问题

Agent 之间传状态，最偷懒的办法是「把上一轮完整 transcript 再喂给下一角色」。上下文暴涨、关键字段被淹没，而且**无法断言「黑板里是否已写入订单号」**这类结构化不变量。另一极端是每个 Agent 私有 dict，交接时靠口头约定 key 名——必漂。

## 试过什么

1. **全量 transcript 接力**：贵、吵、难测。
2. **只传最后一条 assistant 文本**：丢掉中间工具结果。
3. **每个 Agent 自己的全局变量**：进程内能跑，测试隔离失败。
4. **handoff 用自然语言「请某某继续」**：解析脆弱。

## 为什么否决

否决「transcript = 状态」。共享**黑板（blackboard）**放结构化键值；**handoff 协议**只传指针式契约：`from_role`、`to_role`、`reason`、`expects`、`artifact_keys`。下一角色先读黑板再读消息，而不是反向。

## 最终怎么解

`blackboard.py`：`Blackboard` 带 `set/get/snapshot`，写入附带 `updated_by`。  
`handoff.py`：`HandoffRequest` / `validate_handoff`——校验目标角色合法、expects 非空、artifact_keys 已在黑板上（或标记为 optional）。

Planner 写 `plan.steps` 到黑板；Worker 写 `work.outputs`；Critic 写 `critique.verdict`。总线传 handoff 信封，黑板传事实。

## 用到的具体 skill / 技巧清单

| Skill | 用法 |
|-------|------|
| **黑板 KV** | 结构化、可 snapshot |
| **handoff 契约** | expects / artifact_keys |
| **校验先于执行** | `validate_handoff` |
| **updated_by 审计** | 谁写的一目了然 |
| **消息与状态分离** | bus ≠ blackboard |
| **单测锁键存在** | 不测散文质量 |

## 代码解析（按文件路径）

### `lab/src/orch_lab/blackboard.py`

内存 dict + 元数据。`snapshot()` 深拷贝，供 CLI 打印与测试。

### `lab/src/orch_lab/handoff.py`

`HandoffRequest` dataclass；非法 recipient 或缺失 artifact 时抛 `HandoffError`（或返回 error envelope，由 runtime 决定）。

### `lab/src/orch_lab/runtime.py`

编排循环里：发 handoff 前 `validate_handoff`；通过后才 `bus.publish`。
