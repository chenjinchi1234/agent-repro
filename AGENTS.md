# AGENTS.md — agent-repro 仓库操作说明

本仓库是「新生入门任务」的工作仓库：复现 **Tree of Thoughts** (NeurIPS'23) 论文在 Game of 24 上的一个数字（CoT vs ToT 准确率）。最终结果与归因见 `REPORT.md`。

## 环境

- 所有命令在 **WSL2 Ubuntu** 里运行（本机 Windows 11，无独显 → 纯 API 实验）
- Python 用 **uv** 管理；实验 venv 在 `repro/tot/.venv`（Python 3.11；系统 python3 是 3.14、没有 sympy，别用它跑实验）
- API：**OpenCode Go** key（网关）。实验代码走 OpenAI 兼容端点 `http://127.0.0.1:8787/v1`（本地代理 `~/proxy.js`，node 进程，自动转接 `https://opencode.ai/zen/go/v1`）
- 关键坑：`wsl.exe bash -c` 是非交互 shell，**不加载 .bashrc** → OPENAI_API_KEY/OPENAI_API_BASE 必须 inline 在命令前缀

## 怎么装（只装一次）

- 实验代码：`princeton-nlp/tree-of-thought-llm`（clone 到 `repro/tot/`，官方 commit 8050e67 + 适配 commit cd8b9ef）
- 装法以该仓库 README 为准（uv venv + requirements.txt）；装完用下面第 1 步的 `ls` 命令自检

## 怎么跑：从零到出数字（按顺序敲，已验证）

> 所有命令里唯一要改的地方：**`sk-你的key` 换成你的网关 key**，其余照抄。
> 环境变量前缀 `OPENAI_API_KEY=... OPENAI_API_BASE=...` 每次都写 inline（原因见「环境」最后一条）。

### 第 0 步：进 WSL、到代码目录

```bash
wsl.exe                            # 在 Windows 终端敲这条，进入 Ubuntu
cd ~/repos/agent-repro/repro/tot
```

### 第 1 步：开机三件套（每条命令有正常输出 = 过）

```bash
ls .venv/bin/python     # ① venv 在（没有 → 按官方 README 装）
```

```bash
ps aux | grep proxy.js | grep -v grep     # ② 代理进程在（没有 → nohup node ~/proxy.js > ~/proxy.log 2>&1 &）
```

```bash
curl -H 'Authorization: Bearer sk-你的key' https://opencode.ai/zen/go/v1/usage     # ③ key 活着，顺便看配额
```

### 第 2 步：最小验证（1 题 × 1 样本，约 1 分钟）

```bash
OPENAI_API_KEY=sk-你的key OPENAI_API_BASE=http://127.0.0.1:8787/v1 .venv/bin/python run.py \
  --task game24 --task_start_index 900 --task_end_index 901 \
  --naive_run --prompt_sample cot --n_generate_sample 1 --backend glm-5.3-flash
```

跑完不报错、`logs/game24/` 多出一个 json → 全链路通。**先做这步再上大实验**（换模型时尤其必须，能省一整天）。

**自检信号**：启动后应立即打印一行 `Warning: OPENAI_API_BASE is set to http://127.0.0.1:8787/v1`（models.py 的 env 回显）。**没看到这行 = 环境变量没带对**，进程会静默直连 api.openai.com 挂死（被墙 + 官方代码无限重试，表象就是一直卡着不出结果）。最常见死法：`sk-你的key` 和 `OPENAI_API_BASE` 之间漏了空格，整串被当成 key 的值。

### 第 3 步：正式跑（放后台）

```bash
# CoT 基线：15 题（第 900-914 题）× 每题 100 样本
nohup env OPENAI_API_KEY=sk-你的key OPENAI_API_BASE=http://127.0.0.1:8787/v1 .venv/bin/python run.py \
  --task game24 --task_start_index 900 --task_end_index 915 \
  --naive_run --prompt_sample cot --n_generate_sample 100 --backend glm-5.3-flash \
  > ~/cot_run.log 2>&1 &
```

```bash
# ToT：15 题 × 每题目 1 次完整 BFS 搜索（b=3、e=1、greedy）
nohup env OPENAI_API_KEY=sk-你的key OPENAI_API_BASE=http://127.0.0.1:8787/v1 .venv/bin/python run.py \
  --task game24 --task_start_index 900 --task_end_index 915 \
  --method_generate propose --method_evaluate value --method_select greedy \
  --n_evaluate_sample 1 --n_select_sample 3 --backend glm-5.3-flash \
  > ~/tot_run.log 2>&1 &
```

### 第 4 步：30 秒内确认真的在跑

```bash
tail -f ~/proxy.log     # 看到 /v1/chat/completions 的 POST 在滚 = 真在跑（Ctrl+C 退出查看）
```

- 没动静 = env 没带进去，SDK 在静默重试 api.openai.com：`kill %1` 杀掉，回第 3 步检查命令。
- 进度看 json 数在涨：`ls logs/game24/*.json | wc -l`（stdout 日志空着也正常——8KB 块缓冲；每题目完成才落一个 json）。

### 第 5 步：收工

```bash
kill %1     # 停最近的后台任务（%1、%2… 对应启动顺序）
```

```bash
ps aux | grep run.py     # 确认没有孤儿进程
```

### 第 6 步：汇总出数字

```bash
.venv/bin/python ~/combine.py 'logs/game24/glm-5.3-flash_0.7_naive_cot_sample_100_start9*.json' CoT
```

```bash
.venv/bin/python ~/combine.py 'logs/game24/glm-5.3-flash_0.7_propose1_value1_greedy3_start9*.json' ToT
```

`combine.py` 在 WSL 家目录（`~/combine.py`，不在 git 里）；它会同时打两个口径：逐样本准确率（CoT 口径）和「每题目至少一次成功」（ToT io 口径）。**任何汇总数字都要人工复核**（列加和 vs 分母对账）。

### 参数说明（每个 flag 什么意思）

| flag | 含义 | 我们的值 |
|---|---|---|
| `--task game24` | 跑 24 点任务 | game24 |
| `--task_start_index` / `--task_end_index` | 题目行号区间，**左闭右开**（`range(start, end)`，来自 24.csv 的行号） | 900 / 915（=第 900-914 题） |
| `--naive_run` | 不搜索、单次生成（= CoT 基线） | CoT 用 |
| `--prompt_sample` | 提示类型：`cot`（CoT）/ `propose`（生成下一步） | cot |
| `--n_generate_sample` | 每题采样次数（CoT：样本数；ToT：每个节点生成的候选数） | 100 / 1 |
| `--method_generate propose` | BFS 生成候选的方式 | propose |
| `--method_evaluate value` | BFS 打分方式（value prompt，sure/likely/impossible） | value |
| `--method_select greedy` | 每层按分数从高到低取前 b 个 | greedy |
| `--n_evaluate_sample` | 每个候选打 e 次分（求和） | 1（论文 3） |
| `--n_select_sample` | 每层留 b 个候选 | 3（论文 5） |
| `--backend` | 网关模型名 | glm-5.3-flash |
| `OPENAI_API_KEY=sk-...` | 网关 key，**只放环境变量，不进文件** | 你自己的 |
| `OPENAI_API_BASE=http://127.0.0.1:8787/v1` | 走本地代理（自动转接网关） | 固定 |

## 怎么测

- 判定逻辑在 `src/tot/tasks/game24.py:44-55`（test_output：末行 Answer 格式 + 数字多重集合 + sympy 验算）
- **底线：不改评测脚本凑数字；跑不出来如实写**（任务书第 3、6 节）

## 仓库约定

- 进度看 `progress.md`；Agent 出错记录写 `agent_log.md`；bug 根因写 `debug_log.md`
- 论文笔记写 `docs/paper_notes.md`；复现结论写 `REPORT.md`；汇报稿 `docs/presentation.md`
- `repro/` 是嵌套 git 仓库，父仓库不要 `git add repro/` 整体提交；结果 json 默认不进 git（量大），需要时可挑选关键日志提交
- API key 只放环境变量，不进代码、不进 git
