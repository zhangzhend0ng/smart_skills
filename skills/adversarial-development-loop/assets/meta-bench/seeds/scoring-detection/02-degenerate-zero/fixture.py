"""Fixture: 假最差(false-worst)。检测工具对空数据返回 0。"""
from typing import List


def defect_density(records: List[dict]) -> float:
    """检测工具:返回缺陷密度 0-1。

    缺陷:空数据返回 0.0,会被下游当成"零缺陷"钉到地板
    (false-negative,对检测工具比误报更危险)。应退出总分。
    """
    if not records:
        return 0.0            # BUG: 无数据 -> 0(假最差,false-negative)
    defects = sum(1 for r in records if r.get("defect"))
    return defects / len(records)
