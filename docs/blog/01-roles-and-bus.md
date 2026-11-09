# 01 · 角色与总线：先约定谁能说话

## 当时我怎么看这个问题

最早做「多 Agent」时，我把三个系统提示词丢进同一个对话线程，靠模型自觉切换人设。结果是：planner 偷偷写最终答案、worker 开始评审、critic 又去改需求——角色串台。更糟的是排障：日志里只有一坨 messages，看不出**哪次调用是以什么角色、消费了哪条入站消息**。

## 试过什么

1. **单线程多 system prompt 轮流改**：角色边界全靠自觉。
2. **用函数名假装角色**：没有消息类型，仍是自由文本。
3. **直接 asyncio 扇出三个 LLM 调用再拼字符串**：无协议，失败不可复现。
4. **把总线做成全局 list.append**：并发与回放都困难，也缺少订阅关系。

## 为什么否决

否决「prompt 即协议」。多 Agent 的最小闭环是：**类型化消息 + 可订阅总线 + 显式角色处理器**。即使 LLM 是假 stub，协议也要真；换真模型时只替换 `llm_stub.complete`。

## 最终怎么解

- `messages.py`：`Envelope(id, sender, recipient, kind, payload, ts)`
- `bus.py`：进程内 pub/sub，按 `recipient` 或 `kind` 投递；保留 `history` 便于回放
- `agents.py`：`PlannerAgent` / `WorkerAgent` / `CriticAgent`，各自 `handle(envelope) -> list[Envelope]`
- `llm_stub.py`：按角色返回确定性假回复（含可触发失败的关键词）

Runtime 一轮：注入 user 任务 → planner 出计划 → worker 执行步骤 → critic 评审 →（可选）打回。

## 用到的具体 skill / 技巧清单

| Skill | 用法 |
|-------|------|
| **类型化 Envelope** | kind: task/plan/work/critique/handoff/error |
| **显式 sender/recipient** | 禁止「广播到空气」 |
| **总线 history** | 回放与单测断言 |
| **角色 handler 纯函数倾向** | 便于 stub |
| **假 LLM 可注入** | 关键词触发失败路径 |
| **与 tracing 思路对齐** | 每封信可当 span 事件 |

## 代码解析（按文件路径）

### `lab/src/orch_lab/messages.py`

`Envelope` + 工厂函数 `make_envelope`。`kind` 用 Literal 约束，避免魔法字符串散落。

### `lab/src/orch_lab/bus.py`

`MessageBus.publish` / `subscribe` / `drain`。本仓默认同步队列；接口留成可换 Redis 的样子，但不引入依赖。

### `lab/src/orch_lab/agents.py`

三个 Agent 类共享 `BaseAgent`，内部调 `LLMStub.complete(role, prompt)`。

### `lab/src/orch_lab/llm_stub.py`

无网络。planner 把任务拆成 2 步；worker 回显步骤；critic 对含 `FAIL_PLEASE` 的内容投反对票。
