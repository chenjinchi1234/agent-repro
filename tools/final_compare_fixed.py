"""全量重跑结果的完整口径核算 + 与修复前的对比"""
import json, os, re

REPO = '/home/jinchichen1/repos/agent-repro/repro/tot/logs/game24/'
NEW = REPO + 'glm-5.3-flash_0.7_propose1_value1_greedy3_start900_end915.json'

d = json.load(open(NEW))
print("=== 全量重跑（修复后）逐题明细 ===")
print(f"{'idx':<6}{'候选 r':<22}{'候选数':>6}{'top1':>6}{'io':>5}")
allr, n = [], 0
anyc = top1 = 0
for p in d:
    rs = [i['r'] for i in p['infos']]
    allr += rs
    n += len(rs)
    anyc += 1 if any(rs) else 0
    top1 += rs[0]
    print(f"{p['idx']:<6}{str(rs):<22}{len(rs):>6}{rs[0]:>6}{'YES' if any(rs) else 'no':>5}")

print()
print("=== 三种口径 ===")
print(f"  io 口径（每题至少一次成功，论文 74% 用这个）: {anyc}/{len(d)} = {anyc/len(d):.1%}")
print(f"  top-1 口径（value 排名第一，可部署）      : {top1}/{len(d)} = {top1/len(d):.1%}")
print(f"  逐候选口径                                : {sum(allr)}/{n} = {sum(allr)/n:.1%}")

print()
print("=== 与修复前对比 ===")
print(f"{'口径':<34}{'修复前(首轮)':<16}{'修复后':<12}")
print(f"{'io 每题至少一次成功':<34}{'6/15 = 40.0%':<16}{anyc/len(d):>10.1%}")
print(f"{'逐候选':<34}{'11/39 = 28.2%':<16}{sum(allr)/n:>10.1%}")
print(f"{'top-1（修复前未算过）':<34}{'—':<16}{top1/len(d):>10.1%}")

print()
print("=== 与 CoT 对比（同一模型 glm-5.3-flash，同一 15 题）===")
print(f"{'口径':<34}{'CoT':<22}{'ToT(修复后)':<14}")
print(f"{'单次尝试':<34}{'84.0%（100 样本平均）':<22}{top1/len(d):>10.1%}")
print(f"{'best-of-k':<34}{'100%（k=100）':<22}{anyc/len(d):>10.1%}")
