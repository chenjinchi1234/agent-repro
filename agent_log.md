# agent_log.md — Agent 出错记录

## 2026-09-19 | 掩码漏了 options 字段，完整 API key 打印到会话输出

**发生了什么**：为查 OpenCode Go 额度，读取 ZCode 的 provider 配置（`C:\Users\jinchichen\.zcode\v2\config.json`）。
脚本里给 `models`、`name` 等字段加了 key 掩码，但打印 provider 的 `options` 时直接 `json.dumps(options)`，没走掩码函数 →
`opencode-go-openai` 的完整 apiKey（67 字符，`sk-dRsIs…`）被写进了本轮工具输出。

**影响面**（已核实）：

- 完整 key 落在 `~/.zcode/cli/rollout/model-io-sess_06cb1c46-…jsonl`（本机 ZCode 会话日志）
- **没有**进仓库、**没有**进 git（`grep -rF` 扫过 `repos/agent-repro`，无命中）
- 增量风险有限：同一个 key 本来就以明文存在
  `~/.local/share/opencode/auth.json`、`~/.config/opencode`（Windows 侧）和 ZCode `config.json` 里

**处置建议**：本机自用可不动；若要外发/共享会话记录或日志，先到 OpenCode Go 后台轮换该 key
（`sk-dRsIs…`），并同步更新 `~/.local/share/opencode/auth.json` 与 ZCode 的 provider 配置。

**教训**：读凭据类文件时，掩码要作用在**整个序列化结果**上，而不是挑字段；最稳的做法是压根不打印 `options`，
只打印 key 的前 8 位和长度。

---

## 2026-09-20 | ToT 实验"假启动"：进程在跑，一个请求都没发出去

**我当时的 prompt**：把 ToT 的 BFS 主实验（20 题）放到后台运行，跑完汇总结果。

**Agent 的原话**（大意）："BFS 实验已启动，正在后台跑。"——之后我再问进度时它还说过"在跑，还没出结果"。

**我怎么发现的**：追问"在哪跑的，跑出来之后你会自动检测到吗"之后自己检查：
① `tail ~/proxy.log` 长时间没有新增请求（其它实验的流量在正常滚动，唯独这条没有）；
② 进程存在但 CPU 占用为 0；③ `/proc/<PID>/environ` 里没有任何 `OPENAI_*` 变量。

**真相**：`wsl.exe bash -c` 是非交互 shell，不会加载 `.bashrc` 里配好的 API key/base_url 导出。openai SDK 没拿到 key，
静默回退到官方 `api.openai.com` 无限重试（本机网络不通，就挂在那）。进程"活着"，实验"死着"——
直到手动杀掉（exit 15）。

**教训**：**后台任务"已启动"不等于"在跑"。** 启动后 30 秒内必须在网关日志里看到第一批请求才算数；
这之后我才把"启动后立即查 proxy.log"写成了固定动作（也沉淀进了 skill）。

## 2026-09-20 | 汇总脚本输出 "11/11"，分母写错了

**我当时的 prompt**：写一个脚本，汇总 CoT 和 ToT 的 json 日志，输出逐样本/逐题准确率对比表。

**Agent 的原话**（脚本输出原文）：`ToT 逐候选准确率: 11/11`。

**我怎么发现的**：把脚本打印的逐题"候选总数"列人工加和 = 39，与分母 11 对不上——分子是对的，分母顺手写成了分子。

**真相**：写统计脚本时把"正确候选数"填进了分母位置（`tot_total/tot_total`），一行笔误。正确数字是 11/39 = 28.2%。

**教训**：**汇总数字必须能被独立方式复核**（列加和、与原始 json 计数对账）。Agent 产出的任何"最终数字"，
先找一条不依赖它的路径验证一遍再写进报告。这条 11/11 如果没发现，就会以"100% 准确率"进 REPORT。

## 2026-09-19 | Agent 误判"换 deepseek-v4-flash 就能接替"，浪费一轮调试

**我当时的 prompt**：ToT 在 deepseek-v4-pro 上跑不动（propose 返回空），问 Agent 换哪个模型能继续。

**Agent 的原话**（大意）："改用 deepseek-v4-flash 做 value 判定即可，flash 便宜且配额大。"当时把这条写进了 debug_log 的修法栏。

**我怎么发现的**：按它说的单样本复现——deepseek-v4-flash 的 propose **恒为空**（few-shot 8 示例让它的推理流"验证示例"
耗尽 max_tokens，finish_reason=length），value-mid 一次像样一次不像样（非确定）。换过去只会把实验卡死。

**真相**：真正能同时跑通 propose/value/CoT 三个 prompt 的是 **glm-5.3-flash**（无 effort 参数、2-11s/次、flash 配额）。
Agent 的"哪个模型便宜换哪个"直觉没有考虑"推理模型处理长 few-shot 的行为差异"这个变量。

**教训**：Agent 选模型只看"便宜/配额大"，漏了"该模型在这个 prompt 上到底跑不跑得动"。换模型前必须用
**单样本 + 目标 prompt** 实测（后来这成了 debug_log 里"换模型先测 few-shot 行为"一条的由来）。
