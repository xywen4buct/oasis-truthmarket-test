import os

root = r"D:\zhangwen\program\oasis-truthmarket-test"
targets = ["manipulation_detected", "Enhanced behavioral analysis", "/50", "manipulation"]

for dirpath, dirs, files in os.walk(root):
    # 跳过虚拟环境和实验产物
    if ".venv" in dirpath or "experiments" in dirpath or "__pycache__" in dirpath or ".git" in dirpath:
        continue
    for f in files:
        if not f.endswith((".py", ".sh", ".yaml", ".yml")):
            continue
        path = os.path.join(dirpath, f)
        try:
            with open(path, "r", encoding="utf-8") as fh:
                for i, line in enumerate(fh, 1):
                    if any(t in line for t in targets):
                        print(f"{path}:{i}: {line.rstrip()[:160]}")
        except (UnicodeDecodeError, PermissionError):
            continue