import sqlite3
import os

db_path = r"D:\zhangwen\program\oasis-truthmarket-test\experiments\gpt-4o-mini\newresults\rq1_intent\r_wo\run_1.db"

print("file exists:", os.path.exists(db_path))
print("file size:", os.path.getsize(db_path) if os.path.exists(db_path) else "N/A")

con = sqlite3.connect(db_path)
con.row_factory = sqlite3.Row

print("=== tables ===")
for (name,) in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
    print(" ", name)

print("\n=== schema: product ===")
for r in con.execute("PRAGMA table_info(product)"):
    print(" ", r)

print("\n=== schema: transactions ===")
for r in con.execute("PRAGMA table_info(transactions)"):
    print(" ", r)

print("\n=== profit per round ===")
for r in con.execute("""
    SELECT round_number,
           COUNT(*) AS deals,
           SUM(seller_profit) AS profit,
           COUNT(DISTINCT seller_id) AS sellers
    FROM transactions
    GROUP BY round_number ORDER BY round_number
"""):
    print(" ", tuple(r))

print("\n=== probe distribution ===")
try:
    for r in con.execute("""
        SELECT probe_type,
               COUNT(*) AS n,
               SUM(CASE WHEN json_extract(response,'$.selected_option')='A' THEN 1 ELSE 0 END) AS chose_A,
               SUM(CASE WHEN json_extract(response,'$.selected_option')='B' THEN 1 ELSE 0 END) AS chose_B
        FROM cognitive_probes
        GROUP BY probe_type
    """):
        print(" ", tuple(r))
except Exception as e:
    print("  (no cognitive_probes table or error:", e, ")")

print("\n=== round3 listing vs delivery ===")
for r in con.execute("""
    SELECT p.round_number, p.product_id, p.advertised_quality, p.true_quality, p.is_sold,
           t.transaction_id, t.advertised_quality, t.true_quality, t.seller_profit
    FROM product p
    LEFT JOIN transactions t ON t.product_id = p.product_id
    WHERE p.round_number = 3 AND p.user_id = 1
"""):
    print(" ", tuple(r))