"""独立复核脚本 —— 不依赖 combine.py / final_compare.py，自己解析原始 json 对账。
用法: .venv/bin/python ../../tools/verify_numbers.py
"""
import json, os

BASE = '/home/jinchichen1/repos/agent-repro/repro/tot/logs/game24'


def load(files):
    """返回 {idx: {'per_file': {fname: [r,...]}}}，逐文件保留，便于发现重复计数。"""
    recs = {}
    for fn in files:
        path = os.path.join(BASE, fn)
        if not os.path.exists(path):
            print(f"  !! 缺失文件: {fn}")
            continue
        data = json.load(open(path))
        for p in data:
            recs.setdefault(p['idx'], {})
            recs[p['idx']][fn] = [info['r'] for info in p['infos']]
    return recs


def report(title, files, lo=900, hi=915):
    print("=" * 78)
    print(f"### {title}")
    print(f"    输入文件 ({len(files)}): {', '.join(files) if len(files) <= 4 else str(len(files)) + ' 个'}")
    recs = load(files)
    idxs = sorted(i for i in recs if lo <= i < hi)
    out_of_range = sorted(i for i in recs if not (lo <= i < hi))

    # 重复计数检查：同一题被多个文件覆盖
    dup = {i: sorted(recs[i]) for i in idxs if len(recs[i]) > 1}
    if dup:
        print(f"    [警告] 以下题目被多个文件重复提供，本脚本对每题取所有文件之和: {dup}")

    print(f"    {'idx':<6}{'正确':>6}{'样本':>6}{'该题全对?':>12}")
    R = N = solved = 0
    rows = []
    for i in idxs:
        accs = [r for fn in sorted(recs[i]) for r in recs[i][fn]]
        c, n = sum(accs), len(accs)
        R += c
        N += n
        solved += 1 if any(accs) else 0
        rows.append((i, c, n))
        print(f"    {i:<6}{c:>6}{n:>6}{'YES' if any(accs) else 'no':>12}")

    print(f"    ---- 人工对账 ----")
    print(f"    列加和 sum(正确) = {R}")
    print(f"    分母  sum(样本) = {N}")
    print(f"    逐样本准确率 = {R}/{N} = {R / N:.2%}" if N else "    无样本")
    print(f"    每题至少一次成功 = {solved}/{len(idxs)} = {solved / len(idxs):.1%}" if idxs else "")
    if out_of_range:
        print(f"    (范围外题目已排除: {out_of_range})")
    return R, N, solved, len(idxs)


print("\n########## 1. CoT 正式结果（首轮，3 个分片文件） ##########")
report("CoT 首轮 900-914", [
    'glm-5.3-flash_0.7_naive_cot_sample_100_start900_end905.json',
    'glm-5.3-flash_0.7_naive_cot_sample_100_start905_end910.json',
    'glm-5.3-flash_0.7_naive_cot_sample_100_start910_end915.json',
])

print("\n########## 2. CoT 复跑（单文件，换新 key） ##########")
report("CoT 复跑 900-914", [
    'glm-5.3-flash_0.7_naive_cot_sample_100_start900_end915.json',
])

print("\n########## 3. ToT 正式结果 ##########")
report("ToT 900-914", [
    'glm-5.3-flash_0.7_propose1_value1_greedy3_start900_end915.json',
])

print("\n########## 3b. ToT 分片文件（REPORT.md 表格引用的来源） ##########")
report("ToT 分片 900-914", [
    'glm-5.3-flash_0.7_propose1_value1_greedy3_start900_end905.json',
    'glm-5.3-flash_0.7_propose1_value1_greedy3_start905_end910.json',
    'glm-5.3-flash_0.7_propose1_value1_greedy3_start910_end915.json',
])

print("\n########## 4. 管道校准：官方 gpt-4 日志，同一 15 题 ##########")
report("官方 gpt-4 CoT 900-914", [
    'gpt-4_0.7_naive_cot_sample_100_start900_end1000.json',
])
report("官方 gpt-4 ToT 900-914 (论文配置 b=5,e=3)", [
    'gpt-4_0.7_propose1_value3_greedy5_start900_end1000.json',
])
