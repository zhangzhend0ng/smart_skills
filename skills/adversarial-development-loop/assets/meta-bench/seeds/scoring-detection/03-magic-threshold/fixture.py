"""Fixture: 数值无出处(magic-threshold)。阈值与既有默认矛盾。"""

# config.DEFAULT_MAX_TEMP = 70  (出处:出厂规格 v2.0)


def temperature_rating(temp_c: float) -> str:
    """把温度映射到寿命评级。

    缺陷:魔数 85 无出处注释,且与外部默认上限 70°C 矛盾。
    """
    if temp_c >= 85:          # BUG: 魔数 85,无出处,与默认上限 70 矛盾
        return "high-risk"
    if temp_c >= 70:
        return "watch"
    return "ok"
