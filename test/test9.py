import sqlite3

db_path = r"D:\zhangwen\program\oasis-truthmarket-test\experiments\gpt-4o-mini\newresults\rq1_intent\r_wo\run_1.db"
con = sqlite3.connect(db_path)

print("=== 所有表 ===")
for (name,) in con.execute("SELECT name FROM sqlite_master WHERE type='table'"):
    cols = [r[1] for r in con.execute(f"PRAGMA table_info({name})")]
    print(f"  {name:30s} cols: {cols}")

print("\n=== trace 里的行为分析记录 ===")
for r in con.execute("""
    SELECT user_id, action, substr(info,1,300) FROM trace
    WHERE action NOT IN ('sign_up','interview','list_products','purchase_products','rate_transactions')
"""):
    print(" ", r)