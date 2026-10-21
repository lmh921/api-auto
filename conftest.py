import pytest
import yaml
from pathlib import Path
from loguru import logger
from utils.http_client import HttpClient
from utils.yaml_parser import YamlParser
from utils.assertion import Assertion
from utils.config import get_config
from utils.case_collector import build_case_ids, collect_all_cases
from utils.dependency import CASE_RESULTS
from utils.masking import MaskedDict, redact_text, register_extracted

# 以本文件位置定位项目根目录，避免依赖启动时的当前工作目录
PROJECT_ROOT = Path(__file__).resolve().parent

# 日志配置与具体环境无关，直接读取原始配置文件（不走环境解析）
with open(PROJECT_ROOT / 'config' / 'config.yaml', 'r', encoding='utf-8') as f:
    _raw_config = yaml.safe_load(f) or {}

_log_config = _raw_config.get('log') or {}

# 配置日志（patcher对所有日志文本做敏感值替换，覆盖断言消息等非结构化输出）
logger.remove() # 移除所有现有的处理器
logger.configure(patcher=lambda record: record.update(message=redact_text(record["message"])))
logger.add(
    PROJECT_ROOT / _log_config.get('file_path', 'logs/api_test.log'),
    level=_log_config.get('level', 'INFO'),
    rotation="100 MB",
    retention="7 days",
    encoding="utf-8"
)
logger.add(
    sink=print,
    level=_log_config.get('level', 'INFO'),
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> <level>{level}</level> <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)


def pytest_addoption(parser):
    """自定义命令行参数：多环境切换与正式环境确认"""
    group = parser.getgroup("ziufile-api", "接口自动化测试框架")
    group.addoption(
        "--env", action="store", dest="env", default=None,
        help="测试环境名称，见 config/config.yaml 的 environments 段；默认使用 default_env"
    )
    group.addoption(
        "--confirm-prod", action="store_true", dest="confirm_prod", default=False,
        help="确认在正式环境执行（默认拒绝在标记为 prod: true 的环境执行）"
    )


def pytest_generate_tests(metafunc):
    """按用例粒度参数化：每个YAML测试用例 = 一个独立的pytest用例

    同时把用例 tags 中与 pytest.ini 注册 marker 同名的项映射为 pytest marker，
    支持 -m smoke / -m regression 圈选用例。
    """
    if "case" not in metafunc.fixturenames:
        return

    config = get_config(
        env=metafunc.config.getoption("env"),
        confirm_prod=metafunc.config.getoption("confirm_prod"),
    )
    entries = collect_all_cases(config)
    ids = build_case_ids(entries)
    # 收集先于执行，此处清空依赖结果注册表是安全的（同进程重复调用pytest时防串场）
    CASE_RESULTS.clear()
    known_markers = {m.split(":", 1)[0].strip() for m in metafunc.config.getini("markers")}

    params = []
    for (rel_path, case), case_id in zip(entries, ids):
        marks = [getattr(pytest.mark, tag) for tag in case.get("tags", []) if tag in known_markers]
        # case用MaskedDict包装：pytest失败回显与Allure参数记录输出repr时敏感字段自动脱敏
        # case_id透传给执行器，用例结束后据此登记结果，供下游depends_on判定
        params.append(pytest.param(rel_path, MaskedDict(case), case_id, id=case_id, marks=marks))

    metafunc.parametrize("case_file,case,case_id", params)


@pytest.fixture(scope="session")
def global_vars():
    """全局变量fixture：预置配置 variables 段（支持 $ENV{名称} 引用环境变量）

    使用MaskedDict包装：repr脱敏，避免pytest失败回显泄漏明文
    """
    variables = get_config().variables
    register_extracted(variables)
    return MaskedDict(variables)

@pytest.fixture(scope="function")
def http_client():
    """HTTP客户端fixture（function作用域：每个用例独立实例，用例间env覆盖互不影响）"""
    config = get_config()
    client = HttpClient(
        base_url=config.base_url,
        timeout=config.timeout
    )
    yield client
    client.session.close()

@pytest.fixture(scope="function")
def yaml_parser():
    """YAML解析器fixture"""
    return YamlParser()

@pytest.fixture(scope="function")
def assertion():
    """断言器fixture"""
    return Assertion()

@pytest.fixture(scope="function")
def db_client():
    """数据库客户端fixture（function作用域：用例级连接，用完即关）

    环境未配置 db 段时返回 None，用例若使用了 db_* 字段会在执行时给出明确报错
    """
    db_config = get_config().db_config
    if not db_config:
        yield None
        return
    from utils.db_client import DBClient
    client = DBClient(db_config)
    yield client
    client.close()

@pytest.fixture(scope="session", autouse=True)
def clear_allure_results():
    """自动清理Allure报告结果目录"""
    allure_config = get_config().allure_config
    allure_dir = PROJECT_ROOT / allure_config.get('report_dir', 'reports/allure-results')
    if allure_config.get('clean', True):
        import os
        if os.path.exists(allure_dir):
            for file in os.listdir(allure_dir):
                file_path = os.path.join(allure_dir, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
    logger.info("Allure报告结果目录已清理")
