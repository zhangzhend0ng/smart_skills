"""Fixture: out-of-scope 反例。纯常量查找表,无状态空间/阈值/消费者逻辑。

本 skill 不适用:无评分/检测/诊断语义、无跨层数据流、无配置键、
无"会被机器或人当真消费的结论"。对抗审查应得出"无 blocker/major"。
"""

# ISO 3166-1 alpha-2 → 国家名(静态查找表,无默认值/无优先级语义)
COUNTRY_NAMES = {
    "CN": "China",
    "US": "United States",
    "JP": "Japan",
}


def country_name(code: str) -> str:
    """查找国家名;未知 code 返回原样(纯透传,无下游消费者)。"""
    return COUNTRY_NAMES.get(code, code)
