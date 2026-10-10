import time
from typing import Any, Dict, Optional

import requests
from loguru import logger

from utils.masking import mask_data


class HttpClient:
    """HTTP客户端，封装requests库"""

    # 幂等方法：5xx可安全重试；非幂等方法（POST/PUT/PATCH/DELETE）服务端可能已受理，
    # 自动重试会导致重复提交，因此仅连接类错误（请求未到达服务端）才重试
    IDEMPOTENT_METHODS = {"GET", "HEAD", "OPTIONS"}

    def __init__(self, base_url: str = "", timeout: int = 10,
                 max_retries: Optional[int] = None, retry_delay: Optional[float] = None):
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self._max_retries = max_retries
        self._retry_delay = retry_delay

    def _retry_settings(self) -> tuple:
        """重试参数：优先用实例级设置，否则读取全局配置 retry_times/retry_delay"""
        if self._max_retries is not None:
            delay = self._retry_delay if self._retry_delay is not None else 2.0
            return self._max_retries, delay
        try:
            from utils.config import get_config
            config = get_config()
            return config.retry_times, config.retry_delay
        except Exception:
            return 2, 2.0

    def request(self, method: str, url: str, max_retries: Optional[int] = None,
                retry_delay: Optional[float] = None, **kwargs) -> Dict[str, Any]:
        """发送HTTP请求，按配置重试

        重试策略：
        - 5xx响应：仅幂等方法（GET/HEAD/OPTIONS）重试
        - 连接错误（请求未到达服务端）：所有方法重试
        - 超时等其他请求异常：仅幂等方法重试
        - max_retries/retry_delay 不传时使用全局配置
        """
        if not url.startswith(('http://', 'https://')):
            url = self.base_url + url

        default_retries, default_delay = self._retry_settings()
        max_retries = default_retries if max_retries is None else max_retries
        retry_delay = default_delay if retry_delay is None else retry_delay
        method = method.upper()
        idempotent = method in self.IDEMPOTENT_METHODS

        attempt = 0
        while True:
            logger.info(f"发送请求: {method} {url} (尝试 {attempt + 1}/{max_retries + 1})")
            logger.debug(f"请求参数: {mask_data(kwargs)}")

            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    timeout=self.timeout,
                    **kwargs
                )

                logger.info(f"响应状态码: {response.status_code}")
                logger.debug(f"响应头: {mask_data(dict(response.headers))}")

                try:
                    response_data = response.json()
                except ValueError:
                    response_data = response.text
                logger.debug(f"响应体: {mask_data(response_data)}")

                response_result = {
                    'status_code': response.status_code,
                    'headers': dict(response.headers),
                    'body': response_data,
                    'url': response.url,
                    'elapsed': response.elapsed.total_seconds()
                }

                if 500 <= response.status_code < 600 and idempotent and attempt < max_retries:
                    logger.warning(f"接口返回{response.status_code}错误，将在{retry_delay}秒后重试")
                    time.sleep(retry_delay)
                    attempt += 1
                    continue

                return response_result

            except requests.exceptions.ConnectionError as e:
                # 连接类错误：请求未到达服务端，任意方法都可安全重试
                if attempt < max_retries:
                    logger.warning(f"连接失败，将在{retry_delay}秒后重试: {e}")
                    time.sleep(retry_delay)
                    attempt += 1
                    continue
                raise Exception(f"请求失败，重试{max_retries}次后仍无法连接: {e}") from e

            except requests.exceptions.RequestException as e:
                # 超时等其他请求异常：仅幂等方法自动重试
                if idempotent and attempt < max_retries:
                    logger.warning(f"请求异常，将在{retry_delay}秒后重试: {e}")
                    time.sleep(retry_delay)
                    attempt += 1
                    continue
                raise Exception(f"请求失败: {e}") from e

    def get(self, url: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """发送GET请求"""
        return self.request('GET', url, params=params, **kwargs)

    def post(self, url: str, data: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """发送POST请求"""
        return self.request('POST', url, data=data, json=json, **kwargs)

    def put(self, url: str, data: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """发送PUT请求"""
        return self.request('PUT', url, data=data, json=json, **kwargs)

    def delete(self, url: str, **kwargs) -> Dict[str, Any]:
        """发送DELETE请求"""
        return self.request('DELETE', url, **kwargs)

    def patch(self, url: str, data: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """发送PATCH请求"""
        return self.request('PATCH', url, data=data, json=json, **kwargs)

    def set_headers(self, headers: Dict[str, str]) -> None:
        """设置默认请求头"""
        self.session.headers.update(headers)

    def set_cookies(self, cookies: Dict[str, str]) -> None:
        """设置cookies"""
        self.session.cookies.update(cookies)

    def get_cookies(self) -> Dict[str, str]:
        """获取cookies"""
        return requests.utils.dict_from_cookiejar(self.session.cookies)
