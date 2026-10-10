# oasis_market/signals.py
"""互动信号体系。

每条信号包含：类型、来源角色、来源标签（真实/操纵/未识别）、强度、内容、时间戳、阶段。
消费者只能看到平台处理后的 VisibleSignal（可能带风险标签或被屏蔽）。
"""
from dataclasses import dataclass, field, asdict
from typing import Optional, List
import time
import uuid


# 信号类型
SIGNAL_TYPES = ["danmaku", "like", "follow", "reward", "order"]

# 来源标签
SOURCE_LABELS = ["real", "manipulative", "undetected"]

# 角色
ROLES = ["streamer", "operator", "mcn", "merchant", "consumer", "manipulator", "platform"]


@dataclass
class InteractionSignal:
    signal_type: str
    source_agent_id: str
    source_role: str
    source_label: str
    session_id: str
    phase: str
    step: int
    content: str = ""
    intensity: float = 1.0
    timestamp: float = field(default_factory=time.time)
    signal_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class VisibleSignal:
    """平台处理后，消费者可见的信号。"""
    signal: InteractionSignal
    risk_label: Optional[str] = None       # None / "suspected_manipulation" / "hidden"
    was_punished: bool = False

    def to_dict(self) -> dict:
        d = self.signal.to_dict()
        d["risk_label"] = self.risk_label
        d["was_punished"] = self.was_punished
        return d


def make_signal(signal_type: str, source_agent_id: str, source_role: str,
                source_label: str, session_id: str, phase: str, step: int,
                content: str = "", intensity: float = 1.0) -> InteractionSignal:
    assert signal_type in SIGNAL_TYPES, f"unknown signal_type {signal_type}"
    assert source_role in ROLES, f"unknown role {source_role}"
    assert source_label in SOURCE_LABELS, f"unknown source_label {source_label}"
    return InteractionSignal(
        signal_type=signal_type,
        source_agent_id=source_agent_id,
        source_role=source_role,
        source_label=source_label,
        session_id=session_id,
        phase=phase,
        step=step,
        content=content,
        intensity=intensity,
    )


def aggregate_signals(signals: List[InteractionSignal]) -> dict:
    """按类型聚合成一个向量，供消费者智能体观测。"""
    vec = {t: 0.0 for t in SIGNAL_TYPES}
    for s in signals:
        vec[s.signal_type] += s.intensity
    return vec