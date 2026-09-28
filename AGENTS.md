# AGENTS.md — agent-repro 仓库操作说明

本仓库是「新生入门任务」的工作仓库：复现 **Tree of Thoughts** (NeurIPS'23) 论文在 Game of 24 上的一个数字（CoT vs ToT 准确率）。最终结果与归因见 `REPORT.md`。

## 环境

- 所有命令在 **WSL2 Ubuntu** 里运行（本机 Windows 11，无独显 → 纯 API 实验）
- Python 用 **uv** 管理；实验 venv 在 `repro/tot/.venv`（Python 3.11；系统 python3 是 3.14、没有 sympy，别用它跑实验）
- API：**OpenCode Go** key（网关）。实验代码走 OpenAI 兼容端点 `http://127.0.0.1:8787/v1`（本地代理，node 进程）。代理干两件事：补上网关**必须**的 `x-opencode-session` 头、转接 `https://opencode.ai/zen/go/v1`。**代理脚本在仓库里：`tools/proxy.js`**（2026-09-28 加入——原先只放在 WSL 家目录，别人 clone 不到，照本文档跑必然卡死）
- 关键坑：`wsl.exe bash -c` 是非交互 shell，**不加载 .bashrc** → OPENAI_API_KEY/OPENAI_API_BASE 必须 inline 在命令前缀

## 怎么装（只装一次）

> ⚠️ **`repro/` 不在这个仓库里**（`.gitignore` 排除了它，因为里面是另一个 git 仓库 + venv）。
> **拿代码 + 装环境**的完整命令见 `README.md` 的「怎么跑」第 ①② 步——这里不重复，只列两个最容易漏的点：
>
> - 补丁基于官方 commit `8050e67`：clone 官方仓库后要**先 checkout 再 apply**
> - `uv pip install -e .` **不能漏**：漏了 `run.py` 会报 `ModuleNotFoundError: No module named 'tot'`

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
ls .venv/bin/python     # ① venv 在（没有 → 按 README「怎么跑」第①②步装）
```
> ⚠️ 别只"按官方 README 装"——那样会**漏掉本仓库的补丁**（代码里的 propose 过滤器修复在 `patches/` 里），
> 也会漏 `uv pip install -e .`。完整的安装命令见 `README.md`「怎么跑」①②步。

```bash
ps aux | grep proxy.js | grep -v grep     # ② 代理进程在（没有 → nohup node ../../tools/proxy.js > ~/proxy.log 2>&1 &）
```

```bash
curl -H 'Authorization: Bearer sk-你的key' https://opencode.ai/zen/go/v1/usage     # ③ key 活着，顺便看配额
```

### 第 2 步：最小验证

**先跑免费的过滤器单测**（10 秒，**不需要 key**）——它验证 propose 过滤器，本次找出实现缺陷就是靠这条链上的检查：

```bash
.venv/bin/python tests/test_proposal_filter.py
```

应该全部 PASS。**换模型、改过滤器之后先跑它，再上大实验。**

然后是 1 题最小验证（1 题 × 1 样本，约 1 分钟）：

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
# CoT：指向你这次跑的【那一个】文件
.venv/bin/python ../../tools/combine.py logs/game24/glm-5.3-flash_0.7_naive_cot_sample_100_start900_end915.json CoT
```

```bash
# ToT：
.venv/bin/python ../../tools/combine.py logs/game24/glm-5.3-flash_0.7_propose1_value1_greedy3_start900_end915.json ToT
```

> ⚠️ **别用 `start9*.json` 这类宽通配符**（2026-09-28 修）——它会同时命中**分片文件**
> （`start900_end905`、`start905_end910`…）**和合并文件**，还会把 915-919 带进来。
> `combine.py` 把命中的文件简单相加、**不去重**，于是：
> **题目数从 15 变成 32、准确率从 85.1% 变成 84.4%** —— 数字看起来很像真的，但是错的。
> 要合并多个文件就**明确列出文件名**，不要靠通配符。
>
> `combine.py` 在仓库里（`tools/combine.py`），它同时打两个口径：逐样本准确率（CoT 口径）和
> 「每题目至少一次成功」（ToT io 口径）。**任何汇总数字都要人工复核**（列加和 vs 分母对账）。

### 参数说明（每个 flag 什么意思）

| flag | 含义 | 我们的值 |
|---|---|---|
| `--task game24` | 跑 24 点任务 | game24 |
| `--task_start_index` / `--task_end_index` | 题目区间，**左闭右开**（`range(start, end)`）。⚠️ 代码里的 index `i` 对应官方 CSV 的 **Rank `i+1`**——所以 `900 / 915` 抓到的是 **Rank 901-915**（论文也说"indices 901-1000"）。详见 REPORT 附录 A.7 | 900 / 915 |
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
- `repro/` 是嵌套 git 仓库（已被 `.gitignore` 排除）：**代码靠 `patches/tot-adapt-and-fix.patch` 分发**，不要 `git add repro/`
- 结果 json 的**关键几份已随仓库分发**（在 `evidence/`，配 `evidence/README.md` 说明哪个文件对应报告里哪个数字）；新跑出来的 json 不要直接提交（量大，靠 evidence 挑选）
- API key 只放环境变量，不进代码、不进 git
