# 新生入门任务 — 进度记录

> 由 Claude Code 辅助维护。新会话开始时可先读此文件了解进度。
> 任务书：`C:\Users\jinchichen\Desktop\课题组学习\TASKBOOK.md`（WSL 内路径：`/mnt/c/Users/jinchichen/Desktop/课题组学习/TASKBOOK.md`）

## 已做的决定

| 事项 | 决定 |
|---|---|
| 论文 | **Tree of Thoughts** (NeurIPS'23, `princeton-nlp/tree-of-thought-llm`)，复现 Game of 24 上 CoT vs ToT 准确率 |
| Coding Agent | **Claude Code**（WSL 内 CLI 已装，v2.1.263） |
| 硬件 | 无独立显卡（仅 Intel UHD 730 核显）→ A 档纯 API 题 |
| API | **OpenCode Go** key（opencode.ai 订阅网关）。OpenAI 兼容端点 `https://opencode.ai/zen/go/v1`（ToT 实验用），Anthropic 兼容端点 `https://opencode.ai/zen/go`（Claude Code 用）。已写入 WSL `~/.bashrc`（ANTHROPIC_BASE_URL / ANTHROPIC_API_KEY / ANTHROPIC_MODEL=deepseek-v4-pro）。可用模型：glm-5.x、kimi-k3、deepseek-v4-pro/flash、qwen3.8-max 等 30+ 个 |
| 实验模型 | 待定：Day 3 用 3 道题小测试对比 deepseek-v4-pro vs glm-5.3（便宜备选 deepseek-v4-flash / glm-5.3-flash） |

## 环境状态（Day 0 已全部验收通过 ✅ 2026-09-15）

- [x] WSL2 + Ubuntu（用户 `jinchichen1`），VERSION 2
- [x] git 2.53.0、uv 0.12.14、node v24.21.0、Claude Code 2.1.263
- [x] uv 清华源已配；`.wslconfig` 生效（WSL 内存 15Gi，mirrored 网络）
- [x] GitHub：`chenjinchi1234/agent-repro` 公开可访问，SSH 认证通过，README 已 push（`52d7cb4`）
- [x] 代码在 `~/repos/agent-repro`
- [x] 磁盘 954G 可用

## 当前任务（Day 1）

1. **发群**：仓库链接 `https://github.com/chenjinchi1234/agent-repro` 发到课题组群（唯一未完成的人工步骤）
2. 跑通 hello-world agent（Agent 三件事：读文件 / 执行命令 / 改文件——本会话已演示，WSL 里再正式做一遍）
3. 读 ToT 论文 Abstract + 图 1，回答三问：解决什么问题 / 核心方法是什么 / 凭什么说有效
4. 仓库根目录写 `AGENTS.md`（怎么装、怎么跑、怎么测）

## 后续安排（任务书时间表）

- Day 2: 精读 ToT Method；clone `princeton-nlp/tree-of-thought-llm`，跑通 Game of 24 demo；写 `docs/paper_notes.md` 第一版
- Day 3-4: 核心模块 = 思维树的搜索策略（BFS/DFS）+ LLM 给中间状态打分；缩小规模复现 CoT vs ToT 准确率
- Day 5: README / REPORT.md / agent_log.md / debug_log.md / skill / 5 分钟汇报
- 底线：每个数字能解释来源；记录 ≥2 个 Agent 出错的例子；不许改评测凑数字
