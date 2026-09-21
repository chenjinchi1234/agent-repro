---
name: wsl-api-experiment
description: 在本机 WSL2 上跑长 API 实验（后台启动、实时监控、收数、汇总）。
             当需要在 WSL 里跑论文仓库的 LLM API 实验、或要把长任务安全地放到后台时使用。
---

## 什么时候用

- 要跑 ≥ 10 分钟的 API 实验（CoT 批量采样、BFS/ToT 搜索、批量评测）
- 需要后台运行 + 实时看进度
- 实验代码在 WSL 的某个仓库 venv 里（uv 建的 Python 3.11；系统 python3 是 3.14 没有 pip/sympy，别用）

## 步骤（可以直接复制的命令）

1. **确认三件套**：仓库 venv 存在（`.venv/bin/python`）、网关 key 在手、本地代理活着（`127.0.0.1:8787`，见下"代理说明"）
2. **单条样本先行**：先跑 n=1 的最小命令，人工读一遍模型输出格式——换新模型时这步必做，能省一整天
3. **后台启动（环境变量必须 inline！）**：
   ```bash
   wsl.exe -d Ubuntu -u <user> bash -c "cd <repo> && OPENAI_API_KEY=sk-... \
     OPENAI_API_BASE=http://127.0.0.1:8787/v1 .venv/bin/python run.py ... \
     > ~/<exp>.log 2>&1"
   ```
   （`wsl.exe bash -c` 是非交互 shell，不加载 `.bashrc`，所有 env 只能 inline）
4. **30 秒内验证真的在跑**：`tail ~/proxy.log` 看到第一批 POST 才算启动成功。没有 = 立刻停掉排查（经典死因：env 没带进去，SDK 静默回退 api.openai.com 无限重试）
5. **进度监控看 json 不看 stdout**：Python stdout 有 ~8KB 块缓冲，`.log` 文件可能是空的。进度看每题目/每批次落盘的结果 json，或用 check 脚本数样本数
6. **收工三步**：停任务 → 确认 WSL 里无孤儿进程（`ps aux | grep run.py`）→ 汇总脚本出数字，**人工抽查可加和的列**（列加和 vs 分母对账）

## 检查点：每一步怎么确认成功了

- [ ] 代理日志出现 POST 且无 401/403/500
- [ ] 结果 json 的样本数在涨
- [ ] 网关 usage 接口的 weekly/monthly 百分比在预算内：`curl -H 'Authorization: Bearer <key>' https://opencode.ai/zen/go/v1/usage`
- [ ] 汇总数字能通过一条独立的路径复核

## 常见失败与处理

| 现象 | 处理 |
|---|---|
| 进程在、无请求、CPU 0 | env 没带进 wsl bash -c，停掉 inline 重来 |
| 401 "Missing API key" | 代理分流规则：`/v1/messages` 要 x-api-key，`/v1/chat/completions` 要 Bearer，别混 |
| 403 Forbidden | 加 `User-Agent: OpenAI/Python`（Cloudflare 拦默认 urllib UA） |
| 输出空 content（finish_reason=length） | 推理模型的思考 token 计入 max_tokens：提到 3000，或对该调用加 reasoning_effort=low |
| stdout 日志文件空 | 块缓冲，看 json 或 proxy.log，别等日志文件 |
| 网关 500 / 长超时 | 上游 50-95s 超时，换 flash 档模型或重试 |
| 结果 json 里候选数为 0 | 模型输出格式变化把过滤规则全杀了——先人工读原始输出 |

## 不要做什么

- 不要在 10000 样本上 debug——先 3 条样本端到端
- 不要假设 wsl bash -c 会加载 .bashrc 的 exports
- 不要改官方评测代码凑数字（结果不好就如实写，见任务书第 6 节）
- 不要把 API key 写进任何会进 git 的文件

## 附：代理说明（本机架构）

本地 `~/proxy.js` 监听 127.0.0.1:8787：Anthropic 协议路径（/v1/messages）把 Bearer 转成 x-api-key；OpenAI 路径（/v1/chat/completions）保持 Bearer 原样；统一加 `/zen/go` 前缀转发到 `opencode.ai`。实验代码全部走 `http://127.0.0.1:8787/v1`。
