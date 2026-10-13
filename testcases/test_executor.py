import json
from pathlib import Path

import allure
import pytest
from loguru import logger

from utils import setup_runner
from utils.config import PROJECT_ROOT, get_config
from utils.masking import mask_data, register_extracted
from utils.step_runner import cleanup_step, prepare_step, send_prepared


def _require_db(db_client, case_name: str):
    """DB功能前置检查：环境未配置数据库连接时给出明确指引"""
    if db_client is None:
        pytest.fail(
            f"用例 [{case_name}] 使用了数据库功能(db_setup/db_assertions/extract_from_db/db_teardown)，"
            f"但环境 [{get_config().env}] 未配置数据库连接。"
            f"请在 config/config.yaml 对应环境的 db 段补充连接信息（参考README 6.9节）"
        )


def _run_db_statements(db_client, statements, yaml_parser, global_vars, step_label: str):
    """执行一组SQL语句（db_setup/db_teardown），支持字符串或{sql: ...}两种写法"""
    for index, statement in enumerate(statements, 1):
        sql = statement.get("sql") if isinstance(statement, dict) else statement
        sql = yaml_parser.replace_variables(sql, global_vars)
        with allure.step(f"{step_label} #{index}"):
            affected = db_client.execute(sql)
            allure.attach(sql, "SQL", allure.attachment_type.TEXT)
            allure.attach(str(affected), "影响行数", allure.attachment_type.TEXT)


def test_api_executor(case_file: str, case: dict, yaml_parser, http_client, assertion, global_vars, db_client):
    """API测试执行器：每个YAML测试用例作为独立的pytest用例执行

    执行顺序：文件级setup -> db_setup -> 请求(可选) -> 接口断言(可选) -> db_assertions
              -> extract / extract_from_db -> finally: db_teardown
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

    # DB前置（数据准备/建表等）
    if case.get("db_setup"):
        _require_db(db_client, case_name)
        with allure.step("执行数据库前置(db_setup)"):
            _run_db_statements(db_client, case["db_setup"], yaml_parser, global_vars, "DB前置")

    response = None
    teardown_error = None
    try:
        # 准备并发送请求（纯数据库校验用例可无request；files文件句柄在发送前打开，无论成败都关闭）
        if isinstance(case.get("request"), dict):
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

        # 接口断言（软断言：所有断言都会执行，失败项一次性汇总）
        if assertions:
            with allure.step("执行断言"):
                assertion.run_assertions(response, assertions)

        # 数据库校验（如：接口调用后校验数据落库；软断言，与接口断言同风格汇总失败项）
        if case.get("db_assertions"):
            _require_db(db_client, case_name)
            with allure.step("执行数据库校验(db_assertions)"):
                db_assertions = yaml_parser.replace_variables(case["db_assertions"], global_vars)
                try:
                    assertion.run_db_assertions(db_client, db_assertions)
                finally:
                    # 查询结果进报告（脱敏），便于核对实际数据
                    try:
                        for index, spec in enumerate(db_assertions, 1):
                            result_text = str(mask_data(db_client.query_all(spec["sql"])))
                            allure.attach(result_text, f"校验#{index}查询结果", allure.attachment_type.TEXT)
                    except Exception:
                        pass

        # 提取接口变量（写入session级global_vars，供后续用例通过 ${var} 引用；提取值脱敏后进报告）
        if case.get("extract") and response is not None:
            with allure.step("提取变量"):
                for var_name, jsonpath in case["extract"].items():
                    var_value = assertion.get_value_from_jsonpath(response["body"], jsonpath)
                    global_vars[var_name] = var_value
                    # 敏感变量（token/手机号等）注册到文本替换表，后续日志中自动脱敏
                    register_extracted({var_name: var_value})
                    masked_value = mask_data({var_name: var_value})[var_name]
                    logger.info(f"成功提取变量: {var_name} = {masked_value}")
                    allure.attach(f"{var_name} = {masked_value}", "提取的变量", allure.attachment_type.TEXT)

        # 从数据库提取变量（var -> SQL，取首行首列）
        if case.get("extract_from_db"):
            _require_db(db_client, case_name)
            with allure.step("从数据库提取变量(extract_from_db)"):
                for var_name, sql in case["extract_from_db"].items():
                    sql = yaml_parser.replace_variables(sql, global_vars)
                    var_value = db_client.query_value(sql)
                    global_vars[var_name] = var_value
                    register_extracted({var_name: var_value})
                    masked_value = mask_data({var_name: var_value})[var_name]
                    logger.info(f"成功从数据库提取变量: {var_name} = {masked_value}")
                    allure.attach(f"{var_name} = {masked_value}\nSQL: {sql}", "数据库提取变量",
                                  allure.attachment_type.TEXT)

        logger.info(f"测试用例执行完成: {case_name}")
    finally:
        # DB清理（无论断言成败都执行，保证测试数据不残留；清理失败记录后不吞掉原始失败）
        if case.get("db_teardown"):
            if db_client is not None:
                try:
                    with allure.step("执行数据库清理(db_teardown)"):
                        _run_db_statements(db_client, case["db_teardown"], yaml_parser, global_vars, "DB清理")
                except Exception as e:
                    teardown_error = str(e)
                    logger.error(f"db_teardown执行失败: {teardown_error}")
            else:
                teardown_error = "环境未配置数据库连接，db_teardown未能执行"

    if teardown_error:
        pytest.fail(f"用例 [{case_name}] 的 db_teardown 执行失败（测试数据可能残留，请检查）: {teardown_error}")
