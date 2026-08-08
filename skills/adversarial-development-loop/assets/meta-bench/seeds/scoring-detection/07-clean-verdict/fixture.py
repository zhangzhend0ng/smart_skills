"""Fixture: 干净反例(无种子缺陷)。无数据必须退出总分,不得给中性分。"""
from typing import Optional


def classify(score: Optional[float], has_data: bool) -> dict:
    """结论消费契约:无数据退出总分(score=None),不编造中性分。

    出处:本 skill 诚实性硬原则第 1 条——'无数据'既不是 100 也不是 0。
    """
    if not has_data:
        return {"assessable": False, "score": None}
    # 及格线 60:来自验收标准 v1.0(见 docs/spec.md §3.2)
    return {"assessable": True, "score": score,
            "verdict": "PASS" if score >= 60.0 else "FAIL"}
