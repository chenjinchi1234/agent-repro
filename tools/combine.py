import json, sys, glob, os

# 用法: .venv/bin/python combine.py <glob模式> [标签]
# 例:   .venv/bin/python combine.py "logs/game24/glm-5.3-flash_0.7_propose1_value1_greedy3_start*.json" ToT
if len(sys.argv) < 2:
    print(__doc__ or "用法: combine.py <glob模式> [标签]")
    sys.exit(2)
files = sorted(glob.glob(sys.argv[1]))
if not files:
    # 别让"没匹配到"变成 ZeroDivisionError——新人最常见的坑是路径少一层或没先跑实验
    print(f"没匹配到任何文件：{sys.argv[1]}")
    print(f"  当前目录：{os.getcwd()}")
    print(f"  通配符是相对当前目录解析的——先确认路径，或先跑一次实验生成 json。")
    sys.exit(2)
label = sys.argv[2] if len(sys.argv) > 2 else ""
all_accs, puzzles_any, n_puzzles = [], [], 0
for f in files:
    data = json.load(open(f))
    for puzzle in data:
        accs = [info['r'] for info in puzzle['infos']]
        all_accs += accs
        puzzles_any.append(1 if any(accs) else 0)
        n_puzzles += 1
print(f"[{label}] 文件数 {len(files)} 题目数 {n_puzzles} 候选总数 {len(all_accs)}")
print(f"  逐样本准确率 (CoT 口径) : {sum(all_accs)/len(all_accs):.1%}  ({sum(all_accs)}/{len(all_accs)})")
print(f"  每题目至少一次成功 (ToT io 口径): {sum(puzzles_any)/n_puzzles:.1%}  ({sum(puzzles_any)}/{n_puzzles})")
