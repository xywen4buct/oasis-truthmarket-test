# oasis_market/governance.py
"""平台治理规则引擎（非 LLM 驱动）。

三个可调维度：
  - detection_tpr / detection_fpr：检测能力（真阳性率 / 假阳性率）
  - punishment_severity：处罚强度（流量削减/屏蔽概率）
  - disclosure_level：信息披露强度（风险标签公示概率）

治理条件：
  none / detect_only / detect_and_punish / detect_punish_disclose
"""
from dataclasses import dataclass
from typing import List, Tuple
import random

from oasis_market.signals import InteractionSignal, VisibleSignal


GOVERNANCE_TYPES = ["none", "detect_only", "detect_and_punish", "detect_punish_disclose"]


@dataclass
class GovernanceConfig:
    governance_type: str = "detect_punish_disclose"
    detection_tpr: float = 0.8
    detection_fpr: float = 0.05
    punishment_severity: float = 0.5
    disclosure_level: float = 0.0

    def __post_init__(self):
        assert self.governance_type in GOVERNANCE_TYPES, \
            f"unknown governance_type {self.governance_type}"
        assert 0.0 <= self.detection_tpr <= 1.0
        assert 0.0 <= self.detection_fpr <= 1.0
        assert 0.0 <= self.punishment_severity <= 1.0
        assert 0.0 <= self.disclosure_level <= 1.0


@dataclass
class GovernanceEvent:
    signal_id: str
    session_id: str
    action: str                 # none / detected / punished / disclosed
    detection_result: str       # tp / fp / fn / tn
    punishment_applied: float = 0.0
    disclosed: int = 0


class PlatformGovernance:
    """平台治理规则引擎，不做 LLM 决策。"""

    def __init__(self, config: GovernanceConfig, rng: random.Random = None):
        self.cfg = config
        self.rng = rng or random.Random(42)

    def process(self, signals: List[InteractionSignal]
                ) -> Tuple[List[VisibleSignal], List[GovernanceEvent]]:
        visible, events = [], []
        for s in signals:
            is_manip = (s.source_label == "manipulative")

            if is_manip:
                detected = self.rng.random() < self.cfg.detection_tpr
                result = "tp" if detected else "fn"
            else:
                detected = self.rng.random() < self.cfg.detection_fpr
                result = "fp" if detected else "tn"

            action = "none"
            punished = 0.0
            disclosed = 0
            risk_label = None

            if detected:
                action = "detected"
                if self.cfg.governance_type in ("detect_and_punish", "detect_punish_disclose"):
                    punished = self.cfg.punishment_severity
                    action = "punished"
                if self.cfg.governance_type == "detect_punish_disclose":
                    if self.rng.random() < self.cfg.disclosure_level:
                        disclosed = 1
                        risk_label = "suspected_manipulation"
                        action = "disclosed"

            if punished >= 0.7:
                vs = VisibleSignal(signal=s, risk_label="hidden", was_punished=True)
            else:
                vs = VisibleSignal(signal=s, risk_label=risk_label, was_punished=punished > 0)
            visible.append(vs)

            events.append(GovernanceEvent(
                signal_id=s.signal_id,
                session_id=s.session_id,
                action=action,
                detection_result=result,
                punishment_applied=punished,
                disclosed=disclosed,
            ))
        return visible, events