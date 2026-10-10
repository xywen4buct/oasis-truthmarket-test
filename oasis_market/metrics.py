# oasis_market/metrics.py
"""仿真指标计算。

指标：操纵发生率、检出率、误报率、转化率、留存率、声誉轨迹方差、平台信任指数。
"""
from typing import List, Dict
from collections import defaultdict
import statistics


def _safe_div(a, b):
    return a / b if b else 0.0


def compute_metrics(signals: List[dict], events: List[dict],
                    orders: List[dict], reputation_traj: List[dict],
                    num_consumers: int, num_sessions: int) -> Dict:
    # 信号侧
    manip = [s for s in signals if s.get("source_label") == "manipulative"]
    real = [s for s in signals if s.get("source_label") == "real"]
    manipulation_rate = _safe_div(len(manip), len(signals))

    # 治理侧
    tp = sum(1 for e in events if e["detection_result"] == "tp")
    fp = sum(1 for e in events if e["detection_result"] == "fp")
    fn = sum(1 for e in events if e["detection_result"] == "fn")
    detection_rate = _safe_div(tp, tp + fn)
    false_positive_rate = _safe_div(fp, fp + max(len(real) - fp, 0))

    # 交易侧
    conversion_rate = _safe_div(len(orders), num_consumers * num_sessions)

    # 留存：跨场次重复出现的消费者
    by_consumer = defaultdict(set)
    for o in orders:
        by_consumer[o["consumer_id"]].add(o["session_id"])
    multi_session = sum(1 for c, s in by_consumer.items() if len(s) > 1)
    retention_rate = _safe_div(multi_session, max(len(by_consumer), 1))

    # 声誉轨迹方差（按主播聚合）
    by_streamer = defaultdict(list)
    for r in reputation_traj:
        by_streamer[r["streamer_id"]].append(r["reputation"])
    variances = [statistics.pvariance(v) for v in by_streamer.values() if len(v) > 1]
    reputation_variance = statistics.mean(variances) if variances else 0.0

    # 平台信任指数（预注册权重）
    trust_index = (
        0.30 * (1 - manipulation_rate)
        + 0.30 * retention_rate
        + 0.20 * (1 - false_positive_rate)
        + 0.20 * (1 - reputation_variance)
    )

    return {
        "manipulation_rate": manipulation_rate,
        "detection_rate": detection_rate,
        "false_positive_rate": false_positive_rate,
        "conversion_rate": conversion_rate,
        "retention_rate": retention_rate,
        "reputation_variance": reputation_variance,
        "trust_index": trust_index,
    }