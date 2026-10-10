import json

path = r"D:\zhangwen\program\oasis-truthmarket-test\experiments\gpt-4o-mini\newresults\rq1_intent\r_wo\run_1_cognitive_probes.json"
data = json.load(open(path, "r", encoding="utf-8"))

print("total:", len(data))
print("manipulation_detected=true:", sum(1 for d in data if d["manipulation_detected"]))
print()

from collections import Counter
print("by vulnerability_type:")
for k, v in Counter(d["vulnerability_type"] for d in data).most_common():
    sub = [x for x in data if x["vulnerability_type"] == k]
    det = sum(1 for x in sub if x["manipulation_detected"])
    chose_a = sum(1 for x in sub if x.get("selected_option") == "A")
    print(f"  {k:25s} n={len(sub):3d}  manipulation={det}  chose_A={chose_a}")

print("\nby agent:")
for k, v in sorted(Counter(d["agent_id"] for d in data).items()):
    sub = [x for x in data if x["agent_id"] == k]
    det = sum(1 for x in sub if x["manipulation_detected"])
    print(f"  agent {k}: n={v} manipulation={det}")

import json
data = json.load(open(path, "r", encoding="utf-8"))
non_null = [d for d in data if d.get("severity_score") is not None]
print("severity_score non-null:", len(non_null))
for d in non_null[:5]:
    print(" ", d["agent_id"], d["round_num"], d["vulnerability_type"], d["severity_score"], d["selected_option"])


import json

data = json.load(open(path, "r", encoding="utf-8"))

# 按 round 看演变
from collections import defaultdict
by_round = defaultdict(lambda: {"n":0,"det":0})
for d in data:
    by_round[d["round_num"]]["n"] += 1
    by_round[d["round_num"]]["det"] += int(d["manipulation_detected"])
print("by round:")
for r in sorted(by_round):
    print(f"  round {r}: {by_round[r]['det']}/{by_round[r]['n']}")

# 同时查代码里的汇总逻辑
print("\n=== 搜索汇总口径 ===")