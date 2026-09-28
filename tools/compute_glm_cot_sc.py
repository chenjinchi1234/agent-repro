"""补算 glm-5.3-flash 的 CoT-SC —— 报告里缺的那一行（免费，不调 API）"""
import sys, json, glob
from collections import Counter
sys.path.insert(0, '/home/jinchichen1/repos/agent-repro/repro/tot/src')
from tot.tasks.game24 import Game24Task

task = Game24Task()
BASE = '/home/jinchichen1/repos/agent-repro/repro/tot/logs/game24/'


def last_line(y):
    return y.strip().split('\n')[-1]


def extract_expr(y):
    return last_line(y).lower().replace('answer: ', '').split('=')[0].strip()


def is_failure(t):
    x = last_line(t).lower()
    return any(k in x for k in ['none', 'not possible', 'no solution', 'cannot', 'unable'])


def load(patterns):
    recs = {}
    for pat in patterns:
        for f in sorted(glob.glob(BASE + pat)):
            for p in json.load(open(f)):
                if 900 <= p['idx'] < 915:
                    recs[p['idx']] = p
    return recs


def run(recs, label):
    nq = n = per = best = sc1 = sc2 = sc3 = 0
    for idx in sorted(recs):
        p = recs[idx]
        if 'ys' not in p or not p['ys']:
            print(f"  [警告] idx={idx} 没有 ys 字段，跳过 CoT-SC")
            continue
        nq += 1
        rs = [i['r'] for i in p['infos']]
        per += sum(rs); n += len(rs); best += 1 if any(rs) else 0

        w1 = Counter(last_line(y) for y in p['ys']).most_common(1)[0][0]
        sc1 += task.test_output(idx, w1)['r']

        w2 = Counter(extract_expr(y) for y in p['ys']).most_common(1)[0][0]
        sc2 += task.test_output(idx, 'Answer: ' + w2 + ' = 24')['r']

        def cls(y):
            return '<FAIL>' if is_failure(y) else extract_expr(y)
        w3 = Counter(cls(y) for y in p['ys']).most_common(1)[0][0]
        if w3 != '<FAIL>':
            sc3 += task.test_output(idx, 'Answer: ' + w3 + ' = 24')['r']

    print(f"\n===== {label}（{nq} 题）=====")
    print(f"  CoT 逐样本（报告口径）        : {per}/{n} = {per/n:.1%}")
    print(f"  CoT best-of-100               : {best}/{nq} = {best/nq:.1%}")
    print(f"  CoT-SC 口径1 投票'最后一行原文': {sc1}/{nq} = {sc1/nq:.1%}   ← 论文用的口径")
    print(f"  CoT-SC 口径2 投票'抽出的表达式': {sc2}/{nq} = {sc2/nq:.1%}")
    print(f"  CoT-SC 口径3 失败先归类再投票  : {sc3}/{nq} = {sc3/nq:.1%}")


run(load(['glm-5.3-flash_0.7_naive_cot_sample_100_start900_end905.json',
          'glm-5.3-flash_0.7_naive_cot_sample_100_start905_end910.json',
          'glm-5.3-flash_0.7_naive_cot_sample_100_start910_end915.json']),
    "glm-5.3-flash CoT 首轮（REPORT.md 的 84.0% 来源）")

run(load(['glm-5.3-flash_0.7_naive_cot_sample_100_start900_end915.json']),
    "glm-5.3-flash CoT 复跑（84.3% 那份）")
