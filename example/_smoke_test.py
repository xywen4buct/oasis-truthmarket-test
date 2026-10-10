# example/_smoke_test.py
import os, sys, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from oasis_market.phases import iter_phases, SessionContext, LivePhase
from oasis_market.governance import GovernanceConfig, PlatformGovernance
from oasis_market.agents import (StreamerAgent, ConsumerAgent,
                                  ManipulatorAgent, Product)
from oasis_market.metrics import compute_metrics

def main():
    rng = random.Random(42)
    gov = PlatformGovernance(GovernanceConfig(governance_type="detect_punish_disclose",
                                              detection_tpr=0.8,
                                              detection_fpr=0.05,
                                              punishment_severity=0.5,
                                              disclosure_level=1.0),
                             rng=rng)
    streamer = StreamerAgent("s0", rng=rng,
                             product_pool=[Product("p0", 0.8, 0.9, 99.0)])
    consumers = [ConsumerAgent(f"c{i}", rng=rng) for i in range(3)]
    manipulators = [ManipulatorAgent(f"m{i}", rng=rng, strategy="burst_like")
                    for i in range(2)]

    all_signals, all_events, all_orders, rep_traj = [], [], [], []
    streamer.pick_product()

    for s_idx in range(1):
        session_id = f"sess_{s_idx}"
        for phase in iter_phases():
            ctx = SessionContext(session_id, streamer.agent_id, s_idx, phase, 0, 2)
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
                            "product_id": streamer.current_product.product_id,
                        })
                ctx.advance()
        rep_traj.append({"streamer_id": streamer.agent_id,
                         "session_index": s_idx,
                         "reputation": streamer.reputation})

    m = compute_metrics(all_signals, all_events, all_orders, rep_traj,
                        num_consumers=len(consumers), num_sessions=1)
    for k, v in m.items():
        print(f"  {k}: {v:.4f}")

if __name__ == "__main__":
    main()