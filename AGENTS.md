# AGENTS.md — agent-repro 仓库操作说明

本仓库是「新生入门任务」的工作仓库：复现 **Tree of Thoughts** (NeurIPS'23) 论文在 Game of 24 上的一个数字（CoT vs ToT 准确率）。

## 环境

- 所有命令在 **WSL2 Ubuntu** 里运行（本机 Windows 11，无独显 → 纯 API 实验）
- Python 用 **uv** 管理（清华源已配）；Node 24；Claude Code CLI 2.x
- API：**OpenCode Go** key。Anthropic 兼容端点 `https://opencode.ai/zen/go`（已在 `~/.bashrc` 配好）；OpenAI 兼容端点 `https://opencode.ai/zen/go/v1`（实验代码用）

## 怎么装

- 实验代码：`princeton-nlp/tree-of-thought-llm`（Day 2 clone 到 `repro/tot/`）
- 装法以该仓库 README 为准；本仓库只做复现记录，不复制官方代码

## 怎么跑

- 先跑通官方 Game of 24 demo（命令以官方 README 为准，跑通后把确切命令更新到这里）
- 复现规模：缩小到几十题；先用 3 题做最小系统验证

## 怎么测

- 官方仓库自带 Game of 24 评测脚本，跑通后把用法更新到这里
- 底线：不改评测脚本凑数字；跑不出来如实写

## 仓库约定

- 进度看 `progress.md`；Agent 出错记录写 `agent_log.md`；bug 根因写 `debug_log.md`
- 论文笔记写 `docs/paper_notes.md`；复现结论写 `REPORT.md`
- API key 只放环境变量，不进代码、不进 git
