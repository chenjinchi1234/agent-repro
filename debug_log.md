# debug_log.md — Bug 根因记录

> 格式按任务书 5.4：一个 bug 一行。根因类别只有五种：**环境/依赖、数据、实现、评测、理解错误**。

| 现象 | 根因类别 | 怎么发现 | 修法 | 怎么防止再犯 |
|---|---|---|---|---|
| 官方代码调网关 API 挂起：网关一直回 401 "Missing API key"，backoff 无限重试 | 环境 | curl 绕过代理直连网关做对照实验：`Authorization: Bearer` → 200；`x-api-key` → 401。与 Anthropic 端点恰好相反（Anthropic 只认 x-api-key，拒绝 Bearer） | 本地代理按路径分流：`/v1/messages` 才做 Bearer→x-api-key 转换，`/v1/chat/completions` 保留 Bearer 原样 | 接入新端点先用 curl 探明认证格式，不要假设两个端点一致 |
| CoT 答案为空（ys=""、r=0），且 usage completion_tokens=1000 正好顶格 | 理解错误 | 日志里 ys 为空 + usage 顶格；对照实验：max_tokens=1000 → content 0 字（finish_reason=length）；3000 → 109 字且解出题目 | `models.py` `gpt()` 默认 max_tokens 1000→3000 | 换推理模型前先确认"思考 token"计入输出上限——思考会吃掉答案的预算 |
| n=2 / n=5 被网关拒绝：invalid_request_error "only n = 1 is supported" | 环境 | curl 探针直接测 n=2 和 n=5 | `models.py` `chatgpt()` 改为每次只发 n=1、循环取满 n 个（已用真实代码路径验证：n=2 返回 2 个样本） | 跑长实验前先探测网关能力边界（n、max_tokens、超时） |
| ToT 第一轮全错：propose 输出 "Possible next steps:" 标题行被当候选送 value，判 sure=20 进 beam | 理解错误 | 打印 BFS 每步 new_ys 与 values，看到垃圾行分数最高、垃圾分支被选中 | `get_proposals` 加输出过滤：只留"数字开头 + left:"步骤行与 "Answer" 行 | 换模型跑长实验前，先人工读一遍模型在该 prompt 下的原始输出格式 |
| propose 输出带 "- " / "• " 项目符号 → 过滤后 0 个合法候选，搜索空转 | 实现 | 910 题候选全空、分数全 0；打印 propose 原始输出发现全是项目符号行 | 过滤前先剥掉 "- "/"• " 前缀再判断 | 过滤规则要用真实日志样本做单测，覆盖模型实际出现的全部格式变体 |
| 911 题搜索到正确答案但 r=0（Answer 行被过滤丢弃） | 理解错误 | 对 911 单题复跑；对照官方 gpt-4 日志：正确轨迹 ys 以 "Answer: ... = 24" 结尾，由 game24.py:68-69 的 24 特判切 cot 提示引出 | 过滤规则放行 answer 开头的行；911 重跑 r=1（Answer: ((1+8)+2)+13 = 24） | 改提示/过滤前先读判定函数 test_output 的完整契约（只看最后一行 + 数字多重集合 + sympy） |
| ValueError: not enough values to unpack (expected 2, got 0)（bfs.py:81） | 实现 | 回溯发现：死局时 propose 输出被过滤为空 → new_ys=[] → zip(*[]) 崩溃 | 过滤后为空时退化 ['']，保持官方"候选永不为空"语义 | 官方代码的隐含假设（候选非空）在换模型后可能失效，加防御性兜底 |
| BFS 后台任务长时间无输出、进程静默挂起 | 环境 | proxy.log 无新增请求；/proc/PID/environ 无 OPENAI_* 变量；进程 CPU=0 | 环境变量 inline 前缀（wsl.exe bash -c 非交互不加载 .bashrc）；启动后 30 秒内查 proxy.log | 后台任务"已启动"≠"在跑"，必须看到第一批网关请求才算数 |
| 推理模型跑 propose/value 返回空 content（finish_reason=length）/ 网关 500 | 理解错误 | 单样本复现：max_tokens=3000 下 reasoning 耗竭；deepseek-v4-pro 的 reasoning 把 8 示例 few-shot 逐一"验证" | glm-5.3 的 value 调用加 reasoning_effort=low（仅此一处）；最终换 glm-5.3-flash（所有 prompt 正常） | 换推理模型先测它处理长 few-shot 的行为（思考 token 计入 max_tokens） |
| urllib 裸调网关 403 Forbidden | 环境 | openai SDK 同参数请求正常、urllib 被拒；加 OpenAI 风格 UA 后通过 | 调网关的脚本带 'User-Agent: OpenAI/Python' | 直连外部网关优先用官方 SDK，或模拟其 UA |
| **ToT 约 1/3 题目的搜索从第 1 步就跑偏**：题 900（数字 `4 5 6 10`）的候选用 `8 / 2`、`14 - 8` 起步——那是 propose prompt 的 1-shot 示例数字（示例输入 `2 8 8 14`）；另有 4 题最终候选是空串 | **实现** | 解释"ToT 分母为什么是 39"时跟着日志走了一遍，打印 `new_ys` 原文发现是示例回显；再写门禁脚本（判据：轨迹**第 1 步**是否用题目数字起步）全量核查 → 首轮 6/15、复跑 5/15；**拿官方 gpt-4 日志作对照得 0/15** 才确认判据本身正确 | `get_proposals` 过滤加**数字池校验**（步骤行两个操作数必须在当前剩余数字池里，回显行自然被拒）；过滤后为空时改为**重试提议**（最多 3 次），不再直接兜底成空候选。**未触碰 `test_output`**（红线）。⚠️ 只治"回显"与"过滤后为空"两类；题 900 的失效是另一根因，见下一行 | 上一条的"防止再犯"已经写了"过滤规则要用真实日志样本做单测"，但**没做**——同一类 bug 于是复发。现已补上 `repro/tot/tests/test_proposal_filter.py`（用日志里真实的 8 行回显做断言）。另：验证链路不能只挑一道题（原报告只用 911 验证就宣布"实现已排除"） |
| 题 900（`4 5 6 10`）的 propose **间歇性返回空**：探测时连续 3 次都空（该题搜索失效），但**修复后重跑时正常解出**（r=[1,1,1]） | **理解错误**（思考 token 计入输出上限） | 打印原始响应：`finish_reason=length`、`completion_tokens=3000` **顶格**、`reasoning_content` **7179 字**、`content` **0 字**——模型在这道题上枚举所有两数组合（`(4,10): +14, diff6, *40>24...`），思考把 3000 的预算用光，还没开始写答案就被截断 | 由同一处**提议重试**（最多 3 次）覆盖：间歇性失效会被下一次尝试救回，实测有效。若要根治可把 propose 的 `max_tokens` 3000→6000，但这类题耗时/费用翻倍 | 这是本表"推理模型跑 propose/value 返回空 content（finish_reason=length）"那条的**复发**——当时靠**换模型**绕开，没根治。**换模型绕过 ≠ 修好**：同一根因会在新模型上换个题目复发。另：**一次观测不足以断言"必然失败"**（我先写成"恒返回空"，重跑成功被打脸）——间歇性 bug 必须多试几次再下结论 |
