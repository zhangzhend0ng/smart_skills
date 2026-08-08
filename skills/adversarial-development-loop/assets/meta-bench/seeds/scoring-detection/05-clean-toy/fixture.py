"""Fixture: 干净反例(无种子缺陷)。toy 判定逻辑。"""


def pass_fail(pct: float, threshold: float = 60.0) -> str:
    """合格判定:pct >= threshold 为 pass。

    出处:及格线 60% 来自验收标准 v1.0(见 docs/spec.md §3.2),允许调用方覆盖。
    """
    return "pass" if pct >= threshold else "fail"
