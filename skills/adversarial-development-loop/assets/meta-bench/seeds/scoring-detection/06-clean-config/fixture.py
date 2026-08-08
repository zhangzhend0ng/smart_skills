"""Fixture: 干净反例(无种子缺陷)。配置优先级:用户只能加严。"""
from typing import Optional

DEFAULT_TIMEOUT = 30.0  # 秒;出处:运维手册 §4 默认连接超时


def effective_timeout(user_value: Optional[float]) -> float:
    """用户全局只能加严,不能放松下限:max(user, default)。"""
    if user_value is None:
        return DEFAULT_TIMEOUT
    return max(user_value, DEFAULT_TIMEOUT)
