# example/plot_fpr_conversion.py
"""画 FPR × conversion 曲线 + 各治理条件对比图。

用法：
    python example/plot_fpr_conversion.py
    # 输出到 results/figures/
"""
import os
import sys
import csv
from collections import defaultdict
import statistics

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(_REPO_ROOT, "results", "governance_experiment.csv")
OUT_DIR = os.path.join(_REPO_ROOT, "results", "figures")


# Windows 中文支持
for fname in ["SimHei", "Microsoft YaHei"]:
    try:
        font_manager.findfont(fname, fallback_to_default=False)
        plt.rcParams["font.sans-serif"] = [fname]
        plt.rcParams["axes.unicode_minus"] = False
        break
    except Exception:
        continue





def load_rows(path):
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def aggregate(rows):
    """按 condition 聚合，返回 {cond: {metric: (mean, sd)}}"""
    by_cond = defaultdict(list)
    for r in rows:
        by_cond[r["condition"]].append(r)

    metrics = ["manipulation_rate", "detection_rate", "false_positive_rate",
               "conversion_rate", "retention_rate", "trust_index"]

    agg = {}
    for cond, rs in by_cond.items():
        agg[cond] = {}
        for m in metrics:
            vals = [float(r[m]) for r in rs]
            mean = statistics.mean(vals)
            sd = statistics.stdev(vals) if len(vals) > 1 else 0.0
            agg[cond][m] = (mean, sd)
    return agg


def plot_fpr_vs_conversion(agg, out_path):
    """只取披露模式的三个条件，画 FPR × conversion。"""
    disclose_conds = ["high_strict", "detect_punish_disclose",
                      "detect_punish_disclose_high_fpr"]
    points = []
    for c in disclose_conds:
        if c not in agg:
            continue
        fpr_m, fpr_sd = agg[c]["false_positive_rate"]
        conv_m, conv_sd = agg[c]["conversion_rate"]
        points.append((c, fpr_m, fpr_sd, conv_m, conv_sd))

    points.sort(key=lambda x: x[1])  # 按 FPR 排序

    x = [p[1] for p in points]
    y = [p[3] for p in points]
    yerr = [p[4] for p in points]
    labels = [p[0] for p in points]

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.errorbar(x, y, yerr=yerr, marker="o", capsize=5,
                linewidth=2, markersize=10, color="#1f77b4")

    for xi, yi, lab in zip(x, y, labels):
        ax.annotate(lab, (xi, yi), textcoords="offset points",
                    xytext=(8, 8), fontsize=9)

    ax.set_xlabel("假阳性率 FPR", fontsize=12)
    ax.set_ylabel("消费者转化率 conversion_rate", fontsize=12)
    ax.set_title("披露模式下 FPR 对转化率的副作用\n(TPR、处罚强度、披露强度固定)",
                 fontsize=13)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()
    print(f"saved: {out_path}")


def plot_condition_bars(agg, out_path):
    """各治理条件在三个核心指标上的柱状图对比。"""
    conds = ["none", "detect_only", "detect_and_punish",
             "detect_punish_disclose", "detect_punish_disclose_high_fpr",
             "high_strict"]
    conds = [c for c in conds if c in agg]

    metrics = [
        ("manipulation_rate", "操纵信号占比"),
        ("conversion_rate", "消费者转化率"),
        ("trust_index", "平台信任指数"),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    for ax, (m, title) in zip(axes, metrics):
        means = [agg[c][m][0] for c in conds]
        sds = [agg[c][m][1] for c in conds]
        x = range(len(conds))
        ax.bar(x, means, yerr=sds, capsize=5, color="#4c72b0", alpha=0.85)
        ax.set_xticks(list(x))
        ax.set_xticklabels(conds, rotation=30, ha="right", fontsize=9)
        ax.set_title(title, fontsize=12)
        ax.grid(True, axis="y", alpha=0.3)

    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()
    print(f"saved: {out_path}")


def main():
    if not os.path.exists(CSV_PATH):
        print(f"CSV not found: {CSV_PATH}")
        sys.exit(1)
    os.makedirs(OUT_DIR, exist_ok=True)

    rows = load_rows(CSV_PATH)
    agg = aggregate(rows)

    print(f"Loaded {len(rows)} rows, {len(agg)} conditions.")
    for c, d in agg.items():
        print(f"  {c}: conv={d['conversion_rate'][0]:.3f}  "
              f"FPR={d['false_positive_rate'][0]:.3f}  "
              f"trust={d['trust_index'][0]:.3f}")

    plot_fpr_vs_conversion(agg, os.path.join(OUT_DIR, "fpr_vs_conversion.png"))
    plot_condition_bars(agg, os.path.join(OUT_DIR, "condition_bars.png"))


if __name__ == "__main__":
    main()