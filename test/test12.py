import json, glob, os
from collections import defaultdict
import statistics

RUNS_DIR = "D:/zhangwen/program/oasis-truthmarket-test/experiments/gpt-4o-mini/newresults/rq1_intent/r_wo"
PROBE_FILES = sorted(glob.glob(os.path.join(RUNS_DIR, "run_*_cognitive_probes.json")))

by_run = []
for fp in PROBE_FILES:
    with open(fp, encoding="utf-8") as f:
        data = json.load(f)
    cnt = defaultdict(lambda: [0, 0])
    for p in data:
        t = p["vulnerability_type"]
        cnt[t][1] += 1
        if p.get("manipulation_detected"):
            cnt[t][0] += 1
    by_run.append(cnt)
    print(f"\n{fp}")
    for t, (hit, tot) in sorted(cnt.items()):
        print(f"  {t:20s}  {hit:3d}/{tot}  {hit/tot*100:5.1f}%")

print("\n=== Cross-run summary (mean ± std) ===")
types = sorted(by_run[0].keys())
for t in types:
    rates = [r[t][0] / r[t][1] * 100 for r in by_run]
    m = statistics.mean(rates)
    s = statistics.stdev(rates) if len(rates) > 1 else 0.0
    print(f"  {t:20s}  {m:5.1f} ± {s:4.1f}%")