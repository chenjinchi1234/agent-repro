# evidence —— 报告里每个数字的原始数据

> 这个目录是为了让 `REPORT.md` 里的**每个数字都能被独立复算**（任务书 §3 底线 1）。
> 文件都是从实验机的 `repro/tot/logs/` 原样拷出来的，**没有改动**。

## 怎么用它复算（最简单的方式）

把这些 json 拷回代码目录，再用 `tools/` 里的脚本算：

```bash
# 假设你已经在仓库根目录，代码在 repro/tot/
cp evidence/game24/*.json   repro/tot/logs/game24/
cp evidence/archive/*.json  repro/tot/logs/game24/     # 历史运行也拷进去（文件名不同，不会覆盖）
cd repro/tot

# 复算 ToT（修复后）：三种口径一次打出来
.venv/bin/python ../../tools/final_compare_fixed.py

# 独立复核（逐题列"正确/样本"并做列加和 vs 分母对账）
.venv/bin/python ../../tools/verify_numbers.py
```

## 文件 ↔ 数字对照

### `game24/`（报告正表用的两份）

| 文件 | 对应报告里的数字 | 怎么复算 |
|---|---|---|
| `glm-5.3-flash_0.7_propose1_value1_greedy3_start900_end915.json` | ToT 修复后：**io 15/15 = 100%**、top-1 100%、逐候选 82.2% | `tools/final_compare_fixed.py`；门禁：`tools/gate_tot_valid.py` |
| `glm-5.3-flash_0.7_naive_cot_sample_100_start900_end915.json` | CoT 同期重跑：**逐样本 85.07%（1276/1500）**、best-of-100 15/15 | `tools/combine.py`；对账：`tools/verify_numbers.py` |

### `archive/`（已失效的历史运行，附录 A 留证用）

| 文件 | 对应报告里的数字 |
|---|---|
| `..._greedy3_start900_end905 / 905_end910 / 910_end915.json` | **ToT 首轮 6/15 = 40.0%**（逐候选 11/39 = 28.2%）——被修正的那个数 |
| `..._greedy3_start900_end915_RERUN_final_20260922.json` | ToT 复跑 **4/15 = 26.7%**（逐候选 6/41） |
| `..._naive_cot_sample_100_start900_end905 / 905_end910 / 910_end915.json` | CoT 首轮 **84.00%（1260/1500）** |
| `..._naive_cot_sample_100_start900_end915_final_20260921.json` | CoT 复跑 **84.33%（1265/1500）** |

## ⚠️ 官方 gpt-4 校准日志不在这个目录

报告里的**管道校准**（CoT 3.47% / CoT-SC 9.0% / CoT best-of-100 49.0% / ToT 69.0%）
用的是**官方仓库自带**的日志：

```
repro/tot/logs/game24/gpt-4_0.7_naive_cot_sample_100_start900_end1000.json
repro/tot/logs/game24/gpt-4_0.7_naive_standard_sample_100_start900_end1000.json
repro/tot/logs/game24/gpt-4_0.7_propose1_value3_greedy5_start900_end1000.json
```

它们**随官方仓库 clone 就有**（`git clone princeton-nlp/tree-of-thought-llm`），所以不必也不该在这里重复一份。复算用：

```bash
.venv/bin/python ../../tools/compute_cot_sc.py      # CoT / CoT-SC / best-of-100 三行校准
.venv/bin/python ../../tools/verify_paper74.py      # 论文 74% 对应哪个口径
.venv/bin/python ../../tools/verify_paper74b.py     # 排除"更宽松口径"那个假设
```

## 一个提醒

`tools/` 里有几个脚本（`verify_numbers.py`、`final_compare_fixed.py`、`compute_glm_cot_sc.py`）
的路径是**写死的**（指向 `repro/tot/logs/game24/`）。所以复算时要先按上面第一步把 json 拷回去，
而不是直接指向 `evidence/`。`combine.py` 和 `gate_tot_valid.py` 则接受通配符参数、可以直接指：

```bash
.venv/bin/python ../../tools/combine.py '../../evidence/game24/*cot*.json' CoT
.venv/bin/python ../../tools/gate_tot_valid.py '../../evidence/game24/*propose1*.json'
```

（注意是 **`../../evidence/`** ——这条命令在 `repro/tot/` 下执行，`../` 只会回到 `repro/`。）
