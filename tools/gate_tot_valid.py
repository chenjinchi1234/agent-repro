"""【门禁测试 v3】判据：轨迹的**第 1 步**是否用题目数字起步。

为什么只看第 1 步（前两版都错了，教训记在这）：
  v1 加了 "left: 标注必须精确" → 连论文自己的 gpt-4 数据都 FAIL 14/15，
     因为模型写 left 标注很潦草，而 test_output 根本不看中间标注。
  v2 改成 "所有步的操作数都要在池里" → 仍误判：self.steps=4，
     而**没解出 24** 的轨迹第 4 步必然用池外数字（3 步后池里只剩 1 个数），
     那是"正常的解不出"，不是"在解别的题"。
  v3（本版）：只查第 1 步。第 1 步用题目数字 = 搜索起对了；
             第 1 步用 2/8/14（propose prompt 示例的数字）= 示例回显，搜索从一开始就跑偏。

用法：  .venv/bin/python ../../tools/gate_tot_valid.py <日志文件>
"""
import json, re, sys, glob, os

LINE = re.compile(r'^\s*([\d.]+)\s*([+\-*/])\s*([\d.]+)\s*=\s*([\d.]+)\s*\(left:')


def first_step_ok(problem, traj):
    prob = set(re.findall(r'\d+', problem))
    lines = [l for l in traj.strip().split('\n') if l.strip()]
    if not lines:
        return False, '空轨迹（提议全被过滤 → 兜底成空候选）'
    for l in lines:
        m = LINE.match(l)
        if not m:
            continue
        a, op, b, c = m.groups()
        if a in prob and b in prob:
            return True, f'起步合法：{a} {op} {b}'
        return False, f'起步用了题目外数字：{a} {op} {b}（题目={sorted(prob)}）'
    return False, '第 1 步不是合法算式行'


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    pat = sys.argv[1]
    files = sorted(glob.glob(pat)) if '*' in pat else [pat]
    bad, empty, ok, nq = [], [], 0, 0
    skipped_cot = []
    for f in files:
        for p in json.load(open(f)):
            if not (900 <= p['idx'] < 915):
                continue
            # 门禁判据只对 ToT 日志有意义：ToT 的 info 里有 steps（每层的候选），
            # CoT 日志（--naive_run）没有 steps，喂进来要给人话提示而不是 KeyError
            if 'steps' not in p:
                skipped_cot.append(os.path.basename(f))
                continue
            nq += 1
            x = p['steps'][0]['x'] if p['steps'] else '?'
            rs = [i['r'] for i in p['infos']]
            res = [first_step_ok(x, y) for y in p['ys']]
            n_ok = sum(1 for o, _ in res if o)
            ok += n_ok
            if n_ok == 0:
                bad.append(p['idx'])
                reason = res[0][1]
                if '空轨迹' in reason:
                    empty.append(p['idx'])
                print(f"  [FAIL] 题 {p['idx']}（题目 {x}）候选 {len(res)}，起步合法 {n_ok}，r={rs}")
                print(f"         原因：{reason}")
    if skipped_cot:
        print(f"\n⚠️ 跳过了不含 steps 字段的日志（看起来是 CoT/naive_run 的日志）：{sorted(set(skipped_cot))}")
        print("   门禁测试只适用于 ToT 日志（形如 *_propose1_value*_greedy*_start*.json）。")
    if nq == 0:
        print("\n没有可检查的 ToT 日志。用法见文件开头（要指向 ToT 的日志，不是 CoT 的）。")
        return 2
    print(f"\n题目数 {nq} | 候选 {ok+len(bad)} 起步合法 {ok} | 全坏题 {len(bad)}/{nq} {bad}")
    print(f"  其中空轨迹（提议被过滤光）：{empty}")
    print("PASS" if not bad else "FAIL —— 这些题的搜索从第 1 步就跑偏了")
    return 0 if not bad else 1


if __name__ == '__main__':
    sys.exit(main())
