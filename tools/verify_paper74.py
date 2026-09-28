"""定论：论文的 74% 对应哪个口径？
用官方 gpt-4 ToT 日志（论文同配置 b=5/e=3）的全部 100 题复算三种口径，
看哪一个等于论文 Table 2 里的 74%。
"""
import json

f = '/home/jinchichen1/repos/agent-repro/repro/tot/logs/game24/gpt-4_0.7_propose1_value3_greedy5_start900_end1000.json'
d = json.load(open(f))
print(f"官方 gpt-4 ToT 日志：{len(d)} 题（task index 900-999 = 官方 Rank 901-1000）")
print(f"每题候选数：{set(len(p['infos']) for p in d)}（论文配置 b=5）")
print()

anyc = top1 = 0
micro_r = micro_n = 0
macro = 0.0
for p in d:
    rs = [i['r'] for i in p['infos']]
    anyc += 1 if any(rs) else 0        # cnt_any：b 个里至少一个对
    top1 += rs[0]                       # top-1：value 排名第一的那个
    micro_r += sum(rs); micro_n += len(rs)
    macro += sum(rs) / len(rs)          # cnt_avg：先每题求平均，再对题求平均

n = len(d)
print("=" * 62)
print(f"{'口径':<36}{'100 题结果':<16}{'论文 Table 2'}")
print("=" * 62)
print(f"{'cnt_any（b 个里至少一个对）':<36}{f'{anyc}/{n} = {anyc/n:.1%}':<16}{'74%'}   ← 候选")
print(f"{'cnt_avg（逐候选，宏平均）':<36}{f'{macro/n:.1%}':<16}{'—'}")
print(f"{'逐候选（微平均 = 分子/分母）':<36}{f'{micro_r}/{micro_n} = {micro_r/micro_n:.1%}':<16}{'—'}")
print(f"{'top-1（value 排名第一）':<36}{f'{top1}/{n} = {top1/n:.1%}':<16}{'—'}")
print()
print("参考：论文 Table 2 里 CoT 家族三行 = CoT 4.0% / CoT-SC 9.0% / CoT(best of 100) 49%")
