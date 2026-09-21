# AGENTS.md — agent-repro 仓库操作说明

本仓库是「新生入门任务」的工作仓库：复现 **Tree of Thoughts** (NeurIPS'23) 论文在 Game of 24 上的一个数字（CoT vs ToT 准确率）。最终结果与归因见 `REPORT.md`。

## 环境

- 所有命令在 **WSL2 Ubuntu** 里运行（本机 Windows 11，无独显 → 纯 API 实验）
- Python 用 **uv** 管理（清华源已配）；实验 venv 在 `repro/tot/.venv`（Python 3.11；系统 python3 是 3.14、没有 sympy，别用它）
- API：**OpenCode Go** key（网关）。实验代码走 OpenAI 兼容端点 `http://127.0.0.1:8787/v1`（本地代理 ~/proxy.js，自动转接 `https://opencode.ai/zen/go/v1`）
- 关键坑：`wsl.exe bash -c` 是非交互 shell，**不加载 .bashrc** → OPENAI_API_KEY/OPENAI_API_BASE 必须 inline 在命令前缀

## 怎么装

- 实验代码：`princeton-nlp/tree-of-thought-llm`（clone 到 `repro/tot/`，官方 commit 8050e67 + 适配 commit cd8b9ef）
- 装法以该仓库 README 为准（uv venv + requirements.txt）；本仓库只做复现记录

## 怎么跑（已验证的确切命令）

```bash
cd repro/tot

# CoT 基线：每题 100 样本，5 题一批
OPENAI_API_KEY=sk-... OPENAI_API_BASE=http://127.0.0.1:8787/v1 .venv/bin/python run.py \
  --task game24 --task_start_index 900 --task_end_index 905 \
  --naive_run --prompt_sample cot --n_generate_sample 100 --backend glm-5.3-flash

# ToT：propose + value + greedy，b=3、e=1
OPENAI_API_KEY=sk-... OPENAI_API_BASE=http://127.0.0.1:8787/v1 .venv/bin/python run.py \
  --task game24 --task_start_index 900 --task_end_index 905 \
  --method_generate propose --method_evaluate value --method_select greedy \
  --n_evaluate_sample 1 --n_select_sample 3 --backend glm-5.3-flash
```

- 长任务放后台后 **30 秒内必须**在 `tail ~/proxy.log` 看到第一批 POST；否则进程多半在静默重试 api.openai.com（env 没带进去）
- stdout 日志有 8KB 块缓冲，可能是空的；进度看 `logs/game24/*.json` 的样本数（每题目完成时写入）
- 汇总：`.venv/bin/python combine.py '<glob>' <label>`（CoT 逐样本口径 + ToT io 口径）

## 怎么测

- 判定逻辑在 `src/tot/tasks/game24.py:44-55`（test_output：末行 Answer 格式 + 数字多重集合 + sympy 验算）
- **底线：不改评测脚本凑数字；跑不出来如实写**（任务书第 3、6 节）

## 仓库约定

- 进度看 `progress.md`；Agent 出错记录写 `agent_log.md`；bug 根因写 `debug_log.md`
- 论文笔记写 `docs/paper_notes.md`；复现结论写 `REPORT.md`；汇报稿 `docs/presentation.md`
- `repro/` 是嵌套 git 仓库，父仓库不要 `git add repro/` 整体提交；结果 json 默认不进 git（量大），需要时可挑选关键日志提交
- API key 只放环境变量，不进代码、不进 git
