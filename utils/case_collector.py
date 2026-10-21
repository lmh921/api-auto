"""用例收集：发现用例文件、校验用例结构、注册文件级setup、生成用例ID

收集在 pytest_generate_tests 阶段完成，每个测试用例对应一个独立的pytest用例。
结构不合法的用例不会被静默丢弃，而是生成一条失败用例并给出具体原因。
depends_on 引用在收集期解析（存在性/唯一性/循环检测）并按依赖图拓扑排序，
执行顺序由依赖关系决定，跨文件依赖不再依赖文件名排序。
"""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import jsonschema
from loguru import logger

from utils.config import PROJECT_ROOT, Config
from utils.dependency import RUN_IF_OPS
from utils.yaml_parser import YamlParser

# 用例文件级 setup 注册表：文件相对路径 -> {"cache": bool, "steps": [...]}
FILE_SETUPS: Dict[str, Dict[str, Any]] = {}

# 单条用例/前置步骤的结构规则
# request 不再强制：纯数据库校验用例（只含 db_setup/db_assertions/extract_from_db）可省略 request
CASE_SCHEMA = {
    "type": "object",
    "required": ["name"],
    "anyOf": [
        {"required": ["request"]},
        {"required": ["db_assertions"]},
        {"required": ["db_setup"]},
        {"required": ["extract_from_db"]},
    ],
    "properties": {
        "name": {"type": "string"},
        "description": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"}},
        "env": {
            "type": "object",
            "properties": {
                "base_url": {"type": "string"},
                "timeout": {"type": "number"},
            },
        },
        "request": {
            "type": "object",
            "required": ["method", "url"],
            "properties": {
                "method": {"type": "string"},
                "url": {"type": "string"},
                "params": {"type": "object"},
                "headers": {"type": "object"},
                "json": {"type": ["object", "array", "string", "number", "boolean", "null"]},
                "body": {"type": ["object", "string"]},
                "files": {"type": "object"},
            },
        },
        "assertions": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["type"],
                "properties": {
                    "type": {"type": "string"},
                    "jsonpath": {"type": "string"},
                    "expected": {},
                    "message": {"type": "string"},
                },
            },
        },
        "extract": {"type": "object", "additionalProperties": {"type": "string"}},
        # ---- 依赖与条件执行 ----
        # 显式依赖：上游用例 failed/skipped/未执行 时本用例自动 skip；
        # 引用为用例名（全局唯一时）或 "用例文件相对路径::用例名"（跨文件/重名时），
        # 收集期解析为规范形式并按依赖图拓扑排序，跨文件依赖不依赖文件名排序
        "depends_on": {"type": "array", "items": {"type": "string"}},
        # 条件执行：global_vars 中的变量满足条件才执行，否则 skip（不满足不是失败）
        "run_if": {
            "type": "object",
            "required": ["var"],
            "properties": {
                "var": {"type": "string"},
                "op": {"type": "string", "enum": list(RUN_IF_OPS)},
                "value": {},
            },
        },
        # ---- 数据库扩展 ----
        "db_setup": {"type": "array", "items": {"type": ["string", "object"]}},
        "db_teardown": {"type": "array", "items": {"type": ["string", "object"]}},
        "db_assertions": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["sql"],
                "properties": {
                    "sql": {"type": "string"},
                    # row_count: 行数 | value: 单值(默认) | contains_row: 查询结果包含
                    "type": {"type": "string"},
                    "op": {"type": "string"},
                    "expected": {},
                    "column": {"type": "string"},
                    "message": {"type": "string"},
                },
            },
        },
        "extract_from_db": {"type": "object", "additionalProperties": {"type": "string"}},
    },
}

# 文件级 setup 结构规则
SETUP_SCHEMA = {
    "type": "object",
    "required": ["steps"],
    "properties": {
        # cache: 跨用例文件缓存setup结果（相同环境+相同setup内容只执行一次）。
        # 注意：业务会改变账号状态（如注销登录）时不要开启，否则后续文件可能拿到失效token
        "cache": {"type": "boolean"},
        "steps": {"type": "array", "items": CASE_SCHEMA},
    },
}


def get_test_case_files(config: Config) -> List[Path]:
    """获取所有yaml测试用例文件（按文件名排序，保证执行顺序稳定）"""
    case_dir = config.case_data_path
    if not case_dir.exists():
        logger.error(f"用例目录不存在: {case_dir}")
        return []
    files = set(case_dir.rglob("*.yaml")) | set(case_dir.rglob("*.yml"))
    return sorted(p for p in files if not p.name.endswith("_template.yaml"))


def _validate_schema(instance: Any, schema: Dict[str, Any]) -> List[str]:
    """校验结构，返回错误列表（空列表表示通过）"""
    try:
        jsonschema.validate(instance, schema)
        return []
    except jsonschema.ValidationError as e:
        location = ".".join(str(p) for p in e.absolute_path) or "(根节点)"
        return [f"结构不合法 [{location}]: {e.message}"]
    except jsonschema.SchemaError as e:
        return [f"校验规则本身有误: {e.message}"]


def collect_all_cases(config: Config) -> List[Tuple[str, Dict[str, Any]]]:
    """收集所有用例，返回 (用例文件相对路径, 用例) 列表，并注册文件级setup"""
    parser = YamlParser()
    FILE_SETUPS.clear()
    entries: List[Tuple[str, Dict[str, Any]]] = []

    for case_file in get_test_case_files(config):
        rel_path = case_file.relative_to(PROJECT_ROOT).as_posix()
        try:
            raw = parser.load_file(str(case_file)) or {}
        except Exception as e:
            logger.error(f"解析用例文件失败: {rel_path}: {e}")
            entries.append((rel_path, {"name": "YAML解析失败", "_collect_error": f"YAML解析失败: {e}"}))
            continue

        if not isinstance(raw, dict):
            entries.append((rel_path, {"name": "YAML结构错误", "_collect_error": "文件顶层应为键值映射"}))
            continue

        # 文件级前置步骤 setup
        if "setup" in raw:
            errors = _validate_schema(raw["setup"], SETUP_SCHEMA)
            # setup 步骤不支持 depends_on/run_if（无跳过语义），显式报错避免静默失效
            for step in (raw["setup"].get("steps") or []):
                if isinstance(step, dict) and ("depends_on" in step or "run_if" in step):
                    errors.append("setup步骤不支持 depends_on/run_if（仅testcases用例可用）")
            if errors:
                entries.append((rel_path, {"name": "setup定义不合法", "_collect_error": "；".join(errors)}))
                continue
            FILE_SETUPS[rel_path] = raw["setup"]

        # 收集用例
        if "testcases" in raw:
            items = raw["testcases"]
            if not isinstance(items, list):
                entries.append((rel_path, {"name": "testcases类型错误",
                                           "_collect_error": f"testcases 应为列表，实际为 {type(items).__name__}"}))
                continue
            for index, case in enumerate(items):
                errors = _validate_schema(case, CASE_SCHEMA)
                if errors:
                    name = case.get("name") if isinstance(case, dict) else None
                    entries.append((rel_path, {"name": name or f"第{index + 1}条用例",
                                               "_collect_error": "；".join(errors)}))
                else:
                    entries.append((rel_path, case))
        elif "request" in raw:
            # 单接口用例：整个文件就是一条用例
            errors = _validate_schema(raw, CASE_SCHEMA)
            if errors:
                entries.append((rel_path, {"name": raw.get("name", "单接口用例"),
                                           "_collect_error": "；".join(errors)}))
            else:
                entries.append((rel_path, raw))
        else:
            logger.warning(f"用例文件中没有可执行的用例，已跳过: {rel_path}")

    return resolve_and_sort(entries)


def _entry_key(rel_path: str, case: Dict[str, Any]) -> str:
    """用例的规范引用形式：文件相对路径::用例名（与结果注册表的key一致）"""
    return f"{rel_path}::{case.get('name', '未命名测试用例')}"


def resolve_and_sort(entries: List[Tuple[str, Dict[str, Any]]]) -> List[Tuple[str, Dict[str, Any]]]:
    """解析 depends_on 引用并按依赖图拓扑排序

    - 引用改写为规范形式 "文件相对路径::用例名"（运行期直接查结果注册表）
    - 引用不存在 / 名称不唯一 / 依赖自身 / 循环依赖：转为收集失败用例
      （沿用 _collect_error 机制，执行时直接 fail 并给出具体原因）
    - 拓扑排序保证生产者先于消费者，跨文件依赖不再依赖文件名排序；
      无依赖关系的用例保持原有（文件名+书写）顺序，执行顺序仍稳定
    """
    n = len(entries)
    keys = [_entry_key(rel_path, case) for rel_path, case in entries]
    names = [case.get("name") for _, case in entries]

    # 第一遍：解析所有 depends_on 引用。引用写错的用例本身转为失败用例，
    # 但保留其原条目参与解析（其他用例指向它仍有效，运行期会因上游失败而 skip）
    resolved: List[Optional[List[str]]] = [None] * n
    errors: Dict[int, str] = {}
    for i, (_, case) in enumerate(entries):
        refs = case.get("depends_on")
        if not refs:
            continue
        canonical, err = [], []
        for ref in refs:
            if "::" in ref:
                matches = [j for j in range(n) if keys[j] == ref]
                if not matches:
                    err.append(f"依赖的用例不存在: {ref}")
                elif len(matches) > 1:
                    err.append(f"依赖的用例名在同一文件中重复，无法唯一指定: {ref}")
                else:
                    canonical.append(ref)
            else:
                matches = [j for j in range(n) if names[j] == ref]
                if not matches:
                    err.append(f"依赖的用例不存在: {ref}（跨文件依赖请用 文件路径::用例名 指定）")
                elif len(matches) > 1:
                    err.append(f"依赖的用例名不唯一: {ref}（请改用 文件路径::用例名 指定）")
                else:
                    canonical.append(keys[matches[0]])
        if keys[i] in canonical:
            err.append(f"用例不能依赖自身: {keys[i]}")
            canonical = [c for c in canonical if c != keys[i]]
        if err:
            errors[i] = "；".join(err)
        else:
            resolved[i] = canonical

    # 规范引用 -> 唯一索引（解析阶段已保证引用唯一，此处直接建表）
    key_index: Dict[str, int] = {}
    for j, key in enumerate(keys):
        key_index.setdefault(key, j)

    # 第二遍：拓扑排序（稳定：每轮取最靠前的依赖已全部就绪的用例，
    # 保持无依赖用例的原有顺序；O(n²) 对测试规模足够）
    dep_indices = [{key_index[c] for c in refs} if refs else set()
                   for refs in resolved]
    placed = [False] * n
    order: List[int] = []
    for _ in range(n):
        for i in range(n):
            if not placed[i] and all(placed[d] for d in dep_indices[i]):
                placed[i] = True
                order.append(i)
                break
        else:
            break  # 剩余用例互相依赖，存在循环
    if len(order) < n:
        cycle_members = [keys[i] for i in range(n) if not placed[i]]
        for i in range(n):
            if not placed[i]:
                errors[i] = f"存在循环依赖，涉及用例: {' <-> '.join(cycle_members)}"
        order.extend(i for i in range(n) if not placed[i])

    # 第三遍：应用解析结果（depends_on 改写为规范引用）与错误（转为收集失败用例）
    result: List[Tuple[str, Dict[str, Any]]] = []
    for i in order:
        rel_path, case = entries[i]
        if i in errors:
            entries[i] = (rel_path, {"name": case.get("name", "未命名测试用例"),
                                     "_collect_error": f"depends_on 配置错误: {errors[i]}"})
        elif resolved[i] is not None:
            case["depends_on"] = resolved[i]
        result.append(entries[i])
    return result


def build_case_ids(entries: List[Tuple[str, Dict[str, Any]]]) -> List[str]:
    """生成形如 '文件路径::用例名' 的用例ID，重名时追加序号保证唯一"""
    ids, seen = [], {}
    for rel_path, case in entries:
        base = f"{rel_path}::{case.get('name', '未命名测试用例')}"
        seen[base] = seen.get(base, 0) + 1
        ids.append(base if seen[base] == 1 else f"{base}#{seen[base]}")
    return ids
