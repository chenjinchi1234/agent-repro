# debug_log.md — Bug 根因记录

> 格式按任务书 5.4：一个 bug 一行。根因类别只有五种：**环境/依赖、数据、实现、评测、理解错误**。

| 现象 | 根因类别 | 怎么发现 | 修法 | 怎么防止再犯 |
|---|---|---|---|---|
| 官方代码调网关 API 挂起：网关一直回 401 "Missing API key"，backoff 无限重试 | 环境 | curl 绕过代理直连网关做对照实验：`Authorization: Bearer` → 200；`x-api-key` → 401。与 Anthropic 端点恰好相反（Anthropic 只认 x-api-key，拒绝 Bearer） | 本地代理按路径分流：`/v1/messages` 才做 Bearer→x-api-key 转换，`/v1/chat/completions` 保留 Bearer 原样 | 接入新端点先用 curl 探明认证格式，不要假设两个端点一致 |
| CoT 答案为空（ys=""、r=0），且 usage completion_tokens=1000 正好顶格 | 理解错误 | 日志里 ys 为空 + usage 顶格；对照实验：max_tokens=1000 → content 0 字（finish_reason=length）；3000 → 109 字且解出题目 | `models.py` `gpt()` 默认 max_tokens 1000→3000 | 换推理模型前先确认"思考 token"计入输出上限——思考会吃掉答案的预算 |
| n=2 / n=5 被网关拒绝：invalid_request_error "only n = 1 is supported" | 环境 | curl 探针直接测 n=2 和 n=5 | （待改）`models.py` `chatgpt()` 每次只发 n=1，循环取够样本 | 跑长实验前先探测网关能力边界（n、max_tokens、超时） |
