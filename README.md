# Agent 复现周记 — Tree of Thoughts

新生入门任务（一周）：用 Coding Agent 复现 **Tree of Thoughts**（Yao et al., NeurIPS 2023）在 **Game of 24** 上的一个数字：**CoT vs ToT 的准确率**。

> 📌 **2026-09-25 重大修正**：结论被推翻并重写。首轮得出"CoT 反超 ToT、方向与论文相反"，
> 后经查证那个 40% 是**实现缺陷造成的假象**；修复后 ToT 达到 **100%**，方向与论文一致。
> 详见 [REPORT.md](REPORT.md)（原排查过程完整保留在附录 A）。

## 我复现的是哪个数字 / 论文多少 / 我得到多少

| 口径 | 论文（GPT-4-0613，100 题） | 我（glm-5.3-flash，15 题） |
|---|---|---|
| CoT 逐样本 | 4.0% | **85.07%**（1276/1500；三次跑 84.00/84.33/85.07） |
| CoT best-of-100（每题 100 次至少一次成功） | 49% | **100%**（15/15） |
| **ToT 每题（io 口径，与论文 74% 同口径）** | **74%**（b=5, e=3） | **100.0%**（15/15，b=3, e=1） |
| ToT top-1（value 排名第一，可部署） | — | **100.0%**（15/15） |
| ToT 逐候选 | 29.3%（官方日志复算） | **82.2%**（37/45） |

## 差在哪 / 为什么

**方向一致（ToT > CoT），但差距从 70 个百分点缩小到约 15 个百分点。**

1. **基线被抬高（主因）**：论文里 GPT-4 单次只有 4%，需要外部搜索兜底才到 74%；而现在模型单次就到 85%（我们抓取 `reasoning_content` 拿到一手证据：模型自己在隐藏推理流里"尝试→发现数字没用完→推翻→换路"，一条样本里试了 5 次）。**外部搜索的增量空间只剩 15 个点。**
2. **配置差异（b=3、e=1 vs 论文 b=5、e=3）**：这是声明过的差异，但**不能说它压低了逐候选率**——方向其实不确定：b 变小只是丢掉分数最低的那两个候选，逐候选率反而可能更高；只有 e 变小才会因排序噪声变大而变差。而且**修复后 b=3/e=1 拿到了 io 15/15 = 100%**，说明这批题上它没有可见损失。详见 [REPORT.md](REPORT.md) 归因第 3 条。
3. **限定**：n=15，ToT 15/15 的 95% 置信下界约 78%，与 CoT 85.07%±0.9% 区间重叠 → 只能说 **"ToT 不劣于 CoT"**，不能说"显著优于"。

**曾经被写错的归因（已撤回）**：首轮说"价值模型误剪是净损失"，证据是"900 题 CoT 99/100 对、ToT 0/3 全灭"。那个 0/3 全灭**是搜索跑偏造成的**（候选用的是 propose 示例的数字 2/8/14），不是 value 误剪。修复后同一题 ToT = [1,0,1]。

**一个实现缺陷曾制造了看起来很像真的算法结论**：`get_proposals` 的过滤器把模型回显的 1-shot 示例当成合法提议放行，使 6/15 题的搜索从第 1 步就在错误的数字上进行。修复 = 数字池校验 + 提议重试（**未触碰评测红线 `test_output`**）。

**底线声明**：判定函数 `test_output` 一行未改；搜索机制与论文同构；**所有失败运行都保留**在 `repro/tot/logs/` 与 `logs/archive/`。每个数字的来源见 REPORT.md 逐题明细。

## 怎么跑（从零到出数字）

> ⚠️ **`repro/` 不在仓库里**——`.gitignore` 把它排除了（里面是另一个 git 仓库 + venv）。
> **代码通过 `patches/` 提供**。所以一条命令跑不了，完整路线是下面 5 步（每一步都在干净环境里实测过）。

### ① 拿代码：clone 官方仓库 + 打补丁

```bash
git clone https://github.com/princeton-nlp/tree-of-thought-llm.git repro/tot
cd repro/tot
git checkout 8050e67          # 补丁基于这个 commit（官方仓库当前 HEAD 就是它）
git apply ../../patches/tot-adapt-and-fix.patch
```

补丁里是**两份东西**：本组的网关适配（`run.py` 后端名 / `models.py` 的 max_tokens 与 n=1、`bfs.py` 的过滤器）+ 这次修的 propose 过滤器缺陷。**不含任何密钥。**

### ② 装环境

```bash
uv venv .venv --python 3.11
uv pip install -r requirements.txt
uv pip install -e .            # ← 别漏这行
```

> **`uv pip install -e .` 不能少**：官方 README（第 40 行）有这一步，漏了会让 `run.py` 直接报
> `ModuleNotFoundError: No module named 'tot'`。（`tot` 是 `src/` 下的包，要装进 venv 才能 import。）

### ③ 起本地代理（**必须有**）

> ② 到 ⑤ 步都在 `repro/tot/` 目录里执行（第 ① 步结尾就停在那里），所以仓库根目录是 `../../`。

```bash
node ../../tools/proxy.js &    # 监听 127.0.0.1:8787（脚本在仓库的 tools/ 里）
```

> **为什么必须有**：网关**要求 `x-opencode-session` 头**。直连不带它会返回
> `400 {"type":"MissingSessionID"}`，而 `models.py` 有无限指数退避重试——
> 表象就是**进程活着、一个请求都出不来、永远卡着**。
> 代理干的就两件事：补这个头 + 把 Claude Code 的认证格式转成网关认的（`proxy.js:21-27`）。
>
> 实测对照：直连不带头 → `400 MissingSessionID`；直连**带头** → `200 OK`（1.2 秒）；走代理 → `200 OK`。

### ④ 先跑单测（**不需要 key，10 秒**）

```bash
.venv/bin/python tests/test_proposal_filter.py
```

应该全部 PASS。它验证 propose 过滤器——**这次就是靠这条链上的检查发现实现缺陷的**（详见 `REPORT.md` 附录 B）。

### ⑤ 跑实验

```bash
# CoT 基线：每题 100 样本，5 题一批
OPENAI_API_KEY=sk-... OPENAI_API_BASE=http://127.0.0.1:8787/v1 .venv/bin/python run.py \
  --task game24 --task_start_index 900 --task_end_index 905 \
  --naive_run --prompt_sample cot --n_generate_sample 100 --backend glm-5.3-flash
```

```bash
# ToT（b=3, e=1, greedy）：
OPENAI_API_KEY=sk-... OPENAI_API_BASE=http://127.0.0.1:8787/v1 .venv/bin/python run.py \
  --task game24 --task_start_index 900 --task_end_index 905 \
  --method_generate propose --method_evaluate value --method_select greedy \
  --n_evaluate_sample 1 --n_select_sample 3 --backend glm-5.3-flash
```

**自检信号**：命令一跑应立即打印 `Warning: OPENAI_API_BASE is set to http://127.0.0.1:8787/v1`。
**没看到这行 = 环境变量没带对**，进程会静默挂死（原因见 ③）。

> 环境变量必须 inline 在命令前缀里（`wsl.exe bash -c` 是非交互 shell，不加载 `.bashrc`）。
> API key 只放环境变量，不进代码、不进 git（任务书 0.3）。结果 json 在 `repro/tot/logs/game24/`。

## 怎么自查结果（不是"跑通了就算"）

```bash
# 门禁测试：轨迹第 1 步是否用题目数字起步（判据经官方 gpt-4 日志对照验证）
.venv/bin/python ../../tools/gate_tot_valid.py "logs/game24/<某个 ToT 日志>.json"
```

通过标准：输出 `PASS`、且"全坏题 0/15"。**修复前这个测试是 FAIL**（6/15 题失效）——
它就是当时能发现这个 bug 的那个检查。

## API 花费（任务书 8.3）

- 计费/额度看网关 usage 接口（不用官方代码的 gpt-4 计价，models.py 已把 cost 置 0）：
  `curl -H 'Authorization: Bearer <key>' https://opencode.ai/zen/go/v1/usage`
- 实测：全周实验（CoT 三次共约 4500 次调用 + ToT 若干次搜索 + 调试 + 修复后全量重跑）
  把月额度从 11% 用到 **15%**（10-14 重置）；本轮同期 CoT 重跑 1500 次调用约 1.25M token。

## 用的 skill（任务书 7.1 / 7.2）

- 本周自建并用上 `skills/wsl-api-experiment/`（后台长实验标准流程）——省掉了"每次启动都要重新踩环境变量、缓冲、监控三连坑"这一步。
- 本周还自建了 `skills/explain-code/`（逐行讲解代码，面向零编程基础的读者）：读本机实际文件、把调用链一并读出来、每行讲清"做什么 / 为什么需要 / 关键符号"，被调用的外部函数就在那一行下面就地讲。它是这次"读源码搞懂核心模块"（任务书 §4）过程中重复了十几次的流程。**它不绑定本仓库**——换一个人、换一个仓库照样能用。
- ⏳ 组里现成的 skill 用了哪 2 个、各省了哪一步：<待你补一句>

## 文件地图

| 文件 | 内容 |
|---|---|
| `REPORT.md` | 复现结果（修正后）+ 归因 + 我仍然不知道什么 + **附录 A：被修正的过程** + 附录 B：缺陷定位与修复 |
| `docs/paper_notes.md` | 论文精读：两个核心模块的算法逻辑 |
| `agent_log.md` | Agent 出错记录（≥2 例，附 prompt/原话/发现过程） |
| `debug_log.md` | Bug 根因记录（五类根因） |
| `progress.md` | 每日进度 |
| `evidence/` | **报告里每个数字的原始数据**（结果 json）+ 复算说明；官方 gpt-4 校准日志随官方仓库 clone 自带，不在这里 |
| `patches/tot-adapt-and-fix.patch` | **实验代码的补丁**（`repro/` 不在仓库里，靠它分发；含网关适配 + 过滤器修复） |
| `tools/` | 本地代理 `proxy.js` + 全部复算/自查脚本（`combine.py`、`gate_tot_valid.py`、`verify_numbers.py` 等） |
| `skills/wsl-api-experiment/SKILL.md` | 本周沉淀的 skill（后台长 API 实验流程） |
| `skills/explain-code/SKILL.md` | 逐行讲代码的 skill（本周沉淀，面向零基础读者，不绑定本仓库） |
| `repro/tot/tests/test_proposal_filter.py` | propose 过滤器的单测（**在补丁里**，打完补丁才有） |
| `docs/presentation.md` | 5 分钟汇报稿 |
| `AGENTS.md` | 与 Agent 协作的接口说明 |
