# oasis_market/phases.py
"""场次-阶段结构定义。

一场直播 = 预热 -> 讲解 -> 促单 -> 收尾 四阶段。
同一主播跨多场次运行，观察声誉/留存/信任演化。
"""
from enum import Enum
from dataclasses import dataclass


class LivePhase(str, Enum):
    WARMUP = "warmup"      # 预热：建立人设、拉近关系
    EXPLAIN = "explain"    # 讲解：介绍卖点、答疑
    PROMOTE = "promote"    # 促单：制造紧迫感、促销逼单
    CLOSING = "closing"    # 收尾：总结、感谢、预告下场


PHASE_ORDER = [LivePhase.WARMUP, LivePhase.EXPLAIN, LivePhase.PROMOTE, LivePhase.CLOSING]

PHASE_DESCRIPTION = {
    LivePhase.WARMUP: "预热阶段：主播建立人设、拉近关系，互动以打招呼、闲聊为主。",
    LivePhase.EXPLAIN: "讲解阶段：介绍商品卖点、答疑，互动以弹幕问答、点赞为主。",
    LivePhase.PROMOTE: "促单阶段：制造紧迫感、促销逼单，互动以打赏、下单提示、刷屏为主。",
    LivePhase.CLOSING: "收尾阶段：总结、感谢、预告下一场，互动以关注、留存为主。",
}


@dataclass
class SessionContext:
    """单场直播的上下文。"""
    session_id: str
    streamer_id: str
    session_index: int
    phase: LivePhase
    step_in_phase: int
    total_steps_in_phase: int

    def advance(self) -> None:
        self.step_in_phase += 1

    @property
    def is_phase_done(self) -> bool:
        return self.step_in_phase >= self.total_steps_in_phase


def iter_phases():
    """按顺序遍历四阶段。"""
    for p in PHASE_ORDER:
        yield p