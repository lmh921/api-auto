import ast
import os
import random
import re
import string
import time
import uuid as _uuid
from typing import Any, Callable, Dict, List, Optional, Tuple

import yaml
from loguru import logger

# ${var} 占位符
VAR_PATTERN = re.compile(r"\$\{([^}]+)\}")
# 内置造数函数语法：${uuid()} / ${rand_str(8)}（函数名 + 括号参数）
FUNC_PATTERN = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*)\((.*)\)$", re.DOTALL)


# ---------------------------------------------------------------------------
# 内置造数函数（随机数据生成）
# 动机：框架原先没有造数器，唯一性只能靠前置接口或DB准备；现在可直接在
# 请求参数/db_setup SQL/断言期望值中内联生成随机数据，DB侧造数不再依赖外部准备。
# ---------------------------------------------------------------------------
def _fn_uuid(args: List[str]) -> str:
    """uuid()：随机UUID4字符串"""
    return str(_uuid.uuid4())


def _fn_timestamp(args: List[str]) -> int:
    """timestamp()：当前毫秒级时间戳（int，13位，整串占位符保留类型）"""
    return int(time.time() * 1000)


def _fn_rand_str(args: List[str]) -> str:
    """rand_str(长度)：字母+数字随机串，缺省长度8"""
    length = int(args[0]) if args else 8
    if not 1 <= length <= 128:
        raise ValueError(f"rand_str 长度需在 1~128 之间，实际: {length}")
    alphabet = string.ascii_letters + string.digits
    return "".join(random.choice(alphabet) for _ in range(length))


def _fn_rand_mobile(args: List[str]) -> str:
    """rand_mobile()：11位随机手机号（1 + [3-9] + 9位数字，不含11/12号段）"""
    return "1" + random.choice("3456789") + "".join(random.choice(string.digits) for _ in range(9))


def _fn_rand_int(args: List[str]) -> int:
    """rand_int(最小值, 最大值)：区间内随机整数（含边界）"""
    if len(args) != 2:
        raise ValueError(f"rand_int 需要两个参数(最小值, 最大值)，实际: {args}")
    low, high = int(args[0]), int(args[1])
    if low > high:
        raise ValueError(f"rand_int 最小值不能大于最大值: ({low}, {high})")
    return random.randint(low, high)


# 内置函数白名单：仅按名单分发并解析字面量参数，不做任何动态代码执行
BUILTIN_FUNCTIONS: Dict[str, Callable[[List[str]], Any]] = {
    "uuid": _fn_uuid,
    "timestamp": _fn_timestamp,
    "rand_str": _fn_rand_str,
    "rand_mobile": _fn_rand_mobile,
    "rand_int": _fn_rand_int,
}


# ---------------------------------------------------------------------------
# 生成值作用域缓存：同一用例（或同一文件setup）内相同表达式返回相同值，
# 保证 db_setup 造数 → db_assertions 校验 → db_teardown 清理 引用同一份数据；
# 跨用例自动重新生成。owner 变化即重置（test_executor/setup_runner 调用）。
# ---------------------------------------------------------------------------
_generated_cache: Dict[str, Any] = {}
_function_scope_owner: str = ""


def set_function_scope(owner: str) -> None:
    """切换生成值作用域：owner 不同则重置缓存（用例执行/文件setup 进入时调用）"""
    global _function_scope_owner
    if owner != _function_scope_owner:
        _function_scope_owner = owner
        _generated_cache.clear()


def clear_function_scope() -> None:
    """清空生成值作用域（用例执行结束调用）"""
    global _function_scope_owner
    _function_scope_owner = ""
    _generated_cache.clear()


def _parse_args(raw_args: str) -> List[Any]:
    """解析函数参数为字面量列表（支持数字/字符串等，不做动态求值）"""
    raw_args = raw_args.strip()
    if not raw_args:
        return []
    return [ast.literal_eval(item.strip()) for item in raw_args.split(",")]


class YamlParser:
    """YAML测试用例解析器"""

    def __init__(self):
        pass

    def load_file(self, file_path: str) -> Dict[str, Any]:
        """加载YAML文件"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"测试用例文件不存在: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def parse_test_cases(self, file_path: str) -> List[Dict[str, Any]]:
        """解析测试用例"""
        data = self.load_file(file_path)
        test_cases = []

        # 增加类型检查和验证
        if isinstance(data, dict):
            if 'name' in data and 'request' in data:
                # 处理单接口用例
                if isinstance(data['request'], dict):
                    test_cases.append(data)
                else:
                    print(f"警告: request字段类型错误: {type(data['request'])}")

            elif 'testcases' in data:
                # 处理多接口用例集
                if isinstance(data['testcases'], list):
                    for case in data['testcases']:
                        if isinstance(case, dict) and 'name' in case and 'request' in case:
                            test_cases.append(case)
                        else:
                            print(f"警告: 跳过无效用例: {case}")
                else:
                    print(f"错误: testcases应该是列表，实际是{type(data['testcases'])}")

        return test_cases

    def replace_variables(self, data: Any, variables: Dict[str, Any]) -> Any:
        """替换变量与内置函数

        规则：
        - 字符串整体就是一个占位符（如 "${user_id}"、"${uuid()}"）时，替换为求值结果，保留类型
          （数字、布尔、字典、列表等不会被转成字符串，用于断言比较不会出现 "1" != 1）
        - 占位符嵌在字符串中间（如 "Bearer ${token}"、"user_${rand_str(6)}"）时，做字符串插值
        - 未定义的变量保留原文，便于排查
        - 内置函数（${uuid()} 等）优先于变量名解析，同一用例内相同表达式结果一致（见模块级缓存）
        """
        if isinstance(data, str):
            return self._replace_in_string(data, variables)
        elif isinstance(data, dict):
            return {k: self.replace_variables(v, variables) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.replace_variables(item, variables) for item in data]
        else:
            return data

    def _replace_in_string(self, text: str, variables: Dict[str, Any]) -> Any:
        """对单个字符串做变量/内置函数替换"""
        # 整串占位符：保留原始类型
        full_match = VAR_PATTERN.fullmatch(text)
        if full_match:
            return self._resolve_placeholder(full_match.group(1), text, variables)

        # 嵌入式占位符：字符串插值
        def _sub(match: "re.Match") -> str:
            return str(self._resolve_placeholder(match.group(1), match.group(0), variables))

        return VAR_PATTERN.sub(_sub, text)

    def _resolve_placeholder(self, key: str, original: str, variables: Dict[str, Any]) -> Any:
        """解析单个占位符：先查变量，再试内置函数，都未命中保留原文"""
        if key in variables:
            return variables[key]

        resolved = self._eval_builtin_function(key, original)
        if resolved is not None:
            return resolved

        logger.debug(f"变量未定义，保留原文: {original}")
        return original

    def _eval_builtin_function(self, key: str, original: str) -> Optional[Any]:
        """求值内置造数函数（${uuid()} 等）

        返回 None 表示不是函数语法（按普通变量处理）；
        函数未知/参数不合法/执行出错时告警并保留原文（沿用"未定义保留原文"哲学，但不静默）。
        """
        match = FUNC_PATTERN.match(key)
        if not match:
            return None

        name, raw_args = match.group(1), match.group(2)
        fn = BUILTIN_FUNCTIONS.get(name)
        if fn is None:
            logger.warning(
                f"未知的内置函数，保留原文: {original}（可用: {', '.join(sorted(BUILTIN_FUNCTIONS))}）")
            return original

        try:
            args = _parse_args(raw_args)
        except (ValueError, SyntaxError):
            logger.warning(f"内置函数参数不合法，保留原文: {original}")
            return original

        # 缓存键用解析后的参数归一化（rand_str( 8 ) 与 rand_str(8) 视为同一表达式）
        cache_key = f"{name}({','.join(repr(a) for a in args)})"
        if cache_key in _generated_cache:
            return _generated_cache[cache_key]

        try:
            value = fn(args)
        except Exception as e:
            logger.warning(f"内置函数执行失败，保留原文: {original}（{e}）")
            return original

        _generated_cache[cache_key] = value
        logger.debug(f"内置函数生成数据: {cache_key} -> {value}")
        return value
