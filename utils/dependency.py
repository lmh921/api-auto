"""用例依赖与条件执行：执行结果注册表、depends_on 判定、run_if 求值

设计说明：
- CASE_RESULTS 为 session 级注册表，key 为用例ID基名（文件相对路径::用例名），
  value 为 "passed" / "failed" / "skipped"，由 test_executor 在用例结束时写入
- depends_on 引用在收集期（case_collector.resolve_and_sort）已改写为规范形式
  "文件相对路径::用例名"，运行期直接查表，不再做名字解析
- 上游 failed / skipped / 未执行（被 -m/-k 圈选过滤等）三种情况都视为依赖不满足，
  下游 pytest.skip 并给出具体原因，避免带着未替换的字面量 "${var}" 产生误导性失败
- 收集期已按依赖图拓扑排序，正常整批执行时读到的一定是上游的最终结果；
  注册表里的"未执行"分支只在上游被圈选过滤时出现
- pytest-xdist 并行与 session 级 global_vars 本就不兼容（既有约束），注册表同样仅支持单进程
"""
from typing import Any, Dict, Optional

from loguru import logger

from utils.masking import mask_data

# 用例执行结果注册表：case_id基名 -> "passed" | "failed" | "skipped"
CASE_RESULTS: Dict[str, str] = {}

# run_if 支持的比较符
RUN_IF_OPS = ("eq", "ne", "gt", "ge", "lt", "le",
              "in", "not_in", "contains", "exists", "not_exists")


def record_result(case_id: str, status: str) -> None:
    """记录用例执行结果（供下游 depends_on 判定）"""
    CASE_RESULTS[case_id] = status
    logger.debug(f"用例结果登记: {case_id} -> {status}")


def check_dependencies(case: Dict[str, Any]) -> Optional[str]:
    """检查 depends_on 上游用例的执行结果

    返回 None 表示依赖满足可继续执行；返回字符串为应 skip 的原因。
    """
    for ref in case.get("depends_on") or []:
        status = CASE_RESULTS.get(ref)
        if status is None:
            return f"依赖的用例 [{ref}] 未执行（可能被 -m/-k 圈选过滤），跳过"
        if status == "failed":
            return f"依赖的用例 [{ref}] 执行失败，跳过"
        if status == "skipped":
            return f"依赖的用例 [{ref}] 被跳过，跳过"
    return None


def evaluate_run_if(run_if: Dict[str, Any], global_vars: Dict[str, Any],
                    yaml_parser) -> Optional[str]:
    """求值条件执行 run_if：{var, op, value}

    返回 None 表示条件满足可继续执行；返回字符串为应 skip 的原因。
    var 取自 global_vars（extract / extract_from_db / setup 提取的变量与预置变量），
    value 支持 ${var} 引用其他变量。
    """
    var_name = run_if.get("var")
    op = str(run_if.get("op", "eq")).lower()
    if op not in RUN_IF_OPS:
        return f"run_if 使用了不支持的比较符: {op}（支持: {', '.join(RUN_IF_OPS)}），跳过"

    actual = global_vars.get(var_name)
    if op == "exists":
        return None if actual is not None else f"条件不满足: 变量 {var_name} 不存在，跳过"
    if op == "not_exists":
        return None if actual is None else f"条件不满足: 变量 {var_name} 已存在，跳过"

    expected = yaml_parser.replace_variables(run_if.get("value"), global_vars)
    satisfied, reason = _compare(actual, op, expected)
    if satisfied:
        return None
    # 实际值可能为token等敏感信息，进报告前脱敏
    masked_actual = mask_data({var_name: actual})[var_name]
    detail = f"（{reason}）" if reason else ""
    return f"条件不满足: 变量 {var_name} = {masked_actual!r} {op} {expected!r} 不成立{detail}，跳过"


def _to_number(value: Any) -> Optional[float]:
    """能转为数值则转；bool 视为非数值，避免 True == 1 的意外匹配"""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def _compare(actual: Any, op: str, expected: Any):
    """按比较符比较，返回 (是否满足, 不满足原因)"""
    if op == "eq":
        return actual == expected, ""
    if op == "ne":
        return actual != expected, ""
    if op in ("gt", "ge", "lt", "le"):
        left, right = _to_number(actual), _to_number(expected)
        if left is None or right is None:
            return False, "两侧需为数值或数值字符串"
        return {"gt": left > right, "ge": left >= right,
                "lt": left < right, "le": left <= right}[op], ""
    if op in ("in", "not_in"):
        if not isinstance(expected, (list, tuple, set)):
            return False, "value 需为列表"
        return (actual in expected) if op == "in" else (actual not in expected), ""
    if op == "contains":
        try:
            return expected in actual, ""
        except TypeError:
            return False, f"实际值类型 {type(actual).__name__} 不支持包含判断"
    return False, f"未知比较符 {op}"
