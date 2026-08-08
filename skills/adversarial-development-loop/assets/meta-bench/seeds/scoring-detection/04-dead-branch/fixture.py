"""Fixture: 死代码(dead-branch)。防御分支在真实路径不可达。"""


def finalize_report(score: float) -> str:
    """生成报告文本。score 已在上游 clamp 到 [0, 100]。"""
    clamped = max(0.0, min(100.0, score))
    if clamped < 0:           # BUG: 死代码——clamped 永远 >= 0,此分支不可达
        return "invalid"
    if clamped >= 60:         # 及格线 60:验收标准 v1.0(见 docs/spec.md §3.2)
        return "PASS"
    return "FAIL"
