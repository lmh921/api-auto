"""用例收集：发现用例文件、校验用例结构、注册文件级setup、生成用例ID

收集在 pytest_generate_tests 阶段完成，每个测试用例对应一个独立的pytest用例。
结构不合法的用例不会被静默丢弃，而是生成一条失败用例并给出具体原因。
"""
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import jsonschema
from loguru import logger

from utils.config import PROJECT_ROOT, Config
from utils.yaml_parser import YamlParser

# 用例文件级 setup 注册表：文件相对路径 -> {"cache": bool, "steps": [...]}
FILE_SETUPS: Dict[str, Dict[str, Any]] = {}

# 单条用例/前置步骤的结构规则
CASE_SCHEMA = {
    "type": "object",
    "required": ["name", "request"],
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

    return entries


def build_case_ids(entries: List[Tuple[str, Dict[str, Any]]]) -> List[str]:
    """生成形如 '文件路径::用例名' 的用例ID，重名时追加序号保证唯一"""
    ids, seen = [], {}
    for rel_path, case in entries:
        base = f"{rel_path}::{case.get('name', '未命名测试用例')}"
        seen[base] = seen.get(base, 0) + 1
        ids.append(base if seen[base] == 1 else f"{base}#{seen[base]}")
    return ids
