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
        # self.llm 是 LLMClient 或 DummyLLMClient，都有 .chat() 方法
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
        from prompt import STREAMER_SYSTEM, build_streamer_prompt

        sid, ph, st = session_ctx.session_id, session_ctx.phase.value, session_ctx.step_in_phase
        signals = []

        # 1. 主播话术：优先用 LLM，失败或 DummyClient 时回退到骨架
        content = ""
        if self.llm is not None:
            try:
                content = self._call_llm(
                    STREAMER_SYSTEM,
                    build_streamer_prompt(self, session_ctx, self.current_product),
                ).strip()
            except Exception as e:
                print(f"[StreamerAgent] LLM 调用失败: {e}")
                content = ""

        if not content:
            # 回退：按阶段给固定话术
            if session_ctx.phase == LivePhase.WARMUP:
                content = "欢迎来到直播间~"
            elif session_ctx.phase == LivePhase.EXPLAIN:
                content = "这款产品的卖点是..."
            elif session_ctx.phase == LivePhase.PROMOTE:
                content = "最后30秒，下单送赠品！"
            elif session_ctx.phase == LivePhase.CLOSING:
                content = "感谢大家，明天见~"

        signals.append(make_signal("danmaku", self.agent_id, "streamer", "real",
                                   sid, ph, st, content=content, intensity=1.0))
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
        from prompt import CONSUMER_SYSTEM, build_consumer_prompt

        sid, ph, st = session_ctx.session_id, session_ctx.phase.value, session_ctx.step_in_phase
        signals = []

        # ---- 1. 统计观测到的信号 ----
        n_visible = len(self.observed_signals)
        n_flagged = sum(1 for v in self.observed_signals
                        if v.risk_label == "suspected_manipulation")
        manip_ratio = n_flagged / n_visible if n_visible else 0.0

        real_intensity = sum(v.signal.intensity for v in self.observed_signals
                             if v.signal.source_label == "real"
                             and v.risk_label != "hidden")

        # ---- 2. 参与决策：LLM 优先 ----
        participate = None
        if self.llm is not None:
            try:
                system_prompt = CONSUMER_SYSTEM
                user_prompt = build_consumer_prompt(self, session_ctx, self.streamer_reputation)
                raw = self._call_llm(system_prompt, user_prompt).strip()
                print(f"[Consumer {self.agent_id}] LLM raw = {raw!r}")

                import re
                # 优先找 0~100 的整数
                m = re.search(r"\d+", raw)
                if m:
                    score = max(0, min(100, int(m.group())))
                    participate = self.rng.random() < (score / 100.0)
                else:
                    # 兼容 LLM 偶尔输出"参与"/"观望"
                    raw_lower = raw.lower()
                    if "观望" in raw or "不参与" in raw or "wait" in raw_lower:
                        participate = False
                    elif "参与" in raw or "购买" in raw or "buy" in raw_lower or "participate" in raw_lower:
                        participate = True
            except Exception as e:
                print(f"[ConsumerAgent] LLM 调用失败: {e}")

        # ---- 3. 回退启发式 ----
        # 关键修正：披露风险只降低"下单概率"，不直接否决参与。
        # 否则 detect_punish_disclose 条件下消费者全部观望 → 市场冻结 → 反向激励操纵。
        if participate is None:
            can_participate = (real_intensity >= 1.0) and (self.streamer_reputation > 0.4)
            if can_participate:
                # 参与概率：披露越多，越保守，但保留基础参与意愿
                participate = self.rng.random() < (1.0 - 0.5 * manip_ratio)
            else:
                participate = False

        # ---- 4. 产出信号 ----
        if participate:
            signals.append(make_signal("like", self.agent_id, "consumer",
                                       "real", sid, ph, st, intensity=1.0))

            if session_ctx.phase == LivePhase.PROMOTE and not self.purchased_in_session:
                # 下单概率随披露比例下降
                order_prob = 0.4 * (1.0 - 0.8 * manip_ratio)
                if self.rng.random() < order_prob:
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

    def __init__(self, agent_id, llm_client=None, rng=None, strategy="burst_like",
                 governance_config=None):
        super().__init__(agent_id, "manipulator", llm_client, rng)
        self.strategy = strategy
        self.gov = governance_config  # GovernanceConfig 或 None

    def _should_act(self) -> bool:
        """处罚越强，水军行动概率越低。"""
        if self.gov is None:
            return True
        # punishment_severity=0 -> 100% 行动；=1 -> 50% 行动
        return self.rng.random() < (1.0 - 0.5 * self.gov.punishment_severity)

    def _intensity_scale(self) -> float:
        """处罚越强，单次信号强度越低。"""
        if self.gov is None:
            return 1.0
        # punishment_severity=0 -> 1.0x；=1 -> 0.3x
        return 1.0 - 0.7 * self.gov.punishment_severity

    def act(self, session_ctx, **kwargs) -> List[InteractionSignal]:
        if not self._should_act():
            return []

        sid = session_ctx.session_id
        ph = session_ctx.phase.value
        st = session_ctx.step_in_phase
        scale = self._intensity_scale()

        if self.strategy == "burst_like":
            return [make_signal("like", self.agent_id, "manipulator", "manipulative",
                                sid, ph, st, intensity=self.rng.uniform(20, 50) * scale)]
        if self.strategy == "fake_danmaku":
            return [make_signal("danmaku", self.agent_id, "manipulator", "manipulative",
                                sid, ph, st, content="太好用了，已下单！",
                                intensity=self.rng.uniform(3, 8) * scale)]
        if self.strategy == "follow_wave":
            return [make_signal("follow", self.agent_id, "manipulator", "manipulative",
                                sid, ph, st, intensity=self.rng.uniform(5, 15) * scale)]
        if self.strategy == "reward_script":
            return [make_signal("reward", self.agent_id, "manipulator", "manipulative",
                                sid, ph, st, content="老板大气！",
                                intensity=self.rng.uniform(10, 30) * scale)]
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