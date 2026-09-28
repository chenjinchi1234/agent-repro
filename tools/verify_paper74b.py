"""论文的 74% 到底是什么口径？
上一个测试发现：cnt_any（只看最后留下的 5 个候选）= 69.0%，而论文写 74%。
但同一份日志上 CoT 家族三行是精确对上的（4.0/9.0/49.0），说明日志就是论文数据。
所以差距应该来自口径。

测一个更宽松的口径：**搜索过程中访问过的任何节点里，只要有一个算对就算这题解出**。
"""
import json, sys
sys.path.insert(0, '/home/jinchichen1/repos/agent-repro/repro/tot/src')
from tot.tasks.game24 import Game24Task

task = Game24Task()
f = '/home/jinchichen1/repos/agent-repro/repro/tot/logs/game24/gpt-4_0.7_propose1_value3_greedy5_start900_end1000.json'
d = json.load(open(f))

any_final = any_node = 0
n_all = n_final = 0
for p in d:
    idx = p['idx']
    # 口径 A：最后留下的 5 个候选（cnt_any）
    rs_final = [i['r'] for i in p['infos']]
    any_final += 1 if any(rs_final) else 0
    n_final += len(rs_final)
    # 口径 B：整棵树里访问过的所有节点
    seen = set()
    hit = False
    for st in p.get('steps', []):
        for y in st.get('new_ys', []):
            if y in seen:
                continue
            seen.add(y)
            n_all += 1
            if task.test_output(idx, y)['r']:
                hit = True
    any_node += 1 if hit else 0

n = len(d)
print("=" * 64)
print(f"{'口径':<44}{'100 题结果':<14}{'论文'}")
print("=" * 64)
print(f"{'A. cnt_any（只看最后留下的 b=5 个）':<44}{f'{any_final}/{n} = {any_final/n:.1%}':<14}74%")
print(f"{'B. 树里访问过的任一节点对就算解出':<44}{f'{any_node}/{n} = {any_node/n:.1%}':<14}74%")
print()
print(f"（口径 B 一共判定了 {n_all} 个节点，平均每题 {n_all/n:.0f} 个；最后只留 5 个 → 口径 A 只看 {n_final} 个）")
