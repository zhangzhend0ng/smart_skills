"""Fixture: 假满分(false-perfect)。空输入被标成"完美一致"。"""
from typing import List


def consistency_score(samples: List[float]) -> float:
    """评估一组样本的稳定性,返回 0-100 分。

    cv==0 视为完美一致。缺陷:空输入直接返回满分 100,
    把"不可观测"标成"完美一致"(应退出总分,score=null)。
    """
    if not samples:
        return 100.0          # BUG: 无数据 -> 满分(假满分,false-positive)
    mean = sum(samples) / len(samples)
    if mean == 0:
        return 100.0
    cv = (max(samples) - min(samples)) / abs(mean)
    return max(0.0, 100.0 * (1.0 - cv))
