# oasis_market/agents.py
"""7 类角色 + 商品对象。

角色：streamer / operator / mcn / merchant / consumer / manipulator / platform
商品：作为 merchant 持有的对象，参与交易决策。
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import random

from oasis_market.signals import InteractionSignal, VisibleSignal, make_signal
from oasis_market.phases import LivePhase


# ------------------------------------------------------------------
# 商品对象
# ------------------------------------------------------------------
@dataclass
class Product:
    product_id: str
    true_quality: float          # 真实质量 0~1
    described_quality: float     # 宣传质量 0~1
    price: float
    category: str = "general"
    has_warrant: bool = False


# ------------------------------------------------------------------
# 基类
# ------------------------------------------------------------------
class BaseAgent:
    def __init__(self, agent_id: str, role: str,
                 llm_client=None, rng: random.Random = None):
        self.agent_id = agent_id
        self.role = role
        self.llm = llm_client
        self.rng = rng or random.Random(hash(agent_id) % (2**32))
        self.observed_signals: List[VisibleSignal] = []
        self.true_identity = role

    def observe(self, visible_signals: List[VisibleSignal], **ctx) -> None:
        self.observed_signals = visible_signals

    def act(self, session_ctx, **kwargs) -> List[InteractionSignal]:
        raise NotImplementedError

    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        if self.llm is None:
            return ""
        # TODO: 接入 OASIS/CAMEL LLM 客户端（见"接入点 1"）
        return self.llm.chat(system_prompt=system_prompt, user_prompt=user_prompt)


# ------------------------------------------------------------------
# 主播
# ------------------------------------------------------------------
class StreamerAgent(BaseAgent):
    def __init__(self, agent_id, llm_client=None, rng=None,
                 product_pool: Optional[List[Product]] = None):
        super().__init__(agent_id, "streamer", llm_client, rng)
        self.reputation = 0.5
        self.followers = 0
        self.product_pool = product_pool or []
        self.current_product: Optional[Product] = None

    def pick_product(self) -> Optional[Product]:
        if self.product_pool:
            self.current_product = self.rng.choice(self.product_pool)
        return self.current_product

    def act(self, session_ctx, **kwargs) -> List[InteractionSignal]:
        # 骨架：按阶段产出主播侧信号
        # TODO: 接入 prompt.py 的 STREAMER_SYSTEM，用 LLM 生成话术
        sid = session_ctx.session_id
        ph = session_ctx.phase.value
        st = session_ctx.step_in_phase
        signals = []

        if session_ctx.phase == LivePhase.WARMUP:
            signals.append(make_signal("danmaku", self.agent_id, "streamer",
                                       "real", sid, ph, st,
                                       content="欢迎来到直播间~", intensity=1.0))
        elif session_ctx.phase == LivePhase.EXPLAIN:
            signals.append(make_signal("danmaku", self.agent_id, "streamer",
                                       "real", sid, ph, st,
                                       content="这款产品的卖点是...", intensity=1.0))
        elif session_ctx.phase == LivePhase.PROMOTE:
            signals.append(make_signal("danmaku", self.agent_id, "streamer",
                                       "real", sid, ph, st,
                                       content="最后30秒，下单送赠品！", intensity=1.0))
        elif session_ctx.phase == LivePhase.CLOSING:
            signals.append(make_signal("danmaku", self.agent_id, "streamer",
                                       "real", sid, ph, st,
                                       content="感谢大家，明天见~", intensity=1.0))
        return signals


# ------------------------------------------------------------------
# 直播间运营者
# ------------------------------------------------------------------
class OperatorAgent(BaseAgent):
    def __init__(self, agent_id, llm_client=None, rng=None):
        super().__init__(agent_id, "operator", llm_client, rng)

    def act(self, session_ctx, **kwargs) -> List[InteractionSignal]:
        # TODO: 运营侧引导话术、控评、节奏控制
        return []


# ------------------------------------------------------------------
# MCN
# ------------------------------------------------------------------
class MCNAgent(BaseAgent):
    def __init__(self, agent_id, llm_client=None, rng=None):
        super().__init__(agent_id, "mcn", llm_client, rng)

    def act(self, session_ctx, **kwargs) -> List[InteractionSignal]:
        # TODO: 调度水军、分配流量资源
        return []


# ------------------------------------------------------------------
# 商家
# ------------------------------------------------------------------
class MerchantAgent(BaseAgent):
    def __init__(self, agent_id, llm_client=None, rng=None,
                 products: Optional[List[Product]] = None):
        super().__init__(agent_id, "merchant", llm_client, rng)
        self.products = products or []

    def act(self, session_ctx, **kwargs) -> List[InteractionSignal]:
        # TODO: 投放/价格/是否要求操纵
        return []


# ------------------------------------------------------------------
# 消费者
# ------------------------------------------------------------------
class ConsumerAgent(BaseAgent):
    def __init__(self, agent_id, llm_client=None, rng=None):
        super().__init__(agent_id, "consumer", llm_client, rng)
        self.trust = 0.5
        self.cumulative_utility = 0.0
        self.purchased_in_session = False
        self.streamer_reputation = 0.5

    def observe(self, visible_signals, streamer_reputation=0.5, **ctx) -> None:
        super().observe(visible_signals, **ctx)
        self.streamer_reputation = streamer_reputation

    def act(self, session_ctx, current_product=None, **kwargs) -> List[InteractionSignal]:
        # 骨架：简单启发式，后续用 LLM 替代
        n_visible = len(self.observed_signals)
        n_flagged = sum(1 for v in self.observed_signals
                        if v.risk_label == "suspected_manipulation")
        manip_ratio = n_flagged / n_visible if n_visible else 0.0

        real_intensity = sum(v.signal.intensity for v in self.observed_signals
                             if v.signal.source_label == "real" and v.risk_label != "hidden")
        participate = (real_intensity >= 1.0) and (manip_ratio < 0.5) \
                      and (self.streamer_reputation > 0.4)

        sid = session_ctx.session_id
        ph = session_ctx.phase.value
        st = session_ctx.step_in_phase
        signals: List[InteractionSignal] = []

        if participate:
            signals.append(make_signal("like", self.agent_id, "consumer",
                                       "real", sid, ph, st, intensity=1.0))
            if session_ctx.phase == LivePhase.PROMOTE and not self.purchased_in_session:
                if self.rng.random() < 0.4:
                    price = current_product.price if current_product else 1.0
                    signals.append(make_signal("order", self.agent_id, "consumer",
                                               "real", sid, ph, st, intensity=price))
                    self.purchased_in_session = True
        else:
            if self.rng.random() < 0.1:
                signals.append(make_signal("follow", self.agent_id, "consumer",
                                           "real", sid, ph, st, intensity=-1.0))
        return signals


# ------------------------------------------------------------------
# 互动操纵智能体（水军/虚假账号）
# ------------------------------------------------------------------
class ManipulatorAgent(BaseAgent):
    STRATEGIES = ["burst_like", "fake_danmaku", "follow_wave", "reward_script"]

    def __init__(self, agent_id, llm_client=None, rng=None, strategy="burst_like"):
        super().__init__(agent_id, "manipulator", llm_client, rng)
        self.strategy = strategy

    def act(self, session_ctx, **kwargs) -> List[InteractionSignal]:
        sid = session_ctx.session_id
        ph = session_ctx.phase.value
        st = session_ctx.step_in_phase

        if self.strategy == "burst_like":
            return [make_signal("like", self.agent_id, "manipulator", "manipulative",
                                sid, ph, st, intensity=self.rng.uniform(20, 50))]
        if self.strategy == "fake_danmaku":
            return [make_signal("danmaku", self.agent_id, "manipulator", "manipulative",
                                sid, ph, st, content="太好用了，已下单！",
                                intensity=self.rng.uniform(3, 8))]
        if self.strategy == "follow_wave":
            return [make_signal("follow", self.agent_id, "manipulator", "manipulative",
                                sid, ph, st, intensity=self.rng.uniform(5, 15))]
        if self.strategy == "reward_script":
            return [make_signal("reward", self.agent_id, "manipulator", "manipulative",
                                sid, ph, st, content="老板大气！",
                                intensity=self.rng.uniform(10, 30))]
        return []


# ------------------------------------------------------------------
# 平台（规则驱动，不做 LLM 决策）
# ------------------------------------------------------------------
class PlatformAgent(BaseAgent):
    def __init__(self, agent_id, governance, rng=None):
        super().__init__(agent_id, "platform", llm_client=None, rng=rng)
        self.governance = governance  # PlatformGovernance 实例

    def act(self, session_ctx, **kwargs):
        raise NotImplementedError(
            "平台不通过 act() 行动，由 PlatformGovernance.process() 处理信号"
        )

    def process(self, signals):
        return self.governance.process(signals)