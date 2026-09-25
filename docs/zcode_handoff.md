# zcode 对接文档 — Tree of Thoughts 复现任务

> 给 zcode：这是本任务的完整交接上下文。按第 4 节照做即可从零跑出数字；第 5 节的坑请逐条遵守。
> 本文档**不含任何真实 API key**（key 从人类操作者处要，只放环境变量）。

## 0. 任务一句话

复现 **Tree of Thoughts**（Yao et al., NeurIPS 2023）论文在 Game of 24 上的数字：CoT vs ToT 的准确率。使用本组网关模型 **glm-5.3-flash**（T=0.7），题目为官方 `24.csv` 第 900-914 题（15 题）。

## 1. 现状（已完成，勿推倒重做）

- 仓库：`chenjinchi1234/agent-repro`（本机 WSL2 Ubuntu 路径 `~/repos/agent-repro`）
- 已完成：环境搭建、正式复现（CoT 逐样本 84.3%、ToT 每题 40.0%）、报告/笔记/日志、一个 skill
- 结论：方向与论文相反（CoT 反超 ToT），归因 = 现代推理模型已把搜索内化进单次推理（详见 `REPORT.md`）
- 你要做的：**在 zcode 环境里独立把实验跑起来**（验证数字或继续扩展均可）

## 2. 硬性底线（违反任意一条 = 任务作废）

1. **不改评测代码凑数字**：判定函数 `test_output`（`src/tot/tasks/game24.py:44-55`）一行都不能动；跑不出论文数字就如实写负结果
2. API key 只放环境变量，不进代码、不进 git、不进任何文档
3. 任务书原文件（TASKBOOK.md）只读；任何补充必须明确标注
4. 所有汇总数字必须可独立复核（combine.py 列加和 vs 分母人工对账）
5. git 提交前请人类操作者确认

## 3. 环境

| 项 | 说明 |
|---|---|
| 代码 | `princeton-nlp/tree-of-thought-llm` 官方 commit 8050e67 + 本组适配 commit cd8b9ef（`repro/tot/`） |
| Python | 3.11（venv 用 uv 管；系统 python3 是 3.14 没有 sympy，别用它） |
| 依赖 | 官方 requirements.txt，**openai==0.27.7**（新版不兼容） |
| 网络（本机） | 本地代理 `http://127.0.0.1:8787/v1`（`~/proxy.js`，node 进程，自动转接 `https://opencode.ai/zen/go/v1`） |
| 网络（其他机器/云端） | 不需要代理，`OPENAI_API_BASE` 直连 `https://opencode.ai/zen/go/v1` |
| 模型 | `glm-5.3-flash`（网关名，直接当 `--backend` 参数） |
| 配额 | 查询端点：`curl -H "Authorization: Bearer sk-你的key" https://opencode.ai/zen/go/v1/usage` |

## 4. 从零到出数字（本机 WSL2 版，命令全部单行、照贴即用）

### 第 0 步：进 WSL、到代码目录

```bash
wsl.exe
```

```bash
cd ~/repos/agent-repro/repro/tot
```

### 第 1 步：开机三件套（每条有正常输出 = 过）

```bash
ls .venv/bin/python
```

```bash
ps aux | grep proxy.js | grep -v grep
```

```bash
curl -H "Authorization: Bearer sk-你的key" https://opencode.ai/zen/go/v1/usage
```

### 第 2 步：最小验证（1 题 × 1 样本，约 1 分钟，必做）

```bash
OPENAI_API_KEY=sk-你的key OPENAI_API_BASE=http://127.0.0.1:8787/v1 .venv/bin/python run.py --task game24 --task_start_index 900 --task_end_index 901 --naive_run --prompt_sample cot --n_generate_sample 1 --backend glm-5.3-flash
```

**启动自检信号**：命令一跑应立即打印一行 `Warning: OPENAI_API_BASE is set to http://127.0.0.1:8787/v1`。**没看到这行 = 环境变量没带对**，立刻 Ctrl+C 杀掉重来（常见死法见第 5 节第 1 条）。

### 第 3 步：正式跑（后台）

```bash
nohup env OPENAI_API_KEY=sk-你的key OPENAI_API_BASE=http://127.0.0.1:8787/v1 .venv/bin/python run.py --task game24 --task_start_index 900 --task_end_index 915 --naive_run --prompt_sample cot --n_generate_sample 100 --backend glm-5.3-flash > ~/cot_run.log 2>&1 &
```

```bash
nohup env OPENAI_API_KEY=sk-你的key OPENAI_API_BASE=http://127.0.0.1:8787/v1 .venv/bin/python run.py --task game24 --task_start_index 900 --task_end_index 915 --method_generate propose --method_evaluate value --method_select greedy --n_evaluate_sample 1 --n_select_sample 3 --backend glm-5.3-flash > ~/tot_run.log 2>&1 &
```

参数速查：`--task_end_index` 是**左闭右开**（15 题 900-914 = 915）；CoT 约 2-4 小时，ToT 约 1 小时；`--n_evaluate_sample 1 --n_select_sample 3` = 论文 b=5/e=3 的弱化版（本组声明过的配置）。

### 第 4 步：30 秒内确认真的在跑

```bash
tail -f ~/proxy.log
```

看到 `/v1/chat/completions` 的 POST 在滚 = 真在跑（Ctrl+C 退出查看）。**屏幕安静是正常的**（nohup 把输出写进 `~/cot_run.log`），判断进度看 json：

```bash
ls -l logs/game24/*.json
```

文件大小隔几分钟变大 = 在跑（每完成一题落一题的数据）。

### 第 5 步：收工

```bash
ps aux | grep run.py
```

确认没有进程残留（run.py 没留孤儿）；有就 `kill <PID>`。

### 第 6 步：汇总出数字（人工复核）

```bash
.venv/bin/python ~/combine.py logs/game24/glm-5.3-flash_0.7_naive_cot_sample_100_start900_end915.json CoT
```

```bash
.venv/bin/python ~/combine.py logs/game24/glm-5.3-flash_0.7_propose1_value1_greedy3_start900_end915.json ToT
```

`combine.py` 在 WSL 家目录（统计脚本，未进 git）。它打两个口径：逐样本准确率（CoT 口径）和每题至少一次成功（ToT io 口径）。**任何汇总数字都要人工对账**（列加和 vs 分母）。

> **注（2026-09-22 接手人核查补充）：ToT 存在两次运行，别混淆**
>
> | 运行 | 文件 | 结果 |
> |---|---|---|
> | 正式（REPORT.md 口径） | `..._greedy3_start900_end905 / start905_end910 / start910_end915.json`（分片） | **6/15 = 40.0%**，逐候选 11/39 |
> | 未记录的重跑 | `..._greedy3_start900_end915.json`（单文件，9/21 18:29） | **4/15 = 26.7%**，逐候选 6/41 |
>
> 所以**上面第 6 步那条 ToT 命令跑出来是 26.7%，不是参考值表的 40.0%——这不是环境坏了**。
> 40.0% 只能从分片文件得到。另外注意 `start90*.json` 这类宽 glob 会同时命中分片与合并文件、
> 还会把 915-919 一起算进来（题目数变 25），务必用明确的文件列表。
> 两次运行解出的题目不同（正式：902/905/907/908/911/912；重跑：900/909/910/912），
> 方向不变且反转更强。核查细节见 WSL 家目录 `~/zcode_findings.md`。

### 参考值（用于自检，不是用来凑的目标）

| 口径 | 参考值 |
|---|---|
| CoT 逐样本 | 84.0-84.3%（1260-1265/1500） |
| CoT best-of-100 | 15/15（100%） |
| ToT 每题（io 口径） | 6/15（40.0%），来自**分片文件**（另有重跑 4/15 = 26.7%，见第 6 步注） |
| 官方 gpt-4 日志同管道复算（管道正确性校准） | CoT 3.5%、ToT 73.3%（论文 4.0%/74%） |

对不上参考值时：**先按第 5 节自查环境/坑，再怀疑实现，最后才允许怀疑结论；任何情况下不改评测代码。**

## 5. 本周真踩过的坑（逐条都是真事）

1. **env 粘连**：`sk-你的key` 和 `OPENAI_API_BASE` 之间**必须留空格**。漏了空格 = 整串被当成 key 的值 → SDK 静默直连 `api.openai.com`（被墙）+ 官方代码无限重试 → 进程活着但永远不出结果。诊断：启动时没有 `Warning: OPENAI_API_BASE is set to ...` 那行。
2. **nohup 静默 ≠ 没跑**：输出全进了 `~/cot_run.log`，屏幕安静是正常。别因为屏幕没动静就再启动一次——两个同参数进程写同一个 json 会互相覆盖，且双倍烧额度。
3. **stdout 8KB 缓冲**：前台跑也经常看着没输出，其实在跑；进度看 json 文件数/大小，别看 stdout。
4. **额度耗尽不报错**：配额用完后进程不退出、按指数退避无限重试，json 冻结。查 usage 端点确认；确认耗尽就 kill 进程，换 key 重跑（重跑会覆盖同参 json，先 cp 备份）。
5. **粘贴多行命令易坏**：Windows 侧复制的多行 `\` 续行命令容易因 CRLF/格式出错；本文档所有命令都是**单行**，整条粘贴。
6. **不要 `export` 依赖**：`wsl.exe bash -c` 是非交互 shell 不加载 .bashrc；key/base 每次 inline 在命令前缀，别假设终端里 export 过（换新终端就挂死）。
7. **额度耗尽空转的进程要杀**：`ps aux | grep run.py` 查残留，养成收工必查的习惯。

## 6. 出数字之后（存档动作）

```bash
mkdir -p logs/archive && cp logs/game24/glm-5.3-flash_0.7_naive_cot_sample_100_start900_end915.json logs/archive/glm-5.3-flash_0.7_naive_cot_sample_100_start900_end915_final_<日期>.json
```

并把汇总数字与运行参数记入 `REPORT.md` 末尾（格式参照已有「复跑确认」一节）。

## 7. 可选下一步（原任务已完成，以下为扩展）

1. ToT 换 key 重跑交叉验证（约 1 小时）
2. 恢复论文配置 b=5、e=3 看 ToT 能否逼近基线（约 3 倍调用量）
3. 换弱模型（如 glm-5.2）验证「推理模型内化搜索」归因——预期其 CoT 大幅低于 84%，ToT 可能反超
4. value 模型判准率对照实验（REPORT.md「下一步怎么验」第 3 条）

## 8. 关键文件地图

| 文件 | 内容 |
|---|---|
| `AGENTS.md` | 本仓库操作说明（与本文档同源，以本文档为准时优先读本文档） |
| `REPORT.md` | 复现结论、证据链、逐题明细 |
| `docs/paper_notes.md` | 论文模块笔记（BFS 搜索 + 状态打分，含伪代码） |
| `docs/presentation.md` | 5 分钟汇报稿 |
| `repro/tot/src/tot/` | 实验代码（判定逻辑 `tasks/game24.py:44-55`，红线区） |
| `repro/tot/logs/game24/` | 结果 json（含官方 gpt-4 校准日志） |
| `repro/tot/logs/archive/` | 已存档的正式结果 |
| `~/combine.py` | 汇总脚本（WSL 家目录，未进 git） |
