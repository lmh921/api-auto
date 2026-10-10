"""单个步骤（用例/前置步骤）的准备与发送

职责：变量替换、env覆盖、请求参数组装、files文件句柄管理。
调用方负责 allure 记录、断言与变量提取。
"""
from pathlib import Path
from typing import Any, Dict, List, Tuple

from utils.config import PROJECT_ROOT
from utils.yaml_parser import YamlParser


def _open_files(files_spec: Dict[str, Any], base_dir: Path) -> Tuple[Dict[str, Any], List[Any]]:
    """将YAML中的files配置转为requests可用的文件句柄

    支持两种写法：
    - 字段: "路径"                          -> 自动取文件名
    - 字段: ["路径", "文件名", "Content-Type"] -> 自定义文件名与类型（后两项可选）
    相对路径优先相对于用例文件所在目录解析，找不到再回退到项目根目录。
    """
    files: Dict[str, Any] = {}
    handles: List[Any] = []
    for field, spec in files_spec.items():
        if isinstance(spec, str):
            path_str, filename, content_type = spec, Path(spec).name, None
        elif isinstance(spec, list) and 1 <= len(spec) <= 3:
            path_str = spec[0]
            filename = spec[1] if len(spec) > 1 else Path(spec[0]).name
            content_type = spec[2] if len(spec) > 2 else None
        else:
            raise ValueError(
                f"files 配置不合法（字段 {field}）: {spec}，"
                f"支持 \"路径\" 或 [\"路径\", \"文件名\", \"Content-Type\"]"
            )
        path = Path(path_str)
        if not path.is_absolute():
            candidate = base_dir / path
            path = candidate if candidate.exists() else PROJECT_ROOT / path
        handle = open(path, "rb")
        handles.append(handle)
        files[field] = (filename, handle, content_type) if content_type else (filename, handle)
    return files, handles


def prepare_step(step: Dict[str, Any], global_vars: dict, yaml_parser: YamlParser,
                 base_dir: Path) -> Dict[str, Any]:
    """准备一个步骤：变量替换、组装requests参数（files此时才打开文件句柄）"""
    request_data = yaml_parser.replace_variables(step.get("request") or {}, global_vars)
    method = str(request_data.get("method", "GET")).upper()
    url = str(request_data.get("url", ""))

    kwargs: Dict[str, Any] = {}
    for key in ("params", "headers", "json"):
        if key in request_data:
            kwargs[key] = request_data[key]
    if "body" in request_data:
        kwargs["data"] = request_data["body"]

    file_handles: List[Any] = []
    attach_kwargs = dict(kwargs)
    if "files" in request_data:
        files, file_handles = _open_files(request_data["files"], base_dir)
        kwargs["files"] = files
        attach_kwargs["files"] = request_data["files"]  # 附件中展示路径而非句柄

    return {
        "method": method,
        "url": url,
        "kwargs": kwargs,
        "attach_kwargs": attach_kwargs,
        "file_handles": file_handles,
    }


def send_prepared(prep: Dict[str, Any], step: Dict[str, Any], http_client) -> Dict[str, Any]:
    """发送请求，应用步骤级env覆盖（执行后由cleanup_step恢复）"""
    env = step.get("env") or {}
    prep["_saved_env"] = (http_client.base_url, http_client.timeout)
    if "base_url" in env:
        http_client.base_url = env["base_url"]
    if "timeout" in env:
        http_client.timeout = env["timeout"]
    return http_client.request(prep["method"], prep["url"], **prep["kwargs"])


def cleanup_step(prep: Dict[str, Any], http_client) -> None:
    """恢复env覆盖并关闭文件句柄，必须在send_prepared之后调用"""
    saved = prep.pop("_saved_env", None)
    if saved:
        http_client.base_url, http_client.timeout = saved
    for handle in prep.get("file_handles", []):
        try:
            handle.close()
        except Exception:
            pass
