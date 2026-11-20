"""提取变量的分层作用域管理

解决的问题：原先所有提取变量（extract / extract_from_db / setup）静默写入 session 级
单一 global_vars，同名覆盖无告警、生命周期贯穿整个 session、跨用例跨文件互相串扰。

层级与解析优先级（view 合并时从低到高逐层 update，近者优先）：
  session          config 预置变量（variables 段）
  file:<文件路径>   本文件 setup 提取的变量（仅本文件可见；cache 命中时导入目标文件层）
  chain            depends_on 传递闭包内上游用例的产出（近的上游优先于远的）
  case:<用例ID>    本用例 extract / extract_from_db 产出（仅本用例可见）

模式（config.yaml variable_scope.mode）：
  strict（默认）：extract 变量仅本用例可见，沿 depends_on 链向下游传播（传递闭包）；
                 未声明依赖却引用上游变量时 ${var} 保持字面量，立即暴露漏声明
  shared：兼容旧行为，extract / setup 提取写入 session 层全局共享（覆盖检测依然生效）

同名覆盖策略（variable_scope.overwrite）：写入时若同名变量来自更低层（本次写入会使其
在正常解析中不可达），按策略处理：
  warn（默认）：打 WARNING 并注明来源层；fail：抛 VariableOverwriteError 用例失败；
  silent：忽略。同层内重写（如同一用例重复提取同名变量）不算覆盖。

pytest-xdist 并行与作用域表同样不兼容（与 dependency.CASE_RESULTS 既有约束一致），仅支持单进程。
"""
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

# 依赖闭包表：case_id -> 传递上游 case_id 列表（按拓扑序、去重后近者靠后，近者优先覆盖）。
# 收集期由 conftest.pytest_generate_tests 调 build_upstream_map 构建（仿 dependency.CASE_RESULTS 模式）
UPSTREAM_MAP: Dict[str, List[str]] = {}

# 覆盖策略与模式取值
MODES = ("strict", "shared")
OVERWRITE_POLICIES = ("warn", "fail", "silent")


class VariableOverwriteError(Exception):
    """同名覆盖且策略为 fail 时抛出，用例失败并给出来源说明"""


def build_upstream_map(entries: List[Tuple[str, Dict[str, Any]]], ids: List[str]) -> None:
    """构建每条用例的 depends_on 传递闭包（strict 模式链路变量传播的依据）

    entries 为 case_collector.resolve_and_sort 的产出：已是拓扑序，
    且 depends_on 已改写为规范引用 "文件相对路径::用例名"（与 ids 基名一致）。
    闭包按拓扑序排列并去重（保留最近一次出现，近的上游靠后，view 合并时近者优先）。
    """
    UPSTREAM_MAP.clear()
    index_of: Dict[str, int] = {}
    for i, case_id in enumerate(ids):
        index_of.setdefault(case_id, i)

    memo: Dict[int, List[int]] = {}

    def _closure(i: int) -> List[int]:
        if i in memo:
            return memo[i]
        memo[i] = []  # 先占位防环（收集期已拦截循环依赖，此处兜底）
        order: List[int] = []
        for ref in entries[i][1].get("depends_on") or []:
            j = index_of.get(ref)
            if j is None or j == i:
                continue
            order.extend(_closure(j))
            order.append(j)
        last_seen: Dict[int, int] = {}
        for position, j in enumerate(order):
            last_seen[j] = position
        result = sorted(last_seen, key=last_seen.get)
        memo[i] = result
        return result

    for i, case_id in enumerate(ids):
        UPSTREAM_MAP[case_id] = [ids[j] for j in _closure(i)]


class VariableScopes:
    """分层变量作用域管理器（session 级 fixture 持有）"""

    def __init__(self, mode: str = "strict", overwrite: str = "warn"):
        if mode not in MODES:
            raise ValueError(f"variable_scope mode 不合法: {mode}（支持: {', '.join(MODES)}）")
        if overwrite not in OVERWRITE_POLICIES:
            raise ValueError(f"variable_scope overwrite 不合法: {overwrite}（支持: {', '.join(OVERWRITE_POLICIES)}）")
        self.mode = mode
        self.overwrite = overwrite
        self.session: Dict[str, Any] = {}
        self.file_layers: Dict[str, Dict[str, Any]] = {}
        self.case_layers: Dict[str, Dict[str, Any]] = {}
        # shared 模式下 session 层的写入者登记：变量名 -> 写入方标识（用于豁免同用例内重写）
        self._session_writer: Dict[str, str] = {}
        self._case_id: Optional[str] = None
        self._case_file: Optional[str] = None

    # ------------------------------------------------------------------ 上下文
    def set_context(self, case_id: str, case_file: str) -> None:
        """进入用例执行上下文（test_executor 在用例开始时调用）"""
        self._case_id = case_id
        self._case_file = case_file

    def clear_context(self) -> None:
        """退出用例执行上下文（case 层保留，供下游用例链路解析）"""
        self._case_id = None
        self._case_file = None

    # ------------------------------------------------------------------ 初始化
    def init_session(self, variables: Dict[str, Any]) -> None:
        """预置变量写入 session 层（fixture 初始化时调用一次）"""
        self.session = dict(variables)

    # ------------------------------------------------------------------ 读取
    def view(self) -> Dict[str, Any]:
        """当前上下文的扁平变量视图（供 ${var} 替换 / run_if 求值 / db SQL）

        合并顺序：session ← file 层 ← 链路上游 case 层（远→近）← 本用例 case 层。
        无上下文或 shared 模式时即 session（shared 模式提取全部写入 session）。
        用例执行期间请按消费点实时调用（setup 提取会动态更新 file 层）。
        """
        merged = dict(self.session)
        if self.mode == "shared":
            return merged
        if self._case_file:
            merged.update(self.file_layers.get(self._case_file, {}))
        if self._case_id:
            for upstream_id in UPSTREAM_MAP.get(self._case_id, ()):
                upstream_layer = self.case_layers.get(upstream_id)
                if upstream_layer:
                    merged.update(upstream_layer)
            merged.update(self.case_layers.get(self._case_id, {}))
        return merged

    # ------------------------------------------------------------------ 写入
    def extract(self, name: str, value: Any, layer: str = "case") -> str:
        """提取变量写入对应作用域层，返回作用域标签（供调用方日志使用）

        layer: "case"（本用例产出）或 "file"（文件 setup 产出）。
        shared 模式下一律写入 session 层（兼容旧行为）。
        覆盖检测见模块 docstring；同层内重写不算覆盖。
        """
        if self.mode == "shared":
            writer = self._writer_tag(layer)
            if name in self.session and self._session_writer.get(name) != writer:
                self._handle_overwrite(name, "session 层已有同名变量")
            self.session[name] = value
            self._session_writer[name] = writer
            return "session共享"

        if layer == "file":
            if not self._case_file:
                raise RuntimeError("extract(layer='file') 需要用例上下文（set_context）")
            target = self.file_layers.setdefault(self._case_file, {})
            # file 层仅高于 session；链路/file 层的同名变量在解析中仍优先于 file 层，不构成覆盖
            if name in self.session:
                self._handle_overwrite(name, "session 预置变量")
            target[name] = value
            return "文件作用域"

        if layer != "case" or not self._case_id:
            raise RuntimeError(f"extract(layer={layer!r}) 非法或缺少用例上下文（set_context）")
        target = self.case_layers.setdefault(self._case_id, {})
        # case 层高于其余全部层：chain / file / session 中同名变量会被遮蔽为不可达
        for source in self._shadowed_sources(name):
            self._handle_overwrite(name, source)
            break  # 只报告解析中实际被遮蔽的最高层来源
        target[name] = value
        return "用例作用域"

    def import_file_layer(self, case_file: str, variables: Dict[str, Any]) -> None:
        """将 setup 缓存结果导入目标文件的 file 层（cache 命中时调用，按设计共享不做覆盖检测）"""
        self.file_layers.setdefault(case_file, {}).update(variables)

    # ------------------------------------------------------------------ 内部
    def _shadowed_sources(self, name: str) -> List[str]:
        """case 层写入时，按解析优先级从高到低返回会被遮蔽的来源描述"""
        sources: List[str] = []
        if self._case_id:
            for upstream_id in UPSTREAM_MAP.get(self._case_id, ()):
                if name in self.case_layers.get(upstream_id, {}):
                    sources.append("依赖链上游用例产出的同名变量")
                    break
        if name in self.file_layers.get(self._case_file or "", {}):
            sources.append("文件setup提取的同名变量")
        if name in self.session:
            sources.append("session 预置变量")
        return sources

    def _handle_overwrite(self, name: str, source: str) -> None:
        """按覆盖策略处理：warn 打日志 / fail 抛异常 / silent 忽略"""
        context = f"用例 [{self._case_id or '未知'}]"
        message = f"变量覆盖: {context} 提取 {name!r} 遮蔽了{source}（overwrite={self.overwrite}）"
        if self.overwrite == "fail":
            raise VariableOverwriteError(message)
        if self.overwrite == "warn":
            logger.warning(message)

    def _writer_tag(self, layer: str) -> str:
        """shared 模式下写入者标识：同一用例/同一文件的重写不算覆盖"""
        if layer == "file":
            return f"setup:{self._case_file or '未知'}"
        return f"case:{self._case_id or '未知'}"
