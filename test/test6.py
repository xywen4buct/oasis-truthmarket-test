import json

path = r"D:\zhangwen\program\oasis-truthmarket-test\experiments\gpt-4o-mini\newresults\rq1_intent\r_wo\run_1_cognitive_probes.json"

with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

print("type:", type(data))
if isinstance(data, list):
    print("count:", len(data))
    print("keys of item 0:", list(data[0].keys()))
    print("\n=== first item ===")
    print(json.dumps(data[0], ensure_ascii=False, indent=2)[:800])
elif isinstance(data, dict):
    print("keys:", list(data.keys())[:20])
    for k in list(data.keys())[:3]:
        print(f"\n=== {k} ===")
        print(json.dumps(data[k], ensure_ascii=False, indent=2)[:500])