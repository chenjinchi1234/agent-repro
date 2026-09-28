---
name: doc-it
description: >
  Audit and tidy project documentation: inventory every doc file, then flag
  stale references (paths/commands/env vars that no longer exist), missing
  coverage, and internal inconsistencies between files — and restructure docs
  that have grown messy from repeated appends. Use when docs feel cluttered,
  when a repo has accumulated several overlapping README/AGENTS/HANDOFF files,
  when you want to know what documentation is missing or out of date, or before
  handing a repo to someone else. Triggers: "整理文档", "体检文档", "文档乱了",
  "audit the docs", "tidy up the docs", "doc-it".
allowed-tools: [Read, Grep, Glob, Bash, Write]
argument-hint: "<path> 目标文件/目录，或 'all' 做全仓库审计"
user-invocable: true
---

# 审计并整理项目文档

> **出处**：本 skill 取自 [Dosu 的 `/doc-it`](https://dosu.dev/blog/claude-code-skill-doc-it)
> （完整 SKILL.md 在 [onlydole/overdue](https://github.com/onlydole/overdue/blob/main/.claude/skills/doc-it/SKILL.md)，
> Apache-2.0）。**本地改动**：① 加了 Step 3.5「重组结构」（原版只做最小改动，不解决"积累成一团"的问题）；
> ② 加了"保护既有约束"一节（很多仓库的文档结构是外部要求规定的，不能随便动）。

## 什么时候用

- 文档读起来乱：反复往上追加的「补充」「更新」块堆在一起，读者找不到主线
- 仓库里有多份讲同一件事的文件（README / AGENTS / HANDOFF），开始互相矛盾
- 想知道哪些文档过期了、缺什么
- 把仓库交给别人之前

用法：`all` 做全仓库审计；也可以只针对一个文件或目录。

## 工作流

### Step 1 · 清点（Discover）

扫描仓库里的文档：

- 根目录：`README.md`、`AGENTS.md`、`CLAUDE.md`、`CONTRIBUTING.md`、`CHANGELOG.md`、`LICENSE` 等
- 文档目录：`docs/`、`documentation/`、`doc/`、`wiki/`
- **先查软链接**：`ls -la` 每个根级 md。很多仓库把 `CLAUDE.md` 软链到 `AGENTS.md`——
  那样只能改**真身**，改别名会让真身保持过期。若两份是各自独立的文件，则视为独立文件，但要在审计里标出内容分歧。
- 顺带看配置清单（`package.json`、`pyproject.toml`、`Makefile`…），它们决定文档里写的命令是不是真的

**产出**：一份清单——文件路径（标注软链接）、最后修改时间、大概行数、一句话说它覆盖什么。

### Step 2 · 审计（Audit）

对 Step 1 找到的每份文档（只认真身）：

1. **过期引用**：文档提到的文件、目录、命令、环境变量、配置项，在代码里还存不存在
2. **覆盖缺口**：代码里有、文档里没写的东西
3. **内部矛盾**：两份文档讲同一件事但说法不一致

**产出**：一张表——文件 / 问题类型（过期·缺失·矛盾）/ 具体位置 / 建议修法。

### Step 3 · 修（Update）

按审计结果改文档：

- **保留**原有结构、语气、排版
- 加缺失的段落；删（或标记）指向已删代码的引用
- 把示例、命令、配置值更新到与代码一致
- 每处改动留一个短注释（`<!-- updated by /doc-it -->`），方便 review 找到改了哪

### Step 3.5 · 重组结构（Restructure）—— 原版没有这一步

> 原版 `/doc-it` 的原则是"**最小改动**，不重写已经正确的段落"。这适合日常维护，
> 但治不了"文档被反复追加成了一团"。当审计发现下面任一情况时，走这一步：
>
> - 同一个主题的「补充」块散落在多处（尤其是正文中段插进来的事后说明）
> - 正文里夹着已失效内容（靠删除线、`⚠️ 已推翻` 之类标记撑住）
> - 同一件事在两份文件里各写一遍，措辞还不完全一样
> - 读者要跳着读才能拼出完整故事

**重组的三条规矩**：

1. **只搬家，不改事实**。数字、结论、状态一律不动——只调顺序、合并重复、把事后补丁归位。
2. **正文只留"现在的结论"，历史进附录**。被推翻的分析、排查过程、修订记录，统一收到
   文末的附录/修订记录里；正文里用一句话点明"曾经错过什么、细节见附录"。
3. **重组完必须重新验证**：数字还能复现、对外承诺的结构（比如任务书/规范要求的章节）没被破坏、
   所有交叉引用仍然解析得到。**没有验证的重组不算完成。**

   > ⚠️ **光验证"路径能解析"不够**（2026-09-28 实测踩到）：文档里的命令可能**路径是对的、
   > 但算出来是错的**。实例：一条汇总命令写的是 `combine.py 'logs/.../start9*.json'`，
   > 通配符同时命中了**分片文件**（`start900_end905`、`start905_end910`…）**和合并文件**，
   > 还把区间外的题目带了进来；脚本简单相加、不去重 → **题目数从 15 变成 32、
   > 准确率从 85.1% 变成 84.4%**——数字看起来很像真的，但是错的。
   >
   > **所以：文档里凡是带通配符、聚合、统计的命令，都要实跑一遍，并核对"分母和口径对不对"**，
   > 不能只确认"这个文件存在"。

### Step 4 · 补缺失的文档（Generate）

代码里有、但文档里完全没有的东西（新模块、新脚本、新流程）。**不要凭空造**：能从代码/配置里
读出来的才写；读不出来的标成"缺口"（见 Step 6）。

### Step 5 · 提建议（Recommend）

列出"这个仓库应该考虑补的文档"，一句话说明为什么。**只建议，不擅自生成**。

### Step 6 · 汇报（Report）

- **改了什么**：文件 + 一句话
- **新建了什么**
- **建议补什么**
- **缺口**：从代码看不出来的信息（部署目标、团队约定等）

## 保护既有约束（**动手前必做**）

很多仓库的文档结构是**外部要求**规定的，不是随手写的。重组之前先找出这些约束，写下来，**重组后逐条核对**：

- 任务书 / 规范 / 评审清单要求的章节与格式（例：`debug_log` 必须是"现象|根因类别|怎么发现|修法|怎么防止再犯"五列表，根因必须归到给定的五类）
- 谁在读这份文档：是给人看、给 AI 看、还是给评审看？**给评审看的不能为了好读而改结构**
- 文档之间约定的接口（别的文件按固定名字引用它）

> 一句话：**排版可以重排，承诺不能动。**

## 质量红线

- 不编造：代码里没有的字段、命令、环境变量、参数，一律不写
- 每个代码示例都要能真的跑
- **拿不准就标成缺口**，不要用猜测填
- 沿用仓库既有的语气、排版、标题风格
- 只写代码真会产生的返回码、错误信息、返回值
- 拿不准某个参数的用途就写"见源码 `[文件:行号]`"
- **Step 3 的最小改动原则**只适用于日常维护；Step 3.5 的重组是另一回事，别混用
