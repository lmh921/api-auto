from functools import lru_cache
from typing import Any, Dict, List

from jsonpath_ng import parse as jsonpath_parse
from loguru import logger


@lru_cache(maxsize=256)
def _compile_jsonpath(expression: str):
    """编译并缓存JSONPath表达式，避免同一表达式重复解析"""
    return jsonpath_parse(expression)


class Assertion:
    """断言模块"""

    def __init__(self):
        pass

    def get_value_from_jsonpath(self, data: Any, jsonpath: str) -> Any:
        """从JSON数据中获取指定路径的值

        底层使用 jsonpath-ng，`$` 前缀可省略：
        - $.data.token / data.token   普通字段
        - $[0].id / [0].id            数组索引
        - $..token                    递归查找所有层级
        - $[*].id                     通配符
        - $length / length            特殊路径，返回响应体（数组/字典/字符串）的长度

        匹配到单个值返回该值；匹配到多个值返回列表；匹配不到抛出 AssertionError。
        """
        if not jsonpath:
            return data

        # 特殊路径：取长度（列表数量断言的常用场景）
        if jsonpath in ("$length", "length"):
            if isinstance(data, (list, dict, str, tuple)):
                return len(data)
            raise AssertionError(f"$length 仅支持数组/字典/字符串，实际响应体类型: {type(data).__name__}")

        # 兼容无 $ 前缀的写法：data.token -> $.data.token；[0].id -> $[0].id；..email -> $..email
        if jsonpath.startswith('$'):
            expression = jsonpath
        elif jsonpath.startswith(('[', '..')):
            expression = f'${jsonpath}'
        else:
            expression = f'$.{jsonpath}'

        try:
            matches = [match.value for match in _compile_jsonpath(expression).find(data)]
        except Exception as e:
            raise AssertionError(f"JSONPath 表达式无效: {jsonpath}（{e}）")

        if not matches:
            raise AssertionError(f"JSONPath {jsonpath} 在响应中未匹配到任何值")
        if len(matches) == 1:
            return matches[0]
        return matches

    def assert_equal(self, actual: Any, expected: Any, message: str = "") -> None:
        """断言相等"""
        if actual != expected:
            raise AssertionError(f"{message} 断言失败: 实际值 {actual!r} 不等于期望值 {expected!r}")
        logger.info(f"{message} 断言成功: {actual!r} 等于 {expected!r}")

    def assert_not_equal(self, actual: Any, expected: Any, message: str = "") -> None:
        """断言不相等"""
        if actual == expected:
            raise AssertionError(f"{message} 断言失败: 实际值 {actual!r} 等于期望值 {expected!r}")
        logger.info(f"{message} 断言成功: {actual!r} 不等于 {expected!r}")

    def assert_contains(self, actual: Any, expected: Any, message: str = "") -> None:
        """断言包含"""
        # 处理不同类型的包含检查
        if isinstance(actual, str) and isinstance(expected, str):
            if expected not in actual:
                raise AssertionError(f"{message} 断言失败: 字符串 {actual!r} 不包含 {expected!r}")
        elif isinstance(actual, (list, tuple)):
            if expected not in actual:
                raise AssertionError(f"{message} 断言失败: 列表 {actual!r} 不包含 {expected!r}")
        elif isinstance(actual, dict):
            if expected not in actual:
                raise AssertionError(f"{message} 断言失败: 字典 {actual!r} 不包含键 {expected!r}")
        else:
            # 默认比较，转换为字符串
            if str(expected) not in str(actual):
                raise AssertionError(f"{message} 断言失败: {actual!r} 不包含 {expected!r}")
        logger.info(f"{message} 断言成功: {actual!r} 包含 {expected!r}")

    def assert_not_contains(self, actual: Any, expected: Any, message: str = "") -> None:
        """断言不包含"""
        if expected in str(actual):
            raise AssertionError(f"{message} 断言失败: 实际值 {actual!r} 包含期望值 {expected!r}")
        logger.info(f"{message} 断言成功: {actual!r} 不包含 {expected!r}")

    def assert_greater_than(self, actual: Any, expected: Any, message: str = "") -> None:
        """断言大于"""
        if float(actual) <= float(expected):
            raise AssertionError(f"{message} 断言失败: 实际值 {actual} 不大于期望值 {expected}")
        logger.info(f"{message} 断言成功: {actual} 大于 {expected}")

    def assert_less_than(self, actual: Any, expected: Any, message: str = "") -> None:
        """断言小于"""
        if float(actual) >= float(expected):
            raise AssertionError(f"{message} 断言失败: 实际值 {actual} 不小于期望值 {expected}")
        logger.info(f"{message} 断言成功: {actual} 小于 {expected}")

    def assert_greater_or_equal(self, actual: Any, expected: Any, message: str = "") -> None:
        """断言大于等于"""
        if float(actual) < float(expected):
            raise AssertionError(f"{message} 断言失败: 实际值 {actual} 小于期望值 {expected}")
        logger.info(f"{message} 断言成功: {actual} 大于等于 {expected}")

    def assert_less_or_equal(self, actual: Any, expected: Any, message: str = "") -> None:
        """断言小于等于"""
        if float(actual) > float(expected):
            raise AssertionError(f"{message} 断言失败: 实际值 {actual} 大于期望值 {expected}")
        logger.info(f"{message} 断言成功: {actual} 小于等于 {expected}")

    def assert_status_code(self, actual: int, expected: int, message: str = "") -> None:
        """断言状态码"""
        self.assert_equal(actual, expected, f"{message} 状态码")

    def run_assertions(self, response: Dict[str, Any], assertions: List[Dict[str, Any]]) -> None:
        """运行多个断言（软断言）

        同一用例的所有断言都会执行，不会因第一条失败而中断；
        全部执行完后一次性汇总所有失败项，便于一次定位多个问题。
        """
        if not assertions:
            logger.warning("用例未配置任何断言，请检查用例完整性")
            return

        failures: List[str] = []
        for index, assertion in enumerate(assertions, 1):
            assert_type = assertion.get('type', 'equal')
            expected = assertion.get('expected')
            jsonpath = assertion.get('jsonpath')
            message = assertion.get('message', f'第{index}条断言')

            try:
                # 获取实际值
                if jsonpath:
                    actual = self.get_value_from_jsonpath(response['body'], jsonpath)
                else:
                    actual = response['status_code']

                # 执行断言
                assertion_method = getattr(self, f"assert_{assert_type}", None)
                if not assertion_method:
                    raise AssertionError(f"不支持的断言类型: {assert_type}")
                assertion_method(actual, expected, message)
            except AssertionError as e:
                logger.error(f"断言失败: {e}")
                failures.append(str(e))
            except Exception as e:
                logger.error(f"断言执行异常: {message} {type(e).__name__}: {e}")
                failures.append(f"{message} 断言执行异常: {type(e).__name__}: {e}")

        if failures:
            summary = f"共 {len(assertions)} 条断言，失败 {len(failures)} 条:\n" + "\n".join(
                f"  {i}. {item}" for i, item in enumerate(failures, 1)
            )
            raise AssertionError(summary)
        logger.info(f"全部 {len(assertions)} 条断言通过")
