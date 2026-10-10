import sqlite3

db_path = r"D:\zhangwen\program\oasis-truthmarket-test\experiments\gpt-4o-mini\newresults\rq1_intent\r_wo\run_1.db"
con = sqlite3.connect(db_path)
con.row_factory = sqlite3.Row

print("=== trace columns ===")
for r in con.execute("PRAGMA table_info(trace)"):
    print(" ", r["name"], r["type"])

print("\n=== trace row count ===")
print(" ", con.execute("SELECT COUNT(*) FROM trace").fetchone()[0])

print("\n=== one trace row ===")
row = con.execute("SELECT * FROM trace LIMIT 1").fetchone()
for k in row.keys():
    v = str(row[k])
    print("  ", k, "=", v[:200], "..." if len(v) > 200 else "")