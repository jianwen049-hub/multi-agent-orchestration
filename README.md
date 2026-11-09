# multi-agent-orchestration — Planner / Worker / Critic Patterns

> Open lab on **multi-agent orchestration**: role protocols (planner · worker · critic), in-process message bus, handoff contracts, shared blackboard, and failure/retry — with **fake LLM stubs** so everything runs offline (no API key).

**Author:** 马健文 / Evans Owen ([jianwen049-hub](https://github.com/jianwen049-hub))

| | |
|---|---|
| **Lab** | [`lab/`](./lab/) — bus · blackboard · agents · retry · runtime |
| **Blog** | [`docs/blog/`](./docs/blog/) |
| **Bio** | [`PROFILE.md`](./PROFILE.md) |

## 中文速览

多 Agent 不是「多开几个 prompt」。关键是：**谁能说话、消息长什么样、交接何时发生、失败如何收敛、共享状态放哪**。本仓用 stub 模型把这些协议跑成可单测的状态机。

## Reading guide (EN)

```bash
cd lab
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=src
python3 scripts/smoke_check.py
python3 -m orch_lab.cli run "总结退款政策并指出风险"
python3 -m unittest discover -s tests -v
```

## License

MIT — see [`LICENSE`](./LICENSE).
