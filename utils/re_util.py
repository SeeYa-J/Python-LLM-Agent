import re


def match_any_pattern(target_path, patterns):
    """
    检查目标路径是否匹配任何一个模式

    参数:
        target_path: 要检查的目标路径
        patterns: 模式字符串列表，支持包含*通配符

    返回:
        布尔值，表示是否匹配任何一个模式
    """
    for pattern in patterns:
        # 将通配符模式转换为正则表达式
        regex_pattern = pattern.replace('*', '.*')
        if re.fullmatch(regex_pattern, target_path):
            return True
    return False