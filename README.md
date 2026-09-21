# Agent 复现周记 — Tree of Thoughts

新生入门任务（一周）：用 Coding Agent 复现 **Tree of Thoughts**（Yao et al., NeurIPS 2023）在 **Game of 24** 上的一个数字：**CoT vs ToT 的准确率**。

## 我复现的是哪个数字 / 论文多少 / 我得到多少

| 口径 | 论文（GPT-4-0613，100 题） | 我（glm-5.3-flash，15 题 900-914） |
|---|---|---|
| CoT 逐样本 | 4.0% | **84.0%**（1260/1500 样本） |
| CoT best-of-100（每题 100 次至少一次成功） | 49% | **100%**（15/15） |
| ToT 每题（io 口径） | 74%（b=5, e=3） | **40.0%**（6/15，b=3, e=1） |

## 差在哪 / 为什么

**方向反转：CoT 反超 ToT。** 这不是复现失败，而是任务书 6.3 的负结果，证据链完整（详见 [REPORT.md](REPORT.md)）：

1. **模型代差**：2026 年的推理模型在隐藏推理流里自带"尝试→发现数字没用完→推翻→换路"的回溯（我们抓取 `reasoning_content` 拿到了一手证据）。ToT 外部搜索干的事被内化进了单次调用，基线从 4% 挪到 84%。
2. **价值模型误剪**：900 题 CoT 99/100 做对、ToT 却 0/3 全灭——"只会猜、不会算"的 value 模型（sure/likely/impossible 三档）把正确分支剪掉且永不复活。
3. **配置弱化**：我们的 ToT 是 b=3、e=1（论文 b=5、e=3），这是 ToT 只有 40% 的部分原因，但不是反转的原因。

**底线声明**：判定函数 `test_output` 一行未改；搜索机制与论文同构；所有失败运行都保留在 `repro/tot/logs/`。每个数字的来源见 REPORT.md 逐题明细。

## 怎么跑（别人 clone 下来一条命令能跑）

实验代码在 `repro/tot/`（官方仓库 + 我们的适配 commit `cd8b9ef`）。WSL2 Ubuntu 里：

```bash
cd repro/tot
```

（环境：uv 建 venv 后装官方 requirements，见该仓库 README。环境变量必须在命令里 inline——wsl bash -c 非交互，不加载 .bashrc。完整分步走法：开机检查 → 最小验证 → 后台跑 → 收工 → 汇总，见 [AGENTS.md](AGENTS.md)。）

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

## API 花费（任务书 8.3）

- 计费/额度看网关 usage 接口（不用官方代码的 gpt-4 计价，models.py 已把 cost 置 0）：
  `curl -H 'Authorization: Bearer <key>' https://opencode.ai/zen/go/v1/usage`
- 实验结束日（2026-09-20）实测：**本月用量 11%**（10-14 重置）、本周 22%——全周实验（CoT 1500 次 + ToT 若干次搜索 + 调试）在预算内。

## 用的 skill（任务书 7.1）

- 本周自建并用上 `skills/wsl-api-experiment/`（后台长实验标准流程）——省掉了"每次启动都要重新踩环境变量、缓冲、监控三连坑"这一步。
- ⏳ 组里现成的 skill 用了哪 2 个、各省了哪一步：<待你补一句>

## 文件地图

| 文件 | 内容 |
|---|---|
| `REPORT.md` | 复现结果 + 负结果归因 + 我仍然不知道什么 |
| `docs/paper_notes.md` | 论文精读：两个核心模块的算法逻辑 |
| `agent_log.md` | Agent 出错记录（≥2 例，附 prompt/原话/发现过程） |
| `debug_log.md` | Bug 根因记录（五类根因） |
| `progress.md` | 每日进度 |
| `skills/wsl-api-experiment/SKILL.md` | 本周沉淀的 skill |
| `docs/presentation.md` | 5 分钟汇报稿 |
| `AGENTS.md` | 与 Agent 协作的接口说明 |
