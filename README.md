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
2. **配置弱化**：我们的 ToT 是 b=3、e=1（论文 b=5、e=3），这是逐候选只有 82.2% 的部分原因。
3. **限定**：n=15，ToT 15/15 的 95% 置信下界约 78%，与 CoT 85.07%±0.9% 区间重叠 → 只能说 **"ToT 不劣于 CoT"**，不能说"显著优于"。

**曾经被写错的归因（已撤回）**：首轮说"价值模型误剪是净损失"，证据是"900 题 CoT 99/100 对、ToT 0/3 全灭"。那个 0/3 全灭**是搜索跑偏造成的**（候选用的是 propose 示例的数字 2/8/14），不是 value 误剪。修复后同一题 ToT = [1,0,1]。

**一个实现缺陷曾制造了看起来很像真的算法结论**：`get_proposals` 的过滤器把模型回显的 1-shot 示例当成合法提议放行，使 6/15 题的搜索从第 1 步就在错误的数字上进行。修复 = 数字池校验 + 提议重试（**未触碰评测红线 `test_output`**）。

**底线声明**：判定函数 `test_output` 一行未改；搜索机制与论文同构；**所有失败运行都保留**在 `repro/tot/logs/` 与 `logs/archive/`。每个数字的来源见 REPORT.md 逐题明细。

## 怎么跑（别人 clone 下来一条命令能跑）

实验代码在 `repro/tot/`（官方仓库 + 我们的适配 commit `cd8b9ef`）。WSL2 Ubuntu 里：

```bash
cd repro/tot
```

（环境：uv 建 venv 后装官方 requirements，见该仓库 README。环境变量必须在命令里 inline——wsl bash -c 非交互，不加载 .bashrc。完整分步走法：开机检查 → 最小验证 → 后台跑 → 收工 → 汇总，见 [AGENTS.md](AGENTS.md)。）

```bash
# 先跑单测（验证 propose 过滤器，用真实日志样本做断言）
.venv/bin/python tests/test_proposal_filter.py
```

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

> API key 只放环境变量，不进代码、不进 git（任务书 0.3）。结果 json 在 `repro/tot/logs/game24/`。

## 怎么自查结果（不是"跑通了就算"）

```bash
# 门禁测试：轨迹第 1 步是否用题目数字起步（判据经官方 gpt-4 日志对照验证）
.venv/bin/python ~/gate_tot_valid.py "logs/game24/<某个 ToT 日志>.json"
```

通过标准：输出 `PASS`、且"全坏题 0/15"。**修复前这个测试是 FAIL**（6/15 题失效）——
它就是当时能发现这个 bug 的那个检查。

## API 花费（任务书 8.3）

- 计费/额度看网关 usage 接口（不用官方代码的 gpt-4 计价，models.py 已把 cost 置 0）：
  `curl -H 'Authorization: Bearer <key>' https://opencode.ai/zen/go/v1/usage`
- 实测：全周实验（CoT 三次共约 4500 次调用 + ToT 若干次搜索 + 调试 + 修复后全量重跑）
  把月额度从 11% 用到 **15%**（10-14 重置）；本轮同期 CoT 重跑 1500 次调用约 1.25M token。

## 用的 skill（任务书 7.1）

- 本周自建并用上 `skills/wsl-api-experiment/`（后台长实验标准流程）——省掉了"每次启动都要重新踩环境变量、缓冲、监控三连坑"这一步。
- ⏳ 组里现成的 skill 用了哪 2 个、各省了哪一步：<待你补一句>

## 文件地图

| 文件 | 内容 |
|---|---|
| `REPORT.md` | 复现结果（修正后）+ 归因 + 我仍然不知道什么 + **附录 A：被修正的过程** + 附录 B：缺陷定位与修复 |
| `docs/paper_notes.md` | 论文精读：两个核心模块的算法逻辑 |
| `agent_log.md` | Agent 出错记录（≥2 例，附 prompt/原话/发现过程） |
| `debug_log.md` | Bug 根因记录（五类根因） |
| `progress.md` | 每日进度 |
| `skills/wsl-api-experiment/SKILL.md` | 本周沉淀的 skill |
| `repro/tot/tests/test_proposal_filter.py` | propose 过滤器的单测（用真实日志样本做断言） |
| `docs/presentation.md` | 5 分钟汇报稿 |
| `AGENTS.md` | 与 Agent 协作的接口说明 |
