"""数据库客户端：基于 DB-API 2.0 的轻量封装

支持驱动：
- mysql  -> pymysql（pip install pymysql）
- sqlite -> sqlite3（Python内置，零依赖，可用于演示与离线验证）

连接参数来自 config/config.yaml 环境配置的 db 段（见 Config.db_config），
密码等敏感值支持 $ENV{环境变量名} 外部化。
"""
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from utils.config import PROJECT_ROOT


class DBClient:
    """单连接数据库客户端（用例级生命周期，由 conftest 的 db_client fixture 管理）"""

    SUPPORTED_DRIVERS = ("mysql", "sqlite")

    def __init__(self, db_config: Dict[str, Any]):
        self.driver = str(db_config.get("driver", "mysql")).lower()
        if self.driver not in self.SUPPORTED_DRIVERS:
            raise ValueError(f"不支持的数据库驱动: {self.driver}（支持: {', '.join(self.SUPPORTED_DRIVERS)}）")
        self.config = db_config
        self._conn = None
        logger.info(f"DB客户端就绪: driver={self.driver} host={db_config.get('host', '-')} "
                    f"database={db_config.get('database', db_config.get('path', '-'))}")

    def _connect(self):
        """懒连接：首次使用时建立"""
        if self._conn is not None:
            return self._conn

        if self.driver == "mysql":
            import pymysql
            self._conn = pymysql.connect(
                host=self.config.get("host", "127.0.0.1"),
                port=int(self.config.get("port", 3306)),
                user=self.config.get("user", ""),
                password=self.config.get("password", ""),
                database=self.config.get("database", ""),
                charset=self.config.get("charset", "utf8mb4"),
                connect_timeout=int(self.config.get("connect_timeout", 10)),
                cursorclass=pymysql.cursors.DictCursor,
            )
        else:  # sqlite
            db_path = Path(self.config.get("path", "data/test.db"))
            if not db_path.is_absolute():
                db_path = PROJECT_ROOT / db_path
            db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            self._conn = conn
        return self._conn

    def query_all(self, sql: str) -> List[Dict[str, Any]]:
        """执行查询，返回行列表（每行为 {列名: 值}）"""
        conn = self._connect()
        cursor = conn.cursor()
        try:
            cursor.execute(sql)
            rows = [dict(row) for row in cursor.fetchall()]
        finally:
            cursor.close()
        logger.debug(f"DB查询 {len(rows)} 行: {sql}")
        return rows

    def query_value(self, sql: str) -> Optional[Any]:
        """执行查询，返回首行首列的标量值；无结果时返回 None"""
        rows = self.query_all(sql)
        if not rows:
            return None
        return next(iter(rows[0].values()))

    def execute(self, sql: str) -> int:
        """执行DDL/DML语句并提交，返回受影响行数

        注意取 rowcount 而非 execute 返回值：sqlite3返回cursor自身，pymysql返回int，DB-API不统一
        """
        conn = self._connect()
        cursor = conn.cursor()
        try:
            cursor.execute(sql)
            affected = cursor.rowcount
            conn.commit()
        finally:
            cursor.close()
        logger.info(f"DB执行完成(影响{affected}行): {sql}")
        return affected

    def close(self):
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception as e:
                logger.warning(f"DB连接关闭异常: {e}")
            finally:
                self._conn = None
