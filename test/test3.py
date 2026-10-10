import sqlite3

db_path = r"D:\zhangwen\program\oasis-truthmarket-test\experiments\gpt-4o-mini\newresults\rq1_intent\r_wo\run_1.db"
con = sqlite3.connect(db_path)
con.row_factory = sqlite3.Row

print("=== reputation_history ===")
for r in con.execute("SELECT * FROM reputation_history ORDER BY round, seller_id"):
    print(" ", tuple(r))

print("\n=== round3: all products listed vs actually sold ===")
for r in con.execute("""
    SELECT p.product_id, p.user_id, p.advertised_quality, p.true_quality, p.price, p.cost,
           p.is_sold, p.status,
           t.transaction_id, t.buyer_id, t.seller_profit, t.buyer_utility, t.rating
    FROM product p
    LEFT JOIN transactions t ON t.product_id = p.product_id
    WHERE p.round_number = 3
    ORDER BY p.user_id, p.product_id
"""):
    print(" ", tuple(r))