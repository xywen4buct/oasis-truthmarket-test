import sqlite3

db_path = r"D:\zhangwen\program\oasis-truthmarket-test\experiments\gpt-4o-mini\newresults\rq1_intent\r_wo\run_1.db"
con = sqlite3.connect(db_path)
con.row_factory = sqlite3.Row

print("=== product columns ===")
for r in con.execute("PRAGMA table_info(product)"):
    print(" ", r["name"], r["type"])

print("\n=== transactions columns ===")
for r in con.execute("PRAGMA table_info(transactions)"):
    print(" ", r["name"], r["type"])

print("\n=== one row from product ===")
for r in con.execute("SELECT * FROM product LIMIT 1"):
    for k in r.keys():
        print("  ", k, "=", r[k])

print("\n=== one row from transactions ===")
for r in con.execute("SELECT * FROM transactions LIMIT 1"):
    for k in r.keys():
        print("  ", k, "=", r[k])

print("\n=== product count per round ===")
for r in con.execute("SELECT round_number, COUNT(*) FROM product GROUP BY round_number ORDER BY round_number"):
    print(" ", tuple(r))

print("\n=== reputation_history ===")
for r in con.execute("PRAGMA table_info(reputation_history)"):
    print(" ", r["name"], r["type"])
for r in con.execute("SELECT * FROM reputation_history ORDER BY round_number LIMIT 20"):
    print(" ", tuple(r))