# Tree of Thoughts 论文笔记

> 复现目标：**Game of 24 上 CoT vs ToT 的准确率**（论文：CoT 4.0% vs ToT 74%）
> 论文：Yao et al., *Tree of Thoughts: Deliberate Problem Solving with Large Language Models*, NeurIPS 2023
> 官方代码：`princeton-nlp/tree-of-thought-llm`（clone 于 `~/repos/agent-repro/repro/tot`）
> 本文档是初稿骨架，标注 ⏳ 的地方要自己填。

## 读论文的三个问题（Day 1，用自己的话）

**1. 它解决什么问题？**

> 现在的自回归生成模型受到生成方式的限制（从左到右逐词生成，不能中途回溯、无法分支探索），对于需要前瞻性和回溯性的问题解决得不好，ToT 补足了这一点。


**2. 核心方法是什么？**

> 把解题过程分解成一步步，每一步保存之前的思路，这样能保证回溯性；每个节点生成多个不同的候选思路，评估打分，选最好的一条或几条继续往下走。


**3. 它凭什么说有效？**

> 摘要里 Game of 24：同一个模型（GPT-4），不用 ToT（即 CoT）成功率 4%，用了 ToT 成功率 74%。


## 核心模块 vs 脚手架

| | 内容 | 处理 |
|---|---|---|
| 核心模块 1 | 思维树的搜索策略：BFS 逐层扩展（bfs.py 的 `solve()`） | 要搞懂到能画出来 |
| 核心模块 2 | 状态打分：把候选中间步骤交给模型评估 sure/likely/impossible（`get_value` + value prompt） | 同上 |
| 脚手架 | 各任务 prompt 模板、数据加载、答案评测（`test_output`）、日志输出 | 跑通就行 |

判断标准（任务书 4.2）：把这块删掉，论文的方法就不成立了——那它就是核心。

## 模块一：BFS 搜索（Day 3 填）

- 论文原句：3.4.(a) Breadth-first search (BFS) (Algorithm 1) maintains a set of the b most promising states
per step. This is used for Game of 24 and Creative Writing where the tree depth is limit
(T ≤3), and initial thought steps can be evaluated and pruned to a small set (b ≤ 5).
- 我的翻译：广度优先搜索———bfs保留了b个最有潜力的想法，并且不断迭代，保持只有5个最有潜力的想法，这被用在了24点和创意写作游戏上，根据思维树的深度，它可以被限制在一定的合集里面。
- 输入 / 输出：⏳（in = 题目 x + 当前候选 ys；out = 4 步之后的最终候选）
- 伪代码函数 
搜索(题目编号 idx):
##
    题目 x = 取第 idx 题
    当前候选集合 ys = ['']           # 空轨迹，还没走
    每层记录 infos = []

    for step in 0 .. steps-1:        # Game24 固定 4 层
        # ---------- （1） 生成：对每个候选长出子候选 ----------
        子候选集合 = []
        for y in ys:
            回复 = 模型(模板_propose(当前剩余数字), n=1)
            拆成一行行，每条提议接到 y 后面 -> 得到若干新轨迹
            子候选集合.加入这些新轨迹
        # 现在 子候选集合 = 这一层所有新候选（可能几十个）

        # ---------- （2） 评估：给每个子候选打分 ----------
        分数 = 批量打分(x, 子候选集合, n_evaluate_sample)

        # ---------- （3）选择：只留最好的 b 个 ----------
        # greedy 策略（Game24 默认）：
        按下标，依分数从大到小排序
        选出前 b 个 的轨迹 -> 选中集合
        # （sample 策略则是：把分数归一化成概率，按概率随机抽 b 个）

        # ---------- （4）记录并推进 ----------
        infos.记录(step, 子候选, 分数, 选中集合)
        当前候选集合 = 选中集合          # 进入下一层

    return 当前候选集合, infos
##
- 代码位置：（`bfs.py:49-88`，已打开核对）
- 我做的验证：⏳
- 我还不懂：bfs反馈提示词给模型之后，应该生成多少个候选

## 模块二：状态打分（Day 3 填）

- 论文原句：
- 我的翻译：
- 输入 / 输出：⏳（in = 题目 + 一个中间步骤；out = 分数 0.001 / 1 / 20）
- 伪代码：⏳
- 代码位置：⏳（`bfs.py:6-26` + `game24.py` 的 `value_prompt_wrap` / `value_outputs_unwrap`）
- 我做的验证：⏳
- 我还不懂：⏳

## 复现实验设计（Day 3-4）

- 要复现的数字：论文 CoT 4.0% vs ToT 74%（100 题 × 100 样本，GPT-4）
- 我的规模：⏳（约 20 题 × 100 样本；模型待定）
- 环境适配（**不算改评测代码**，评测逻辑 `test_output` 一行没动）：
  1. `--backend` 增加网关模型名
  2. `gpt()` 默认 max_tokens 1000→3000（推理模型思考 token 计入上限）
  3. `chatgpt()` 分块改 n=1（网关只支持 n=1）
- 每个数字都能解释：数字来源与解释见 REPORT.md
