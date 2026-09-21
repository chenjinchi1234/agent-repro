# 新生入门任务 — 进度记录

> 辅助维护。新会话/新 Agent 开始时可先读此文件了解进度。
> 任务书：`C:\Users\jinchichen\Desktop\课题组学习\TASKBOOK.md`（WSL 内路径：`/mnt/c/Users/jinchichen/Desktop/课题组学习/TASKBOOK.md`）

## 已做的决定

| 事项 | 决定 |
|---|---|
| 论文 | **Tree of Thoughts** (NeurIPS'23, `princeton-nlp/tree-of-thought-llm`)，复现 Game of 24 上 CoT vs ToT 准确率 |
| Coding Agent | **ZCode 桌面端**（2026-09-16 起；Claude Code CLI 2.1.272 仍在 WSL 作备选） |
| 硬件 | 无独立显卡（仅 Intel UHD 730 核显）→ A 档纯 API 题 |
| API | **OpenCode Go** key（组里发的，已实测有效）。订阅模型列表 30+：glm-5.x、kimi-k3、deepseek-v4-pro/flash、qwen3.8-max、gpt-5.6-luna 等 |
| 实验模型 | 待定：Day 3 用 3 道题小测试对比 deepseek-v4-pro vs glm-5.3（便宜备选 deepseek-v4-flash / glm-5.3-flash） |

## ⭐ API 调用关键结论（2026-09-16 排障实测定论，所有调用都按这个来）

**网关有两个硬性要求：**
1. **`x-opencode-session` 请求头必须带**（值随意，如 `claude-wsl`）。不带 → 400 `MissingSessionID`。带错 key → 401 `Missing API key`
2. 两种协议都已实测通过（HTTP 200，`cost: 0` 走订阅）：

| 协议 | 地址 | 认证头 | 验证状态 |
|---|---|---|---|
| OpenAI | `https://opencode.ai/zen/go/v1/chat/completions` | `Authorization: Bearer <key>` | ✅ 200 |
| Anthropic | `https://opencode.ai/zen/go/v1/messages` | `x-api-key: <key>` + `anthropic-version: 2023-06-01` | ✅ 200 |

- **ZCode 配置**：OpenAI 协议 + Base URL `https://opencode.ai/zen/go/v1` + key + 请求头 `x-opencode-session`（供应商设置的 headers 项）+ 模型 ID 一字不差（如 `gpt-5.6-luna` 不能写 `gpt5.6`）。报「连接失败 + HTML」= 地址/协议填错，请求打到了网页
- **WSL 的 Claude Code**：`~/.bashrc` 已配 `ANTHROPIC_BASE_URL=https://opencode.ai/zen/go`、`ANTHROPIC_API_KEY`、`ANTHROPIC_MODEL=deepseek-v4-pro`、`ANTHROPIC_CUSTOM_HEADERS={"x-opencode-session":"claude-wsl"}`（重复的 key 行已删）
- **实验代码（Day 2-3）**：用 openai Python SDK，`base_url=https://opencode.ai/zen/go/v1` + `default_headers={"x-opencode-session": "..."}`

## 环境状态

- [x] Day 0 全部验收通过（WSL2 / git 2.53.0 / uv 0.12.14 / node 24 / GitHub SSH / 仓库公开 / `~/repos` / A 档）
- [x] GitHub：`chenjinchi1234/agent-repro`（README + AGENTS.md + progress.md 已 push，`89b285e`）
- [x] `.wslconfig`（15Gi 内存、mirrored 网络）；uv 清华源
- [ ] ZCode：安装 + 按上面配置接 OpenCode Go（连接失败问题按上面结论修）
- [ ] 仓库链接发到课题组群（未确认）

## 当前任务（Day 1）

1. 发群链接 `https://github.com/chenjinchi1234/agent-repro`
2. ZCode 装好并配通（连接失败 → 按上面「ZCode 配置」修）
3. hello-world agent 三件事：读 progress.md → 改 README.md 加一行日期 → 跑 git status/git diff
4. 读 ToT 论文 Abstract + 图 1（https://arxiv.org/abs/2305.10601），用自己话回答三问：解决什么问题 / 核心方法是什么 / 凭什么说有效

## 后续安排（任务书时间表）

- Day 2: 精读 ToT Method；clone `princeton-nlp/tree-of-thought-llm`，跑通 Game of 24 demo；写 `docs/paper_notes.md` 第一版
- Day 3-4: 核心模块 = 思维树的搜索策略（BFS/DFS）+ LLM 给中间状态打分；缩小规模复现 CoT vs ToT 准确率
- Day 5: README / REPORT.md / agent_log.md / debug_log.md / skill / 5 分钟汇报
- 底线：每个数字能解释来源；记录 ≥2 个 Agent 出错的例子；不许改评测凑数字
