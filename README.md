# C API Scanner

面向 C 项目的 Web API 接口提取工具。它按目录选择 extractor skill，因为不同目录可能用不同框架、不同路由表、不同动态分发方式实现 API。

## 架构

- `c_api_scanner/agent_skills/*/SKILL.md`：真正的 Markdown skill 文档。当前包含 `webdis` 专用 skill 和 `generic-c` 兜底 skill。
- `c_api_scanner/skills/`：确定性 adapter。流水线没有模型 key 时也能按 Markdown skill 的规则稳定输出。
- `c_api_scanner/workflow.py`：LangGraph 工作流，节点为 `discover_directories -> extract_with_deepagents_skill_dispatch -> build_report`。
- `c_api_scanner/deep_agent.py`：DeepAgents 适配层，用一个 tool 调用目录 skill。没有安装 DeepAgents 或没有模型 key 时，自动退回确定性 dispatcher，方便 CI 定时跑。
- `c_api_scanner/cli.py`：流水线入口，输出 JSON 报告。
- `langgraph.json`：LangSmith Studio / LangGraph Studio 可加载的 graph 配置。

## 安装

```bash
cd /Users/ccc/ai-c-api-scanner
python3 -m pip install -e .
```

如需 LangSmith Studio 查看每一步 trace，设置：

```bash
cp .env.example .env
# 填 LANGSMITH_API_KEY 和模型 API key
```

## 扫描 webdis

本仓库不提交第三方 fixture。第一次测试 webdis 前先克隆样例：

```bash
mkdir -p fixtures
git clone https://github.com/nicolasff/webdis.git fixtures/webdis
```

```bash
python3 -m c_api_scanner fixtures/webdis --output output/webdis-api-report.json
```

输出报告包含 `source_file`、`line`、`methods`、`path`、`handler`、`confidence`、`evidence`、`skill` 和 `directory`。

## 流水线定时运行

```bash
python3 -m c_api_scanner /path/to/c/project --output /path/to/artifacts/api-report.json
```

建议流水线保存 `output/*.json` 作为 artifact，并配置 `LANGSMITH_PROJECT=c-api-scanner` 以便按运行批次查看 trace。

## 新增目录 Markdown skill

1. 新建 `c_api_scanner/agent_skills/<name>/SKILL.md`。
2. 在 frontmatter 里写 `name`、`priority`、`adapter`、`match.required_files` 或 `match.any_files`。
3. 在正文里写这个目录的提取步骤、证据要求、输出字段。
4. 如果流水线需要确定性运行，再在 `c_api_scanner/skills/` 增加同名 adapter，并在 `SkillRegistry` 的 `adapters` 字典里注册。

示例：

```markdown
---
name: webdis
priority: 100
adapter: webdis
match:
  required_files:
    - worker.c
    - websocket.c
    - cmd.h
---

# Webdis C API Extraction Skill

...
```

## webdis 当前提取语义

webdis 不是固定 REST 路由项目，而是 Redis-over-HTTP 动态命令接口：

- `GET /{redis-command}[/{arg}...]`
- `PUT /{redis-command}[/{arg}...]`
- `POST /{request-body redis-command}`
- `GET /crossdomain.xml`
- `OPTIONS /*`
- `WEBSOCKET /.json websocket`
- `WEBSOCKET /.raw websocket`
