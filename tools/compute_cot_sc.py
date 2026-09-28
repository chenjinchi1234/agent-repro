"""从官方 gpt-4 CoT 日志免费复算 CoT / CoT-SC / best-of-100
论文的三种口径（§4.1 Baselines + Table 2）：
  CoT            = 每题采 100 次，"for average performance"  → 单样本正确率
  CoT-SC (k=100) = "takes the majority output from 100 CoT samples" → 投票后判对错
  CoT (best of 100) = 100 个样本里至少一个正确
"""
import sys, re
from collections import Counter
sys.path.insert(0, '/home/jinchichen1/repos/agent-repro/repro/tot/src')
from tot.tasks.game24 import Game24Task

task = Game24Task()
LOG = '/home/jinchichen1/repos/agent-repro/repro/tot/logs/game24/gpt-4_0.7_naive_cot_sample_100_start900_end1000.json'
import json
data = json.load(open(LOG))


def last_line(y):
    return y.strip().split('\n')[-1]


def extract_expr(y):
    """按 test_output 的规则抽出表达式（最后一行、去 answer:、取 = 左边）"""
    return last_line(y).lower().replace('answer: ', '').split('=')[0].strip()


def is_failure(text):
    """识别'我解不出来'类输出"""
    t = last_line(text).lower()
    return any(k in t for k in ['none', 'not possible', 'no solution', 'cannot', 'unable'])


def run(scope_idx, label):
    n = per_sample = bestof = 0
    sc_exact = sc_expr = sc_grouped = 0
    nq = 0
    for p in data:
        if p['idx'] not in scope_idx:
            continue
        nq += 1
        rs = [i['r'] for i in p['infos']]
        ys = p['ys']
        per_sample += sum(rs)
        n += len(rs)
        bestof += 1 if any(rs) else 0

        # CoT-SC 口径 1：对"最后一行原文"投票（论文字面意义的 majority output）
        w1 = Counter(last_line(y) for y in ys).most_common(1)[0][0]
        sc_exact += task.test_output(p['idx'], w1)['r']

        # CoT-SC 口径 2：对"抽出的表达式"投票
        w2 = Counter(extract_expr(y) for y in ys).most_common(1)[0][0]
        sc_expr += task.test_output(p['idx'], 'Answer: ' + w2 + ' = 24')['r']

        # CoT-SC 口径 3：先把所有失败输出归成一类再投票（避免失败信息因措辞雷同而胜出）
        def cls(y):
            return '<FAIL>' if is_failure(y) else extract_expr(y)
        w3 = Counter(cls(y) for y in ys).most_common(1)[0][0]
        if w3 != '<FAIL>':
            sc_grouped += task.test_output(p['idx'], 'Answer: ' + w3 + ' = 24')['r']

    print(f"\n===== {label}（{nq} 题）=====")
    print(f"  CoT（每题 100 次取平均，论文口径） : {per_sample}/{n} = {per_sample/n:.1%}")
    print(f"  CoT (best of 100)                  : {bestof}/{nq} = {bestof/nq:.1%}")
    print(f"  CoT-SC 口径1 投票'最后一行原文'     : {sc_exact}/{nq} = {sc_exact/nq:.1%}")
    print(f"  CoT-SC 口径2 投票'抽出的表达式'     : {sc_expr}/{nq} = {sc_expr/nq:.1%}")
    print(f"  CoT-SC 口径3 失败先归类再投票       : {sc_grouped}/{nq} = {sc_grouped/nq:.1%}")


all_idx = set(p['idx'] for p in data)
run(all_idx, "官方 gpt-4 日志全部 100 题（论文 Table 2 的范围：Rank 901-1000）")
run(set(range(900, 915)), "官方 gpt-4 日志前 15 题（= 你们实验的范围）")
