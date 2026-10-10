import sqlite3

db_path = r"D:\zhangwen\program\oasis-truthmarket-test\experiments\gpt-4o-mini\newresults\rq1_intent\r_wo\run_1.db"
con = sqlite3.connect(db_path)
con.row_factory = sqlite3.Row

print("=== distinct actions ===")
for r in con.execute("SELECT action, COUNT(*) FROM trace GROUP BY action ORDER BY COUNT(*) DESC"):
    print(" ", tuple(r))

print("\n=== all trace rows ===")
for r in con.execute("SELECT user_id, created_at, action, substr(info,1,150) as info_preview FROM trace ORDER BY created_at, user_id"):
    print(" ", tuple(r))

print("\n=== agent identities (sign_up rows) ===")
for r in con.execute("SELECT user_id, json_extract(info,'$.name') as name, substr(json_extract(info,'$.bio'),1,100) as bio FROM trace WHERE action='sign_up'"):
    print(" ", tuple(r))

print("\n=== fraud rate by seller & round ===")
for r in con.execute("""
    SELECT p.user_id, p.round_number,
           COUNT(*) as listed,
           SUM(CASE WHEN p.advertised_quality='HQ' AND p.true_quality='LQ' THEN 1 ELSE 0 END) as fraud_listed,
           SUM(CASE WHEN p.advertised_quality='HQ' AND p.true_quality='LQ' AND p.is_sold=1 THEN 1 ELSE 0 END) as fraud_sold
    FROM product p
    GROUP BY p.user_id, p.round_number
    ORDER BY p.user_id, p.round_number
"""):
    print(" ", tuple(r))

print("\n=== does fraud pay off? ===")
for r in con.execute("""
    SELECT p.user_id,
           SUM(CASE WHEN p.advertised_quality='HQ' AND p.true_quality='LQ' AND p.is_sold=1 THEN p.price-p.cost ELSE 0 END) as fraud_profit,
           SUM(CASE WHEN p.advertised_quality=p.true_quality AND p.is_sold=1 THEN p.price-p.cost ELSE 0 END) as honest_profit,
           SUM(p.is_sold) as items_sold
    FROM product p
    GROUP BY p.user_id
"""):
    print(" ", tuple(r))