import sqlite3, json

db_path = r"D:\zhangwen\program\oasis-truthmarket-test\experiments\gpt-4o-mini\newresults\rq1_intent\r_wo\run_1.db"
con = sqlite3.connect(db_path)
con.row_factory = sqlite3.Row

print("=== analysis_labels 行数 ===")
print(" ", con.execute("SELECT COUNT(*) FROM analysis_labels").fetchone()[0])

print("\n=== 全部记录 ===")
for r in con.execute("SELECT * FROM analysis_labels"):
    d = dict(r)
    for k, v in d.items():
        if isinstance(v, str) and len(v) > 60:
            d[k] = v[:60] + "..."
    print(" ", d)

print("\n=== 关键字段统计 ===")
for col in ["label_manipulator", "label_type", "pattern_confidence",
            "deception_rate_overall", "adaptation_detected",
            "warrant_abuse_detected", "exit_reentry_detected",
            "behavioral_pattern", "market_impact_score"]:
    vals = [r[col] for r in con.execute(f"SELECT {col} FROM analysis_labels")]
    non_null = [v for v in vals if v is not None]
    print(f"  {col:25s} non_null={len(non_null)} unique={sorted(set(map(str, non_null)))}")

print("\n=== 与探针结果对比 ===")
# 探针的判定
probe = json.load(open(r"D:\zhangwen\program\oasis-truthmarket-test\experiments\gpt-4o-mini\newresults\rq1_intent\r_wo\run_1_cognitive_probes.json", encoding="utf-8"))
probe_det = {}
for d in probe:
    probe_det[d["agent_id"]] = probe_det.get(d["agent_id"], 0) + (1 if d["manipulation_detected"] else 0)
for sid in sorted(probe_det):
    row = con.execute("SELECT label_manipulator, deception_rate_overall, pattern_confidence FROM analysis_labels WHERE seller_id=?", (sid,)).fetchone()
    print(f"  agent {sid}: 探针操纵={probe_det[sid]}/25, 行为判定={dict(row) if row else 'N/A'}")