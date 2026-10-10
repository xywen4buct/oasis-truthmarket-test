# example/run_live_commerce.py
"""多治理条件对照实验入口。

用法：
    python example/run_live_commerce.py                    # 用 DummyLLM，离线跑通
    python example/run_live_commerce.py --use-llm           # 用真实 LLM
    python example/run_live_commerce.py --reps 3            # 每条件重复 3 次
"""
import os
import sys
import json
import csv
import random
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from oasis_market.phases import iter_phases, SessionContext
from oasis_market.governance import GovernanceConfig, PlatformGovernance
from oasis_market.agents import (StreamerAgent, ConsumerAgent, ManipulatorAgent,
                                  Product)
from oasis_market.metrics import compute_metrics
from oasis_market.llm_client import LLMClient, DummyLLMClient


GOVERNANCE_CONDITIONS = [
    {"name": "none", "governance_type": "none",
     "detection_tpr": 0.0, "detection_fpr": 0.0,
     "punishment_severity": 0.0, "disclosure_level": 0.0},
    {"name": "detect_only", "governance_type": "detect_only",
     "detection_tpr": 0.8, "detection_fpr": 0.05,
     "punishment_severity": 0.0, "disclosure_level": 0.0},
    {"name": "detect_and_punish", "governance_type": "detect_and_punish",
     "detection_tpr": 0.8, "detection_fpr": 0.05,
     "punishment_severity": 0.6, "disclosure_level": 0.0},
    {"name": "detect_punish_disclose", "governance_type": "detect_punish_disclose",
     "detection_tpr": 0.8, "detection_fpr": 0.05,
     "punishment_severity": 0.6, "disclosure_level": 1.0},
    {"name": "detect_punish_disclose_high_fpr", "governance_type": "detect_punish_disclose",
     "detection_tpr": 0.8, "detection_fpr": 0.20,
     "punishment_severity": 0.6, "disclosure_level": 1.0},
    {"name": "high_strict", "governance_type": "detect_punish_disclose",
     "detection_tpr": 0.95, "detection_fpr": 0.01,
     "punishment_severity": 0.8, "disclosure_level": 1.0},
]


def run_one(condition: dict, seed: int,
            num_streamers=2, num_consumers=10, num_manipulators=3,
            num_sessions=5, steps_per_phase=3,
            use_llm=False) -> dict:
    rng = random.Random(seed)
    llm = LLMClient() if use_llm else DummyLLMClient()

    gov_cfg = GovernanceConfig(
        governance_type=condition["governance_type"],
        detection_tpr=condition["detection_tpr"],
        detection_fpr=condition["detection_fpr"],
        punishment_severity=condition["punishment_severity"],
        disclosure_level=condition["disclosure_level"],
    )
    gov = PlatformGovernance(gov_cfg, rng=rng)

    products = [Product(f"p{i}", 0.7, 0.8, 99.0) for i in range(5)]
    streamers = [StreamerAgent(f"s{i}", llm_client=llm, rng=rng,
                                product_pool=products)
                 for i in range(num_streamers)]
    consumers = [ConsumerAgent(f"c{i}", llm_client=llm, rng=rng)
                 for i in range(num_consumers)]
    manipulators = [ManipulatorAgent(f"m{i}", llm_client=None, rng=rng,
                                      strategy=rng.choice(ManipulatorAgent.STRATEGIES),
                                      governance_config=gov_cfg)
                    for i in range(num_manipulators)]

    all_signals, all_events, all_orders, rep_traj = [], [], [], []

    for s_idx in range(num_sessions):
        streamer = streamers[s_idx % len(streamers)]
        streamer.pick_product()
        for c in consumers:
            c.purchased_in_session = False

        session_id = f"sess_{s_idx}_seed{seed}"
        for phase in iter_phases():
            ctx = SessionContext(session_id, streamer.agent_id, s_idx,
                                 phase, 0, steps_per_phase)
            while not ctx.is_phase_done:
                raw = []
                raw += streamer.act(ctx)
                for m in manipulators:
                    raw += m.act(ctx)
                for c in consumers:
                    raw += c.act(ctx, current_product=streamer.current_product)

                visible, events = gov.process(raw)
                for c in consumers:
                    c.observe(visible, streamer_reputation=streamer.reputation)

                all_signals += [s.to_dict() for s in raw]
                all_events += [e.__dict__ for e in events]
                for s in raw:
                    if s.signal_type == "order":
                        all_orders.append({
                            "consumer_id": s.source_agent_id,
                            "session_id": session_id,
                            "product_id": getattr(streamer.current_product, "product_id", "p0"),
                        })
                ctx.advance()

        rep_traj.append({"streamer_id": streamer.agent_id,
                         "session_index": s_idx,
                         "reputation": streamer.reputation})

    return compute_metrics(all_signals, all_events, all_orders, rep_traj,
                           num_consumers, num_sessions)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--use-llm", action="store_true",
                        help="用真实 LLM（默认用 DummyLLM 离线跑）")
    parser.add_argument("--reps", type=int, default=3,
                        help="每个治理条件重复次数")
    parser.add_argument("--sessions", type=int, default=5)
    parser.add_argument("--consumers", type=int, default=10)
    parser.add_argument("--out", type=str, default="results/governance_experiment.csv")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    rows = []
    for cond in GOVERNANCE_CONDITIONS:
        print(f"\n=== Condition: {cond['name']} ===")
        for rep in range(args.reps):
            seed = 1000 + rep
            m = run_one(cond, seed, use_llm=args.use_llm,
                        num_consumers=args.consumers, num_sessions=args.sessions)
            m["condition"] = cond["name"]
            m["rep"] = rep
            m["seed"] = seed
            rows.append(m)
            print(f"  rep {rep}: " + "  ".join(f"{k}={v:.4f}" for k, v in m.items()
                                                if isinstance(v, float)))

    # 汇总
    print("\n=== Summary ===")
    import statistics
    for cond in GOVERNANCE_CONDITIONS:
        crows = [r for r in rows if r["condition"] == cond["name"]]
        print(f"\n{cond['name']}:")
        for key in ["manipulation_rate", "detection_rate", "false_positive_rate",
                    "conversion_rate", "retention_rate",
                    "reputation_variance", "trust_index"]:
            vals = [r[key] for r in crows]
            print(f"  {key}: mean={statistics.mean(vals):.4f}  sd={statistics.stdev(vals) if len(vals) > 1 else 0:.4f}")

    # 落 CSV
    fieldnames = ["condition", "rep", "seed",
                  "manipulation_rate", "detection_rate", "false_positive_rate",
                  "conversion_rate", "retention_rate",
                  "reputation_variance", "trust_index"]
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k) for k in fieldnames})
    print(f"\nResults saved to {args.out}")


if __name__ == "__main__":
    main()