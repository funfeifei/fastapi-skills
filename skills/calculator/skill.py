import re
from pathlib import Path
from skills.base import BaseSkill, SkillContext, SkillResult


class CalculatorSkill(BaseSkill):
    """计算器 Skill - 自定义 Python 实现"""

    async def execute(self, context: SkillContext) -> SkillResult:
        """执行数学计算"""
        try:
            # 获取用户消息
            user_message = context.user_message.strip()

            # 提取数学表达式
            expression = self._extract_expression(user_message)

            if not expression:
                return SkillResult(
                    success=False,
                    content="",
                    error="无法从消息中提取数学表达式"
                )

            # 验证表达式只包含合法字符
            if not self._is_valid_expression(expression):
                return SkillResult(
                    success=False,
                    content="",
                    error=f"表达式包含非法字符: {expression}"
                )

            # 计算结果
            try:
                # 限制内置函数，只允许数学相关函数
                allowed_names = {
                    '__builtins__': {
                        'abs': abs,
                        'round': round,
                        'min': min,
                        'max': max,
                        'pow': pow,
                        'sum': sum,
                    }
                }

                result = eval(expression, allowed_names)
            except Exception as e:
                return SkillResult(
                    success=False,
                    content="",
                    error=f"计算错误: {str(e)}"
                )

            # 格式化结果
            if isinstance(result, float):
                # 如果是浮点数，保留最多6位小数
                if result.is_integer():
                    result_str = str(int(result))
                else:
                    result_str = f"{result:.6f}".rstrip('0').rstrip('.')
            else:
                result_str = str(result)

            return SkillResult(
                success=True,
                content=f"{expression} = {result_str}",
                metadata={
                    "skill_name": "calculator",
                    "expression": expression,
                    "result": result_str
                }
            )

        except Exception as e:
            return SkillResult(
                success=False,
                content="",
                error=str(e)
            )

    def _extract_expression(self, text: str) -> str:
        """从文本中提取数学表达式"""
        # 常见模式：提取数字、运算符、括号
        pattern = r'[\d+\-*/^().%]+\s*[\d+\-*/^().%\s]*[\d+\-*/^().%]+'
        match = re.search(pattern, text)

        if match:
            expr = match.group(0)
            # 替换中文标点和空格
            expr = expr.replace('？', '').replace('＝', '=').replace('乘', '*').replace('除', '/')
            expr = expr.replace('^', '**')  # Python 用 ** 表示幂
            expr = expr.replace('%', '/100')  # 百分号转小数
            return expr.strip()

        # 如果没找到，尝试更简单的模式
        # 查找类似 "2 + 3" 的模式
        simple_pattern = r'[-+]?\d*\.?\d+\s*[\+\-\*/]\s*[-+]?\d*\.?\d+'
        match = re.search(simple_pattern, text)
        if match:
            return match.group(0)

        return ""

    def _is_valid_expression(self, expr: str) -> bool:
        """验证表达式只包含合法字符"""
        # 只允许数字、运算符、括号、空格和小数点
        allowed_chars = set('0123456789+-*/(). %')
        return all(c in allowed_chars for c in expr)
