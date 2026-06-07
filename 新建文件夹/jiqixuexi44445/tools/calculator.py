import re
import math

class Calculator:
    """安全计算数学表达式"""

    @staticmethod
    def evaluate(expression: str) -> float:
        """
        计算数学表达式，支持 + - * / ** 和基本函数
        """
        # 清理表达式
        expr = expression.strip().replace('^', '**')
        # 只允许安全字符
        if not re.match(r'^[\d\s\+\-\*\/\(\)\.\*\*]+$', expr):
            raise ValueError(f"不安全表达式: {expr}")
        # 使用 eval 但限制命名空间
        allowed_names = {
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "pow": pow,
            "math": math
        }
        try:
            result = eval(expr, {"__builtins__": {}}, allowed_names)
            return float(result)
        except Exception as e:
            raise ValueError(f"计算错误: {e}")

    @staticmethod
    def is_safe(expression: str) -> bool:
        return bool(re.match(r'^[\d\s\+\-\*\/\(\)\.\*\*]+$', expression))