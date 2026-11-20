"""全局配置模块

统一加载 config/config.yaml，收敛原先散落在 conftest/test_executor/debug脚本中的配置读取逻辑。

支持：
- 多环境：environments 段定义各环境的 base_url / caseData_path，通过 --env 或 TEST_ENV 环境变量切换，
  未指定时使用 default_env；未定义 environments 时自动回退到旧版顶层 base_url/caseData_path 写法
- 正式环境保护：标记 prod: true 的环境，必须显式追加 --confirm-prod（或环境变量 ALLOW_PROD=1）才会执行
- 预置变量：variables 段定义的变量注入 global_vars，值支持 $ENV{NAME} 引用环境变量（敏感数据外部化）
"""
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = PROJECT_ROOT / "config" / "config.yaml"

_ENV_VAR_PATTERN = re.compile(r"\$ENV\{([^}]+)\}")


class ConfigError(Exception):
    """配置错误"""


class Config:
    """一次解析完成的运行配置"""

    def __init__(self, env: Optional[str] = None, confirm_prod: bool = False):
        self.confirm_prod = confirm_prod
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            self.raw: Dict[str, Any] = yaml.safe_load(f) or {}

        environments = self.raw.get("environments") or {}
        if env is None:
            env = os.environ.get("TEST_ENV") or self.raw.get("default_env")

        if environments:
            if env not in environments:
                raise ConfigError(
                    f"未知环境: {env}，可用环境: {', '.join(environments)}"
                    f"（或在 config/config.yaml 的 environments 段中新增）"
                )
            self.env = env
            self.env_config: Dict[str, Any] = dict(environments[env] or {})
        else:
            if env not in (None, "default"):
                logger.warning("配置中未定义 environments 段，忽略环境参数，使用顶层配置")
            # 兼容旧版配置：直接使用顶层 base_url / caseData_path
            self.env = "default"
            self.env_config = {}

        # 正式环境保护
        if self.is_prod and not (confirm_prod or os.environ.get("ALLOW_PROD") == "1"):
            raise ConfigError(
                f"环境 [{self.env}] 标记为正式环境！\n"
                f"如确认要在正式环境执行测试，请追加 --confirm-prod 参数（或设置环境变量 ALLOW_PROD=1）"
            )

        logger.info(f"使用环境: {self.env} -> {self.base_url}")

    @property
    def is_prod(self) -> bool:
        return bool(self.env_config.get("prod", False))

    @property
    def base_url(self) -> str:
        return self.env_config.get("base_url", self.raw.get("base_url", ""))

    @property
    def case_data_path(self) -> Path:
        rel = self.env_config.get("caseData_path") or self.raw.get("caseData_path")
        if not rel:
            raise ConfigError("配置缺少 caseData_path（环境配置或顶层配置）")
        return PROJECT_ROOT / rel

    @property
    def timeout(self) -> int:
        return self.env_config.get("timeout", self.raw.get("timeout", 10))

    @property
    def retry_times(self) -> int:
        return self.raw.get("retry_times", 2)

    @property
    def retry_delay(self) -> float:
        return self.raw.get("retry_delay", 2.0)

    @property
    def log_config(self) -> Dict[str, Any]:
        return self.raw.get("log") or {}

    @property
    def allure_config(self) -> Dict[str, Any]:
        return self.raw.get("allure") or {}

    @property
    def variables(self) -> Dict[str, Any]:
        """预置变量，值支持 $ENV{NAME} 引用环境变量；环境变量未设置时该变量不生效"""
        result: Dict[str, Any] = {}
        for key, value in (self.raw.get("variables") or {}).items():
            if isinstance(value, str):
                match = _ENV_VAR_PATTERN.fullmatch(value.strip())
                if match:
                    env_name = match.group(1)
                    env_value = os.environ.get(env_name)
                    if env_value is None:
                        logger.warning(f"环境变量 {env_name} 未设置，预置变量 {key} 不生效")
                        continue
                    result[key] = env_value
                    continue
            result[key] = value
        return result

    @property
    def variable_scope_config(self) -> Dict[str, Any]:
        """变量作用域配置：mode(strict/shared) 与同名覆盖策略 overwrite(warn/fail/silent)"""
        section = self.raw.get("variable_scope") or {}
        mode = str(section.get("mode", "strict")).lower()
        overwrite = str(section.get("overwrite", "warn")).lower()
        if mode not in ("strict", "shared"):
            raise ConfigError(
                f"variable_scope.mode 配置不合法: {section.get('mode')}（支持 strict / shared）"
            )
        if overwrite not in ("warn", "fail", "silent"):
            raise ConfigError(
                f"variable_scope.overwrite 配置不合法: {section.get('overwrite')}（支持 warn / fail / silent）"
            )
        return {"mode": mode, "overwrite": overwrite}

    @property
    def db_config(self) -> Dict[str, Any]:
        """数据库连接配置：优先取环境配置的 db 段，回退到顶层 db 段；无配置返回空字典

        值支持 $ENV{NAME} 引用环境变量（如密码外部化），环境变量未设置时该键不生效
        """
        db = self.env_config.get("db") or self.raw.get("db")
        if not db:
            return {}
        result: Dict[str, Any] = {}
        for key, value in db.items():
            if isinstance(value, str):
                match = _ENV_VAR_PATTERN.fullmatch(value.strip())
                if match:
                    env_value = os.environ.get(match.group(1))
                    if env_value is None:
                        logger.warning(f"环境变量 {match.group(1)} 未设置，数据库配置 {key} 不生效")
                        continue
                    result[key] = env_value
                    continue
            result[key] = value
        return result


_config: Optional[Config] = None


def get_config(env: Optional[str] = None, confirm_prod: bool = False) -> Config:
    """获取全局配置（单例）

    env/confirm_prod 与当前实例不一致时重新加载（pytest_generate_tests 传入 --env 时触发）；
    不带参数调用时复用已有实例。
    """
    global _config
    need_init = _config is None
    if not need_init and env is not None and (env != _config.env or confirm_prod != _config.confirm_prod):
        need_init = True
    if need_init:
        _config = Config(env=env, confirm_prod=confirm_prod)
    return _config
