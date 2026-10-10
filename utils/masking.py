"""敏感信息脱敏工具

三层防护：
1. mask_data: 深拷贝并脱敏字典/列表中的敏感键值（用于Allure附件、日志内容）
2. MaskedDict: repr输出脱敏的dict（用于global_vars/case等会被pytest失败回显和Allure参数记录的对象）
3. register_secret + redact_text: 注册已知敏感值，对任意文本做替换（用于loguru patcher，覆盖断言消息等）

断言内部仍使用真实值，脱敏只影响展示层。
"""
import re
from typing import Any, Dict

# 无条件脱敏的键（不区分大小写，子串匹配：x-mobile、X-Auth-Token等同样命中）
SENSITIVE_KEYS = {
    "password", "passwd", "pwd",
    "token", "access_token", "refresh_token", "authorization",
    "secret", "apikey", "api_key",
    "smscode", "sms_code", "verification_code", "vcode",
    "mobile", "phone", "telephone",
    "idcard", "id_card",
    "cvv", "cvc",
    "cookie", "set-cookie", "session", "sessionid",
}

# 条件脱敏的键：仅当值为长度>=4的字符串时脱敏
# （"code" 常被用作业务响应码如 {"code": 0}，不能一刀切；验证码通常是长度>=4的字符串）
CONDITIONAL_KEYS = {"code", "key"}

MASK = "******"


def _is_sensitive(key: Any, value: Any) -> bool:
    key_name = str(key).lower().strip()
    for sensitive in SENSITIVE_KEYS:
        if sensitive in key_name:
            return True
    for conditional in CONDITIONAL_KEYS:
        if conditional in key_name and isinstance(value, str) and len(value) >= 4:
            return True
    return False


def mask_data(data: Any) -> Any:
    """深拷贝并脱敏：字典/列表中的敏感键值替换为 ******，其余结构原样保留"""
    if isinstance(data, dict):
        return {
            k: (MASK if _is_sensitive(k, v) else mask_data(v))
            for k, v in data.items()
        }
    if isinstance(data, (list, tuple)):
        masked = [mask_data(item) for item in data]
        return type(data)(masked) if isinstance(data, tuple) else masked
    return data


class MaskedDict(dict):
    """repr输出脱敏的dict

    pytest失败回显、Allure参数记录都会输出fixture/参数的repr，
    用本类包装含敏感数据的字典可避免明文进入报告。
    """

    def __repr__(self):
        return repr(mask_data(dict(self)))

    __str__ = __repr__


# ===== 已知敏感值注册与文本替换 =====

_registered_secrets: set = set()


def register_secret(value: Any) -> None:
    """注册一个敏感值（如提取到的token），之后所有日志文本中出现该值都会被替换"""
    if value is not None and str(value):
        _registered_secrets.add(str(value))


def register_extracted(vars_dict: Dict[str, Any]) -> None:
    """批量注册提取的变量：仅注册键名敏感的变量值"""
    for key, value in vars_dict.items():
        if _is_sensitive(key, value):
            register_secret(value)


def redact_text(text: str) -> str:
    """替换文本中所有已注册的敏感值"""
    for secret in _registered_secrets:
        if secret in text:
            text = text.replace(secret, MASK)
    return text
