"""文件级前置步骤(setup)执行器

同一用例文件的 setup 只执行一次（挂在该文件第一条用例上），
提取的变量写入该文件的 file 作用域层（variable_scope），仅本文件用例可见，
避免每个文件重复维护登录用例。步骤提取逐条即时写入，后续 setup 步骤可引用前面步骤提取的变量。

跨文件缓存（cache: true）：相同环境 + 相同 setup 内容只执行一次，命中时把缓存变量
导入目标文件的 file 层。
注意：业务会改变账号状态（如注销登录）时不要开启缓存，否则后续文件可能拿到失效token。
"""
import json
from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger

from utils.case_collector import FILE_SETUPS
from utils.config import PROJECT_ROOT
from utils.masking import mask_data, register_extracted
from utils.step_runner import cleanup_step, prepare_step, send_prepared
from utils.yaml_parser import set_function_scope

# 跨文件缓存：(setup内容签名, 环境base_url) -> 提取的变量
_setup_cache: Dict[tuple, Dict[str, Any]] = {}
# 执行失败的文件：文件相对路径 -> 错误信息（该文件的所有用例直接失败并给出原因）
_setup_failed: Dict[str, str] = {}
# 本会话已执行过 setup 的文件
_done_files: set = set()


def ensure_setup(case_file: str, variable_scope, http_client, assertion, yaml_parser) -> Optional[str]:
    """确保文件级setup已执行；返回错误信息（None表示成功或无需setup）"""
    spec = FILE_SETUPS.get(case_file)
    if not spec or case_file in _done_files:
        return None
    if case_file in _setup_failed:
        return _setup_failed[case_file]

    steps = spec.get("steps") or []
    if not steps:
        return None

    signature = (json.dumps(steps, sort_keys=True, ensure_ascii=False), str(http_client.base_url))
    if spec.get("cache") and signature in _setup_cache:
        variable_scope.import_file_layer(case_file, _setup_cache[signature])
        _done_files.add(case_file)
        logger.info(f"setup命中缓存，跳过执行: {case_file}")
        return None

    file_dir = (PROJECT_ROOT / case_file).parent
    extracted: Dict[str, Any] = {}
    try:
        # setup 内的造数函数表达式（${uuid()} 等）在文件域内保持一致，用例域由执行器随后切回
        set_function_scope(f"setup::{case_file}")
        for step in steps:
            # 视图按步骤实时获取：前面步骤提取的变量（file层）对本步骤可见
            prep = prepare_step(step, variable_scope.view(), yaml_parser, file_dir)
            try:
                response = send_prepared(prep, step, http_client)
            finally:
                cleanup_step(prep, http_client)

            if step.get("assertions"):
                assertion.run_assertions(
                    response, yaml_parser.replace_variables(step["assertions"], variable_scope.view()))

            for var_name, jsonpath in (step.get("extract") or {}).items():
                var_value = assertion.get_value_from_jsonpath(response["body"], jsonpath)
                extracted[var_name] = var_value
                scope_label = variable_scope.extract(var_name, var_value, layer="file")
                # 敏感变量（token等）注册到文本替换表，后续日志/回显自动脱敏
                register_extracted({var_name: var_value})
                masked = mask_data({var_name: var_value})[var_name]
                logger.info(f"setup提取变量: {var_name} = {masked}（写入{scope_label}）")

        # cache 保存本文件 setup 的产出，供相同内容跨文件复用
        if spec.get("cache"):
            _setup_cache[signature] = dict(extracted)
        _done_files.add(case_file)
        return None
    except Exception as e:
        error = f"文件 {case_file} 的前置步骤(setup)执行失败: {e}"
        logger.error(error)
        _setup_failed[case_file] = error
        return error
