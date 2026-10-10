import json
from pathlib import Path

import allure
import pytest
from loguru import logger

from utils import setup_runner
from utils.config import PROJECT_ROOT, get_config
from utils.masking import mask_data, register_extracted
from utils.step_runner import cleanup_step, prepare_step, send_prepared


def test_api_executor(case_file: str, case: dict, yaml_parser, http_client, assertion, global_vars):
    """API测试执行器：每个YAML测试用例作为独立的pytest用例执行

    用例收集与参数化见 conftest.py 的 pytest_generate_tests。
    """
    if "_collect_error" in case:
        pytest.fail(f"用例收集失败: {case['_collect_error']}")

    case_name = case.get("name", "未命名测试用例")
    logger.info(f"开始执行测试用例: {case_file} :: {case_name}")

    # 设置测试报告信息
    allure.dynamic.title(case_name)
    allure.dynamic.description(case.get("description", ""))
    allure.dynamic.label("case_file", case_file)
    allure.dynamic.label("env", get_config().env)
    for tag in case.get("tags", []):
        allure.dynamic.tag(tag)

    # 文件级前置步骤（同一文件只执行一次；失败则该文件所有用例失败并给出原因）
    with allure.step("执行文件前置步骤(setup)"):
        setup_error = setup_runner.ensure_setup(case_file, global_vars, http_client, assertion, yaml_parser)
    if setup_error:
        pytest.fail(setup_error)

    # 变量替换：断言期望值支持 ${var}，整串占位符保留原始类型
    assertions = yaml_parser.replace_variables(case.get("assertions") or [], global_vars)
    case_dir = (PROJECT_ROOT / case_file).parent

    # 准备并发送请求（files文件句柄在发送前打开，无论成败都关闭）
    prep = prepare_step(case, global_vars, yaml_parser, case_dir)
    try:
        with allure.step(f"发送{prep['method']}请求到 {prep['url']}"):
            # 附件经过脱敏，避免token/手机号等明文进入报告
            allure.attach(json.dumps(mask_data(prep["attach_kwargs"]), ensure_ascii=False, default=str),
                          "请求参数", allure.attachment_type.JSON)

            response = send_prepared(prep, case, http_client)

            allure.attach(str(response["status_code"]), "响应状态码", allure.attachment_type.TEXT)
            allure.attach(json.dumps(mask_data(response["body"]), ensure_ascii=False, default=str),
                          "响应体", allure.attachment_type.JSON)

            if response["status_code"] != 200:
                logger.error(f"接口返回错误状态码: {response['status_code']}，URL: {prep['url']}，"
                             f"响应体: {mask_data(response['body'])}")
    finally:
        cleanup_step(prep, http_client)

    # 执行断言（软断言：所有断言都会执行，失败项一次性汇总）
    with allure.step("执行断言"):
        assertion.run_assertions(response, assertions)

    # 提取变量（写入session级global_vars，供后续用例通过 ${var} 引用；提取值脱敏后进报告）
    if case.get("extract"):
        with allure.step("提取变量"):
            for var_name, jsonpath in case["extract"].items():
                var_value = assertion.get_value_from_jsonpath(response["body"], jsonpath)
                global_vars[var_name] = var_value
                # 敏感变量（token/手机号等）注册到文本替换表，后续日志中自动脱敏
                register_extracted({var_name: var_value})
                masked_value = mask_data({var_name: var_value})[var_name]
                logger.info(f"成功提取变量: {var_name} = {masked_value}")
                allure.attach(f"{var_name} = {masked_value}", "提取的变量", allure.attachment_type.TEXT)

    logger.info(f"测试用例执行完成: {case_name}")
