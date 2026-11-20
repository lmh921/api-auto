# Code Wiki · ziufileApi 接口自动化测试框架

> 版本：v1.1 · 更新时间：2026-10-14
> 项目路径：`d:\pythontest\ziufileApi`

---

## 目录

1. [项目概述](#1-项目概述)
2. [整体架构](#2-整体架构)
3. [目录结构](#3-目录结构)
4. [模块详解](#4-模块详解)
   - 4.1 [config · 全局配置模块](#41-configpy-全局配置模块)
   - 4.2 [http_client · HTTP客户端](#42-http_clientpy-http客户端)
   - 4.3 [yaml_parser · YAML解析器](#43-yaml_parserpy-yaml解析器)
   - 4.4 [assertion · 断言模块](#44-assertionpy-断言模块)
   - 4.5 [case_collector · 用例收集器](#45-case_collectorpy-用例收集器)
   - 4.6 [step_runner · 步骤执行器](#46-step_runnerpy-步骤执行器)
   - 4.7 [setup_runner · 文件级前置执行器](#47-setup_runnerpy-文件级前置执行器)
   - 4.8 [masking · 敏感信息脱敏](#48-maskingpy-敏感信息脱敏)
   - 4.9 [result_summary · 测试结果摘要](#49-result_summarypy-测试结果摘要)
   - 4.10 [db_client · 数据库客户端](#410-db_clientpy-数据库客户端)
   - 4.11 [dependency · 用例依赖与条件执行](#411-dependencypy-用例依赖与条件执行)
5. [入口与执行层](#5-入口与执行层)
   - 5.1 [conftest.py · Pytest 配置与 Fixtures](#51-conftestpy-pytest-配置与-fixtures)
   - 5.2 [test_executor.py · 用例执行主体](#52-test_executorpy-用例执行主体)
   - 5.3 [run_test.py · 统一运行脚本](#53-run_testpy-统一运行脚本)
   - 5.4 [run_test.bat · Windows 菜单式批处理](#54-run_testbat-windows-菜单式批处理)
6. [依赖关系](#6-依赖关系)
   - 6.1 [第三方依赖](#61-第三方依赖)
   - 6.2 [内部模块依赖图](#62-内部模块依赖图)
7. [配置与环境](#7-配置与环境)
   - 7.1 [config/config.yaml](#71-configconfigyaml)
   - 7.2 [pytest.ini](#72-pytestini)
   - 7.3 [环境变量](#73-环境变量)
8. [YAML 用例规范](#8-yaml-用例规范)
   - 8.1 [单接口用例](#81-单接口用例)
   - 8.2 [多接口用例集](#82-多接口用例集)
   - 8.3 [文件级前置步骤 setup](#83-文件级前置步骤-setup)
   - 8.4 [变量提取与引用](#84-变量提取与引用)
   - 8.5 [文件上传 files](#85-文件上传-files)
   - 8.6 [断言类型一览](#86-断言类型一览)
   - 8.7 [JSONPath 语法](#87-jsonpath-语法)
   - 8.8 [数据库连接与校验](#88-数据库连接与校验)
   - 8.9 [用例依赖与条件执行](#89-用例依赖与条件执行)
9. [项目运行方式](#9-项目运行方式)
   - 9.1 [环境准备](#91-环境准备)
   - 9.2 [本地运行](#92-本地运行)
   - 9.3 [命令行参数](#93-命令行参数)
   - 9.4 [Allure 报告](#94-allure-报告)
10. [Jenkins CI/CD](#10-jenkins-cicd)
11. [扩展开发指南](#11-扩展开发指南)
12. [常见问题 FAQ](#12-常见问题-faq)

---

## 1. 项目概述

**ziufileApi** 是一个基于 Python + Pytest 的 **零代码** 接口自动化测试框架。测试人员只需编写 YAML 格式的测试用例，即可完成从 HTTP 请求发送、断言校验、变量提取传递、多环境切换、Allure 报告生成到 Jenkins 邮件通知的完整闭环，无需编写任何 Python 代码。

### 1.1 核心特性

| 特性 | 说明 |
|------|------|
| 零代码封装 | 仅用 YAML 描述测试用例，测试人员无需掌握 Python |
| 用例级隔离 | 每个 YAML 用例 = 独立 Pytest 用例，单条失败不影响其他 |
| 软断言 | 多条断言全部执行后一次性汇总失败项 |
| 变量传递 | `extract` 提取 + `${var}` 引用，整串占位符保留原始类型 |
| 文件级 setup | 登录等前置步骤一个文件写一次，所有用例复用 |
| setup 缓存 | 相同环境 + 相同 setup 内容跨文件缓存执行结果 |
| 多环境切换 | `--env <name>` 一键切换；支持环境变量 `TEST_ENV` |
| 正式环境保护 | `prod: true` 环境须追加 `--confirm-prod` 或 `ALLOW_PROD=1` |
| 自动脱敏 | token / password / mobile 等敏感字段自动打码 |
| Allure 集成 | 自动生成带附件的美观报告，请求/响应脱敏后展示 |
| CI 流水线 | 内置 Jenkinsfile：装依赖→跑测试→报告→邮件通知 |
| JSONPath | 基于 jsonpath-ng，`$` 前缀可省略，支持 `$length` 扩展 |
| 用例结构校验 | YAML 结构不合规生成显式失败用例而非静默跳过 |
| Marker 支持 | 用例 tags 自动映射 pytest marker，`-m smoke` 圈选用例 |
| **数据库断言** | 支持 `db_setup` / `db_assertions` / `extract_from_db` / `db_teardown`，MySQL + SQLite 双驱动，用例级连接生命周期 |
| **用例依赖** | `depends_on` 显式依赖：上游失败/跳过/未执行时下游自动 skip；依赖图拓扑排序，跨文件依赖不依赖文件名排序 |
| **条件执行** | `run_if` 按变量条件决定执行与否，不满足时 skip（不是失败） |

### 1.2 技术栈

- **语言**：Python 3.8+
- **测试引擎**：Pytest
- **HTTP 客户端**：requests（封装重试与连接池）
- **用例格式**：YAML（PyYAML）
- **断言表达**：JSONPath（jsonpath-ng） + jsonschema（结构校验）
- **日志**：Loguru（带自动脱敏 patcher）
- **报告**：Allure（allure-pytest + allure commandline）
- **CI**：Jenkins 声明式流水线（Email Extension 插件）

---

## 2. 整体架构

```
┌───────────────────────────────────────────────────────────────┐
│                       入口层 (Entry)                           │
│   run_test.py   run_test.bat   pytest CLI   Jenkinsfile       │
└───────────────────────────┬───────────────────────────────────┘
                            │
┌───────────────────────────▼───────────────────────────────────┐
│                    Pytest 集成层 (Harness)                     │
│  conftest.py            │          testcases/test_executor.py │
│  参数化 / Fixtures      │          单条用例编排 + Allure 记录  │
└───────────────────────────┬───────────────────────────────────┘
                            │
┌───────────────────────────▼───────────────────────────────────┐
│                    核心业务层 (Core)                           │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │case_collector│  │ setup_runner │  │    step_runner       │  │
│  │ 用例发现     │  │ 文件级setup  │  │ 步骤准备/发送/清理   │  │
│  │ 结构校验     │  │ 执行与缓存   │  │ files/env 覆盖       │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
│         │                 │                     │              │
│         ▼                 ▼                     ▼              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ yaml_parser  │  │  assertion   │  │    http_client       │  │
│  │ 变量替换     │  │ 软断言引擎   │  │ 重试/幂等/session    │  │
│  │ 类型保留     │  │ JSONPath 取值│  │ 日志记录             │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │     masking.py  (横切关注点：日志/附件/repr 脱敏)         │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────┬───────────────────────────────────┘
                            │
┌───────────────────────────▼───────────────────────────────────┐
│                    配置与数据层 (Config & Data)                 │
│   config/config.yaml      data/*_data/*.yaml   pytest.ini      │
└───────────────────────────────────────────────────────────────┘
                            │
┌───────────────────────────▼───────────────────────────────────┐
│                    产物与 CI 层 (Artifacts)                    │
│   logs/api_test.log   reports/  邮件摘要   Jenkins 归档        │
└───────────────────────────────────────────────────────────────┘
```

**调用链概览**：
```
pytest 启动
  → conftest.pytest_addoption            注册 --env / --confirm-prod
  → conftest.pytest_generate_tests
       → get_config()                    加载环境并校验正式环境保护
       → collect_all_cases()             扫描用例目录 + 结构校验 + 注册 FILE_SETUPS
       → build_case_ids() + build_upstream_map()   用例ID + 依赖闭包表（链路变量传播依据）
       → parametrize("case_file,case")  每一条用例独立参数化 + tag→marker 映射
  → conftest.clear_allure_results        session 级清理
  → 对每个参数化用例：
       → test_api_executor(case_file, case, case_id, yaml_parser, http_client, assertion, variable_scope)
            → allure 动态打标
            → variable_scope.set_context   进入用例作用域上下文（结束 clear_context）
            → setup_runner.ensure_setup  文件级setup（首次触发，支持缓存）
                 → prepare_step → send_prepared → cleanup_step
                 → run_assertions → extract 写文件作用域层 → register_extracted
            → prepare_step(case)         变量替换（variable_scope.view()） + 组装files
            → send_prepared(case)        发送 + env覆盖
            → cleanup_step               恢复env + 关闭文件句柄
            → assertion.run_assertions   软断言
            → variable_scope.extract     写入用例作用域层（沿 depends_on 链传播）+ 注册脱敏
  → (可选) result_summary.py             解析 allure-results → 邮件正文/附件
```

---

## 3. 目录结构

```
ziufileApi/
├── config/                         # 全局配置
│   └── config.yaml                 # 多环境定义、超时重试、预置变量、日志与Allure
│
├── data/                           # 真实业务测试用例（按环境 caseData_path 加载）
│   └───├── case_template/          # 模板用例（当前目录演示用）
│       ├── client_data/            # 客户端侧用例：login / selectUser / delUser ...
│       └── station_data/           # 驿站侧用例
│
├── logs/                           # 日志输出（运行时生成，.gitignore）
│   └── api_test.log
│
├── reports/                        # 测试报告（运行时生成）
│   ├── allure-results/             # Pytest 输出的原始结果 JSON
│   ├── allure-report/              # Allure 生成的静态报告
│   ├── email_summary.txt           # 邮件正文（result_summary.py 输出）
│   └── email_summary.html          # 邮件附件（result_summary.py 输出）
│
├── testcases/                      # Pytest 测试代码 + 演示用例
│   ├── test_executor.py            # 主执行函数 test_api_executor
│   ├── example_test.yaml           # 完整示例（JSONPlaceholder，含 env 覆盖）
│   ├── mock_test.yaml              # 框架自测（httpbin.org）
│   ├── multi_case_template.yaml    # 多接口用例模板（含全局变量注释）
│   └── single_case_template.yaml   # 单接口用例模板
│
├── utils/                          # 核心模块（12 个子模块）
│   ├── config.py                   # 全局配置：多环境/正式环境保护/预置变量/变量作用域/DB配置
│   ├── http_client.py              # HTTP 客户端：幂等重试策略
│   ├── yaml_parser.py              # YAML 解析 + ${var} 变量替换（保留类型）
│   ├── assertion.py                # 软断言 + JSONPath 取值引擎 + DB断言
│   ├── case_collector.py           # 用例发现 / jsonschema 校验 / setup 注册 / 依赖拓扑排序 / 用例ID
│   ├── dependency.py               # depends_on 判定 / run_if 条件执行 / 结果注册表
│   ├── variable_scope.py           # 变量作用域：case/链路/文件/session 分层 + 同名覆盖告警
│   ├── step_runner.py              # 单步骤准备-发送-清理三件套
│   ├── setup_runner.py             # 文件级 setup 执行 + 跨文件缓存
│   ├── masking.py                  # 三层脱敏：字典/Repr/文本替换
│   ├── result_summary.py           # Allure 结果 → 邮件正文+HTML附件
│   └── db_client.py                # 数据库客户端（MySQL/SQLite，用例级连接）
│
├── conftest.py                     # Pytest 入口：参数化 + Fixtures + 日志脱敏
├── pytest.ini                      # Pytest 静态配置：markers / addopts / testpaths
├── requirements.txt                # 第三方依赖清单
├── run_test.py                     # argparse 统一运行脚本（推荐入口）
├── run_test.bat                    # Windows 菜单式批处理
├── Jenkinsfile                     # Jenkins 声明式流水线（装依赖→测→报→邮）
├── .gitignore                      # 忽略 pycache / venv / logs / reports
├── README.md                       # 用户使用手册
└── CODE_WIKI.md                    # 本文档（工程级完整 Code Wiki）
```

---

## 4. 模块详解

### 4.1 config.py · 全局配置模块

**文件**：[utils/config.py](file:///d:/pythontest/ziufileApi/utils/config.py)

#### 职责

- 统一加载 `config/config.yaml`
- 多环境切换：支持 `--env`、`TEST_ENV`、`default_env` 三级回退
- 正式环境保护：`prod: true` 环境需要 `--confirm-prod` 或 `ALLOW_PROD=1`
- 预置变量：`variables` 段支持 `$ENV{NAME}` 引用系统环境变量
- 单例缓存：`get_config()` 无参复用已有实例；参数变化时重建
- 兼容旧版：无 `environments` 段时回退到顶层 `base_url` / `caseData_path`

#### 关键类

| 类/函数 | 类型 | 说明 |
|---------|------|------|
| `ConfigError` | 异常类 | 配置错误统一抛出 |
| `Config(env, confirm_prod)` | 数据类 | 一次解析完成的运行配置 |
| `get_config(env, confirm_prod)` | 函数 | 单例入口；参数不一致时重建 |

#### Config 核心属性（property）

| 属性 | 类型 | 来源 | 说明 |
|------|------|------|------|
| `env` | `str` | environments 段 key / default | 当前环境名 |
| `is_prod` | `bool` | `env_config.prod` | 是否正式环境 |
| `base_url` | `str` | env_config > raw | 接口基础地址 |
| `case_data_path` | `Path` | env_config > raw | 用例目录绝对路径 |
| `timeout` | `int` | env_config > raw（默认10） | 请求超时（秒） |
| `retry_times` | `int` | raw（默认2） | 失败重试次数（不含首次） |
| `retry_delay` | `float` | raw（默认2.0） | 重试间隔（秒） |
| `log_config` | `dict` | raw.log | Loguru 配置 |
| `allure_config` | `dict` | raw.allure | Allure 配置 |
| `variables` | `dict` | raw.variables | 预置变量（含 `$ENV{}` 展开） |
| `db_config` | `dict` | env_config.db > raw.db | 数据库连接配置（支持 `$ENV{NAME}` 展开密码等）；无配置返回空 dict |

#### 预置变量 `$ENV{}` 展开规则

```python
# 整串匹配 $ENV{NAME} → 读 os.environ[NAME]；未设则跳过并警告
variables:
  test_mobile: "$ENV{TEST_MOBILE}"   # 整串占位符 → 读取环境变量
  app_id: "fixed-app-id"             # 普通字符串 → 原样保留
```

> 注意：仅支持 **整串** `$ENV{...}`（`fullmatch`），不支持字符串内拼接。

#### 常量

| 常量 | 值 | 说明 |
|------|----|------|
| `PROJECT_ROOT` | `Path(__file__).parent.parent` | 项目根目录绝对路径 |
| `CONFIG_FILE` | `PROJECT_ROOT / "config" / "config.yaml"` | 配置文件路径 |

---

### 4.2 http_client.py · HTTP 客户端

**文件**：[utils/http_client.py](file:///d:/pythontest/ziufileApi/utils/http_client.py)

#### 职责

- 基于 `requests.Session` 封装连接池复用
- URL 自动拼接 `base_url`（非绝对 URL 自动前缀）
- 智能重试策略（幂等安全）
- 请求/响应日志（经过 `mask_data` 脱敏后输出）

#### 重试策略（核心）

| 异常场景 | 幂等方法 (GET/HEAD/OPTIONS) | 非幂等方法 (POST/PUT/PATCH/DELETE) |
|---------|---------------------------|----------------------------------|
| **5xx 响应** | ✅ 重试 N 次 | ❌ 直接返回（防止重复提交） |
| **ConnectionError**（请求未到服务端） | ✅ 重试 N 次 | ✅ 重试 N 次 |
| **其他 RequestException**（超时等） | ✅ 重试 N 次 | ❌ 直接抛出 |

> 设计意图：幂等方法的多次执行与一次结果相同，可安全重试；非幂等方法只有请求**未到达服务端**时才能安全重试。

#### 关键类 `HttpClient`

| 方法 | 签名 | 说明 |
|------|------|------|
| `__init__` | `(base_url="", timeout=10, max_retries=None, retry_delay=None)` | 初始化 Session；重试参数为 None 时从全局 Config 读取 |
| `_retry_settings` | `() -> (int, float)` | 内部：解析实例级 / Config 级重试参数 |
| `request` | `(method, url, max_retries=None, retry_delay=None, **kwargs) -> dict` | 核心方法：发送+重试+日志，返回统一响应结构 |
| `get/post/put/delete/patch` | 便捷封装 | 对 `request` 的语义化封装 |
| `set_headers` | `(headers: dict)` | 更新 Session 默认请求头 |
| `set_cookies` | `(cookies: dict)` | 更新 Session cookies |
| `get_cookies` | `() -> dict` | 以字典返回 cookies |

#### 统一响应结构（`request` 返回值）

```python
{
    'status_code': int,        # HTTP 响应状态码
    'headers':     dict,       # 响应头 dict
    'body':        Any,        # JSON → dict/list；非 JSON → str
    'url':         str,        # 最终请求 URL
    'elapsed':     float,      # 响应耗时（秒，response.elapsed.total_seconds）
}
```

---

### 4.3 yaml_parser.py · YAML 解析器

**文件**：[utils/yaml_parser.py](file:///d:/pythontest/ziufileApi/utils/yaml_parser.py)

#### 职责

- 加载并解析 YAML 用例文件
- 兼容两种 YAML 组织形式：单接口用例（顶层含 `name/request`）与多接口集合（顶层 `testcases: []`）
- 递归做 `${var}` 变量替换；**整串占位符保留原始类型**（数字/布尔/字典/列表不会转字符串）
- **内置造数函数**：`${uuid()}` / `${timestamp()}` / `${rand_str(8)}` / `${rand_mobile()}` / `${rand_int(1,100)}`，白名单分发 + 字面量参数解析（不做动态代码执行）

#### 关键类 `YamlParser`

| 方法 | 签名 | 说明 |
|------|------|------|
| `load_file` | `(file_path: str) -> dict` | 读取 YAML；不存在抛 `FileNotFoundError` |
| `parse_test_cases` | `(file_path: str) -> List[dict]` | 统一返回用例列表；自动识别单接口/多接口形式 |
| `replace_variables` | `(data: Any, variables: dict) -> Any` | 递归：字符串 / dict / list 替换变量；其他类型原样返回 |
| `_replace_in_string` | `(text: str, variables: dict) -> Any` | 单个字符串：整串占位符保留类型，嵌入占位符做 `sub` |
| `_resolve_placeholder` / `_eval_builtin_function` | 内部 | 变量优先 → 内置函数求值 → 都未命中保留原文 |

#### 变量替换规则（核心设计）

```python
# 规则1：整串占位符 → 保留原始类型
expected: "${user_id}"    # 若作用域视图 view()["user_id"] = 123 (int) → 结果为 123 int
                          # 避免 "123" != 123 的断言误判

# 规则2：嵌入占位符 → 字符串插值
Authorization: "Bearer ${token}"   # → "Bearer xxxx"

# 规则3：未定义变量 → 保留原文 + DEBUG 日志
url: "/users/${undefined_var}"     # → "/users/${undefined_var}"

# 规则4：内置函数 → 白名单求值；未知函数/坏参数 → WARNING + 保留原文
json: { mobile: "${rand_mobile()}" }   # 同一用例内相同表达式结果一致（用例内缓存）
```

#### 常量与生成值作用域

| 常量 | 正则/说明 |
|------|------|
| `VAR_PATTERN` | `\$\{([^}]+)\}` 占位符 |
| `FUNC_PATTERN` | `^([a-zA-Z_][a-zA-Z0-9_]*)\((.*)\)$` 内置函数语法 |
| `BUILTIN_FUNCTIONS` | 函数白名单：uuid / timestamp / rand_str / rand_mobile / rand_int |
| `set_function_scope(owner)` / `clear_function_scope()` | 生成值缓存作用域：同一 owner（用例ID 或 `setup::文件`）内相同表达式返回同值，owner 变化即重置；test_executor / setup_runner 在用例与 setup 边界调用 |

---

### 4.4 assertion.py · 断言模块

**文件**：[utils/assertion.py](file:///d:/pythontest/ziufileApi/utils/assertion.py)

#### 职责

- 基于 jsonpath-ng 的响应体取值引擎
- 8 种断言方法 + 状态码断言 + **软断言汇总**
- **数据库断言**（`run_db_assertions`）：行数 / 单值 / 包含行 三种校验，复用比较符映射表
- JSONPath 表达式 LRU 缓存（`_compile_jsonpath`，maxsize=256）
- 兼容无 `$` 前缀的 JSONPath 写法
- 扩展 `$length` 路径：返回数组/字典/字符串长度

#### 关键类 `Assertion`

##### 取值方法

| 方法 | 签名 | 说明 |
|------|------|------|
| `get_value_from_jsonpath` | `(data, jsonpath) -> Any` | 取单值/列表；0 匹配抛 `AssertionError` |

`$length` 特殊路径：

```yaml
assertions:
  - type: "greater_than"
    jsonpath: "$length"   # 或 "length"
    expected: 5
    message: "列表长度大于5"
```

JSONPath 前缀兼容：
```
data.token       → 自动补 "$."  → "$.data.token"
[0].id           → 自动补 "$"   → "$[0].id"
..email          → 自动补 "$"   → "$..email"
$.data.token     → 原样
```

##### 断言方法

| 方法 | 说明 | 典型 YAML type |
|------|------|----------------|
| `assert_equal(actual, expected, msg)` | 严格相等 `!=` | `equal` |
| `assert_not_equal(...)` | 反向相等 | `not_equal` |
| `assert_contains(actual, expected, msg)` | 字符串包含 / 列表元素 / 字典键 | `contains` |
| `assert_not_contains(...)` | 反向包含 | `not_contains` |
| `assert_greater_than(a, e, msg)` | `float(a) > float(e)` | `greater_than` |
| `assert_less_than(...)` | `<` | `less_than` |
| `assert_greater_or_equal(...)` | `>=` | `greater_or_equal` |
| `assert_less_or_equal(...)` | `<=` | `less_or_equal` |
| `assert_status_code(actual, expected, msg)` | 内部调用 `assert_equal` | `status_code` |

##### 软断言 `run_assertions`

```python
def run_assertions(self, response, assertions) -> None:
```

特性：
1. **不中断执行**：逐条断言都跑一遍，任何一条失败不影响后续
2. **自动取 JSONPath**：配了 `jsonpath` 从响应体取；否则取状态码
3. **动态分派**：`assert_{type}` 通过 `getattr` 查找，未定义抛"不支持的断言类型"
4. **统一汇总**：最终若有失败则抛 `AssertionError`，内容形如：

```
共 3 条断言，失败 2 条:
  1. 检查用户ID 断言失败: 实际值 2 不等于期望值 1
  2. 检查用户名 断言失败: 实际值 'a' 不包含 'b'
```

##### 常量与比较符映射

| 常量 | 内容 | 说明 |
|------|------|------|
| `OP_METHODS` | `{"==": assert_equal, "!=": assert_not_equal, ">": assert_greater_than, ">=": assert_greater_or_equal, "<": assert_less_than, "<=": assert_less_or_equal}` | DB 断言用，把 YAML 的 `op` 字符串映射到内部断言方法 |
| `DB_ASSERT_TYPES` | `("row_count", "value", "contains_row")` | 支持的 DB 校验类型 |

##### 数据库断言 `run_db_assertions`

```python
def run_db_assertions(self, db_client, db_assertions: List[Dict]) -> None:
```

与 `run_assertions` 同风格的**软断言**：全部执行后一次性汇总失败项。

**三种校验类型**：

| type | 实际值来源 | 比较方式 | 典型字段 |
|------|-----------|---------|---------|
| `row_count` | SQL 查询结果的**行数**（`len(rows)`） | 按 `op`（默认 `==`）与 `expected` 比较 | `sql`, `op`, `expected` |
| `value` | 首行指定列的值（`column` 缺省取第一列） | 按 `op` 与 `expected` 比较 | `sql`, `column`, `op`, `expected` |
| `contains_row` | 查询结果列表（或 `column` 指定列的值列表） | 调用 `assert_contains` 检查 `expected` 在列表中 | `sql`, `column`, `expected` |

> 查询 0 行时：`row_count` 返回 0；`value` / `contains_row` 直接失败（`SQL未查询到数据`）。
> `value` 类型若 `column` 不存在于查询结果，会失败并提示实际列名。

---

### 4.5 case_collector.py · 用例收集器

**文件**：[utils/case_collector.py](file:///d:/pythontest/ziufileApi/utils/case_collector.py)

#### 职责

- 根据环境配置的 `case_data_path` 扫描所有 `.yaml/.yml`（排除 `*_template.yaml`）
- 用 **JSON Schema** 校验 setup 与 单条 case 的结构合规性
- 结构错误 / YAML 解析错误 → 生成显式失败用例（带 `_collect_error` 字段），不会静默丢失
- 注册文件级 setup 到全局字典 `FILE_SETUPS`
- **解析 `depends_on` 引用**（存在性/唯一性/自身依赖校验）并按依赖图**拓扑排序**：生产者先于消费者，跨文件依赖不依赖文件名排序；无依赖用例保持原顺序
- 生成形如 `路径::用例名` 的唯一用例 ID（重名追加 `#2`、`#3`）

#### 常量与 Schema

| 名称 | 类型 | 说明 |
|------|------|------|
| `FILE_SETUPS` | `Dict[str, dict]` | 全局注册表：`rel_path → {cache, steps}` |
| `CASE_SCHEMA` | JSON Schema | 要求 `name` + 以下四选一：`request` / `db_assertions` / `db_setup` / `extract_from_db`（纯数据库校验用例可省略 request）；允许 `tags/env/assertions/extract/db_setup/db_teardown/db_assertions/extract_from_db/depends_on/run_if` |
| `SETUP_SCHEMA` | JSON Schema | 要求 `steps[]`；可选 `cache: bool`；setup 步骤中出现 `depends_on`/`run_if` 会校验失败（无跳过语义） |

#### 关键函数

| 函数 | 签名 | 说明 |
|------|------|------|
| `get_test_case_files(config)` | `(Config) -> List[Path]` | 按文件名排序（初始顺序）；排除模板文件 |
| `_validate_schema(instance, schema)` | `(Any, dict) -> List[str]` | 返回错误列表；空列表=通过 |
| `collect_all_cases(config)` | `(Config) -> List[Tuple[str, dict]]` | 核心：返回 `(相对路径, 用例dict)` 列表；末尾调用 `resolve_and_sort` |
| `resolve_and_sort(entries)` | `(List[Tuple]) -> List[Tuple]` | 解析 depends_on 引用（改写为 `文件::用例名` 规范形式）+ 拓扑排序；引用不存在/名称不唯一/依赖自身/循环依赖 → 转为 `_collect_error` 失败用例 |
| `_entry_key(rel_path, case)` | `(str, dict) -> str` | 用例规范引用形式 `rel_path::name`（与结果注册表 key 一致） |
| `build_case_ids(entries)` | `(List[Tuple]) -> List[str]` | 生成 `rel_path::name` 唯一 ID |

#### 错误用例机制

当用例收集阶段出错时（YAML 语法错、结构错、testcases 不是列表等），会生成一条"错误用例"：

```python
(rel_path, {"name": "setup定义不合法", "_collect_error": "；".join(errors)})
```

`test_executor.py` 检测到 `_collect_error` 后立即 `pytest.fail(...)`，确保问题显式可见。

---

### 4.6 step_runner.py · 步骤执行器

**文件**：[utils/step_runner.py](file:///d:/pythontest/ziufileApi/utils/step_runner.py)

#### 职责

执行器的三件套：**准备 → 发送 → 清理**。一个"步骤"既可以是文件级 setup 的单个 step，也可以是 testcases 中的单条 case。

| 函数 | 签名 | 说明 |
|------|------|------|
| `_open_files(files_spec, base_dir)` | `(dict, Path) -> (dict, List[handle])` | 解析 YAML `files` → requests 格式；打开文件句柄；优先相对用例目录解析路径，不存在则回退项目根 |
| `prepare_step(step, variables, yaml_parser, base_dir)` | 核心：变量替换（传入作用域视图） + 组装 requests kwargs + 打开 files + 返回 attach_kwargs（报告用，内容是路径不包含句柄） |
| `send_prepared(prep, step, http_client)` | 临时覆盖 `http_client.base_url / timeout`（若用例 env 段指定）→ 调用 `http_client.request` |
| `cleanup_step(prep, http_client)` | 恢复被覆盖的 base_url/timeout；关闭所有文件句柄；多次调用安全 |

#### `files` 支持两种写法

```yaml
files:
  image: "testdata/a.png"                                     # 简写：自动取文件名
  avatar: ["testdata/a.png", "my.png", "image/png"]          # 完整：路径、文件名、Content-Type
```

`prepare_step` 返回的 `prep` 结构：
```python
{
    "method": "POST",
    "url": "/upload",
    "kwargs": {"headers": {...}, "files": {字段: (文件名, file_handle, MIME)}},
    "attach_kwargs": {"headers": {...}, "files": {原始 YAML 配置}},   # 供 Allure 附件展示
    "file_handles": [handle1, handle2],
    "_saved_env": (base_url, timeout),   # send_prepared 写入
}
```

---

### 4.7 setup_runner.py · 文件级前置执行器

**文件**：[utils/setup_runner.py](file:///d:/pythontest/ziufileApi/utils/setup_runner.py)

#### 职责

- 同一用例文件的 setup **只执行一次**（挂在该文件的**第一条用例**上执行）
- 执行成功：提取的变量写入**文件作用域层**（variable_scope，逐条即时写入，后续 setup 步骤可引用前面步骤的变量），注册脱敏 → 本文件所有用例可用
- 执行失败：该文件的后续所有用例直接失败，原因来自 `_setup_failed[case_file]`
- 跨文件缓存（`cache: true`）：**相同 steps 内容 + 相同 base_url** → 用签名命中缓存跳过执行，命中时把缓存变量导入目标文件的文件层
- 步骤断言 + 变量提取完全复用 `assertion` / `step_runner`

#### 全局状态（模块级）

| 变量 | 类型 | 说明 |
|------|------|------|
| `_setup_cache` | `Dict[tuple, dict]` | 缓存键 = `(json.dumps(steps, sort_keys), base_url)`，值 = 提取变量 dict |
| `_setup_failed` | `Dict[str, str]` | setup 失败的文件 → 错误信息 |
| `_done_files` | `set` | 已执行过 setup 的文件集合 |

#### 关键函数

| 函数 | 签名 | 说明 |
|------|------|------|
| `ensure_setup(case_file, variable_scope, http_client, assertion, yaml_parser) -> Optional[str]` | 返回 `None` 成功；返回 str = 错误信息；失败会写入 `_setup_failed`，后续同文件用例直接拿缓存错误 |

**执行顺序**：
1. `spec = FILE_SETUPS.get(case_file)` 不存在 / 已 done → 跳过
2. 计算签名 → 命中缓存且 `cache: true` → `variable_scope.import_file_layer(缓存)` → done
3. 依次执行 steps（视图 `variable_scope.view()` 按步骤实时获取）：`prepare_step` → `send_prepared` → `cleanup_step`
4. 执行断言（如有）→ 提取变量写文件层 → `register_extracted` 注册脱敏
5. 成功 → `_done_files`（cache 时存 `_setup_cache`）；失败 → `_setup_failed[case_file] = error`

> 注意：业务会改变账号状态（如注销登录）时务必不要开启 `cache: true`，否则后续文件会拿到失效 token。

---

### 4.8 masking.py · 敏感信息脱敏

**文件**：[utils/masking.py](file:///d:/pythontest/ziufileApi/utils/masking.py)

三层防护架构：

| 层级 | 实现 | 作用于 | 效果 |
|------|------|--------|------|
| 第1层 | `mask_data(data)` | 结构化字典/列表（请求参数、响应体、Allure 附件） | 深拷贝后替换敏感键值为 `******` |
| 第2层 | `MaskedDict(dict)` | pytest 失败回显 / Allure 参数记录（case 参数） | `__repr__` 输出时调用 mask_data |
| 第3层 | `register_secret / redact_text` + loguru patcher | 任意日志文本、断言消息等非结构化输出 | 全文替换已注册敏感值 |

#### 敏感键集合

- **无条件脱敏**（不区分大小写，子串匹配）：`password, passwd, pwd, token, access_token, refresh_token, authorization, secret, apikey, api_key, smscode, sms_code, verification_code, vcode, mobile, phone, telephone, idcard, id_card, cvv, cvc, cookie, set-cookie, session, sessionid`
- **条件脱敏**（值为长度 ≥ 4 的字符串时才脱敏）：`code`、`key`（兼顾业务响应码不被误脱敏）

#### 对外 API

| 函数/类 | 说明 |
|---------|------|
| `mask_data(data) -> Any` | 深拷贝 + 结构化脱敏；支持 dict/list/tuple/标量 |
| `MaskedDict` | `dict` 子类；`repr()` / `str()` 输出脱敏版 |
| `register_secret(value)` | 将一个提取到的敏感值加入文本替换集合 |
| `register_extracted(vars_dict)` | 批量：仅对键名敏感的变量调用 `register_secret` |
| `redact_text(text) -> str` | 替换文本中所有已注册敏感值；供 loguru patcher 调用 |

> 关键保证：**脱敏只影响展示层**，断言内部、请求发送一律使用真实值。

---

### 4.9 result_summary.py · 测试结果摘要

**文件**：[utils/result_summary.py](file:///d:/pythontest/ziufileApi/utils/result_summary.py)

#### 职责

解析 `reports/allure-results/*-result.json`，统计执行结果并生成两个邮件文件：

- `email_summary.txt`：纯文本 → 作为邮件**正文内嵌**
- `email_summary.html`：带颜色样式的 HTML → 作为邮件**附件**

#### 关键函数

| 函数 | 签名 | 说明 |
|------|------|------|
| `parse_results(results_dir)` | `(Path) -> (stats, failures, duration)` | 遍历 `*-result.json`；stats = {passed/failed/broken/skipped/unknown}；failures 取前 3 行失败信息（≤300 字符）；duration 根据所有 start/stop 计算 |
| `build_txt(env, stats, failures, duration) -> str` | 纯文本邮件正文模板 |
| `build_html(env, stats, failures, duration) -> str` | HTML 邮件附件模板；失败用例标红，状态数量分色显示 |
| `main()` | CLI 入口：`--results` / `--out-dir` / `--env`；存在未通过用例时退出码=1，便于流水线感知 |

#### 退出码约定

| 情况 | 退出码 |
|------|--------|
| 全部通过 | 0 |
| 存在 failed / broken 用例 | 1 |
| 结果目录不存在 / 没结果文件 | 1 |

---

### 4.10 db_client.py · 数据库客户端

**文件**：[utils/db_client.py](file:///d:/pythontest/ziufileApi/utils/db_client.py)

#### 职责

- 基于 DB-API 2.0 的轻量数据库封装，支持 **MySQL**（pymysql）和 **SQLite**（内置 sqlite3）
- **用例级连接生命周期**：由 conftest 的 `db_client` fixture 管理，每条用例独立连接、用完即关
- 懒连接：首次执行 SQL 时才建立连接，未使用 DB 功能的用例不建立连接
- 统一结果格式：查询返回 `List[Dict[列名, 值]]`，便于断言与调试
- 连接配置来自 `config.yaml` 环境段的 `db` 段，密码支持 `$ENV{NAME}` 外部化

#### 支持的驱动

| driver | 依赖 | 配置项 | 说明 |
|--------|------|--------|------|
| `mysql` | `pip install pymysql`（已在 requirements） | `host`, `port`, `user`, `password`, `database`, `charset`, `connect_timeout` | 默认 127.0.0.1:3306，charset=utf8mb4，使用 DictCursor |
| `sqlite` | Python 内置，零依赖 | `path`（相对路径按项目根解析） | 适合演示与离线验证 |

#### 关键类 `DBClient`

| 方法 | 签名 | 说明 |
|------|------|------|
| `__init__(db_config)` | `(Dict) -> DBClient` | 校验 driver；不立即建连 |
| `_connect()` | `() -> Connection` | 懒连接内部方法；按 driver 分支建立连接 |
| `query_all(sql)` | `(str) -> List[Dict]` | 执行查询，返回行列表（每行 `{列名: 值}`） |
| `query_value(sql)` | `(str) -> Optional[Any]` | 返回首行首列的标量值；无结果返回 None |
| `execute(sql)` | `(str) -> int` | 执行 DDL/DML 并提交，返回受影响行数（用 `cursor.rowcount` 兼容不同驱动返回值差异） |
| `close()` | `() -> None` | 关闭连接（多次调用安全） |

#### 常量

| 常量 | 值 | 说明 |
|------|----|------|
| `SUPPORTED_DRIVERS` | `("mysql", "sqlite")` | 非法驱动抛 `ValueError` |

> 设计要点：`execute()` 不直接返回 `cursor.execute()` 的结果（sqlite3 返回 cursor 自身、pymysql 返回 int，DB-API 不统一），统一取 `cursor.rowcount`。

---

### 4.11 dependency.py · 用例依赖与条件执行

**文件**：[utils/dependency.py](file:///d:/pythontest/ziufileApi/utils/dependency.py)

#### 职责

- 维护 **session 级用例结果注册表** `CASE_RESULTS`：`case_id基名 → "passed" / "failed" / "skipped"`，由 test_executor 在用例结束时写入
- **depends_on 判定**：上游 failed / skipped / 未执行（被 `-m`/`-k` 过滤）→ 下游 `pytest.skip` 并给出具体原因，避免带着字面量 `${var}` 产生误导性失败
- **run_if 求值**：对作用域视图（`variable_scope.view()`）中的变量按比较符判定，不满足 → skip（不是失败）

#### 常量与注册表

| 名称 | 类型 | 说明 |
|------|------|------|
| `CASE_RESULTS` | `Dict[str, str]` | 结果注册表；key 为 `rel_path::name` 基名（与 `depends_on` 规范引用一致）；conftest 收集期 `clear()` |
| `RUN_IF_OPS` | `tuple` | `eq ne gt ge lt le in not_in contains exists not_exists`（同时作为 CASE_SCHEMA 的 op 枚举） |

#### 关键函数

| 函数 | 签名 | 说明 |
|------|------|------|
| `record_result(case_id, status)` | `(str, str) -> None` | 用例结束时登记结果（test_executor 的 try/except 全路径调用） |
| `check_dependencies(case)` | `(dict) -> Optional[str]` | 返回 None=依赖满足；返回 str=应 skip 的原因（引用已在收集期规范化） |
| `evaluate_run_if(run_if, variables, yaml_parser)` | `(dict, dict, YamlParser) -> Optional[str]` | 返回 None=条件满足；`variables` 为当前用例的作用域视图；`value` 支持 `${var}`；实际值进报告前脱敏 |
| `_to_number(value)` / `_compare(actual, op, expected)` | 内部 | 数值转换（bool 视为非数值，避免 `True == 1` 意外匹配）与比较实现 |

> 设计要点：
> - 注册表只支持单进程（pytest-xdist 与 session 级变量作用域本就不兼容，既有约束）。
> - skip 语义为强依赖且**沿链传播**：A 失败 → B skip → 依赖 B 的 C 也 skip。
> - 收集期已拓扑排序，整批执行时读到的一定是上游最终结果；"未执行"分支仅在上游被圈选过滤时出现。
> - `depends_on` 在 strict 变量作用域下同时是变量传递通道（见 [4.12 variable_scope 模块](#412-variable_scopepy--变量作用域)）。

---

### 4.12 variable_scope.py · 变量作用域

**文件**：[utils/variable_scope.py](file:///d:/pythontest/ziufileApi/utils/variable_scope.py)

#### 职责

解决原先所有提取变量静默写入 session 级单一 `global_vars` 带来的同名覆盖无告警、生命周期贯穿 session、跨用例跨文件串扰问题。

**层级与解析优先级**（`view()` 从低到高逐层合并，近者优先）：

| 层级 | 写入来源 | 可见范围 |
|------|---------|---------|
| `session` | config `variables` 段预置 | 所有用例 |
| `file:<文件路径>` | 文件 setup 提取（逐条即时写入） | 本文件用例；`cache: true` 命中时导入目标文件层 |
| `chain` | 依赖闭包内上游用例产出 | 仅 depends_on 链上的下游可见（传递闭包，近的上游优先于远的） |
| `case:<用例ID>` | 用例 extract / extract_from_db | 本用例 |

#### 模式与覆盖策略（config.yaml `variable_scope` 段）

| 配置 | 取值 | 说明 |
|------|------|------|
| `mode` | `strict`（默认） | extract 产物仅本用例可见，沿 depends_on 链传播；未声明依赖引用上游变量 → `${var}` 保持字面量暴露漏声明 |
| | `shared` | 兼容旧行为：提取变量写入 session 层全局共享 |
| `overwrite` | `warn`（默认）/ `fail` / `silent` | 写入遮蔽更低层同名变量（使其在解析中不可达）时的策略；同层内重写不算覆盖 |

#### 注册表与关键 API

| 名称 | 签名 | 说明 |
|------|------|------|
| `UPSTREAM_MAP` | `Dict[case_id, List[case_id]]` | 依赖闭包表；`build_upstream_map(entries, ids)` 在收集期构建（输入为 resolve_and_sort 产出的拓扑序 + 规范引用） |
| `VariableScopes(mode, overwrite)` | 构造 | session fixture 持有；`init_session(variables)` 预置 session 层 |
| `set_context(case_id, case_file)` / `clear_context()` | — | 用例执行上下文（test_executor 进入/退出） |
| `view() -> dict` | — | 当前上下文的扁平变量视图；setup 阶段按消费点实时获取 |
| `extract(name, value, layer="case"\|"file") -> str` | — | 写入对应层并做覆盖检测，返回作用域标签供日志使用；`fail` 策略抛 `VariableOverwriteError` |
| `import_file_layer(case_file, variables)` | — | setup 缓存导入（按设计共享，不做覆盖检测） |

---

## 5. 入口与执行层

### 5.1 conftest.py · Pytest 配置与 Fixtures

**文件**：[conftest.py](file:///d:/pythontest/ziufileApi/conftest.py)

#### 关键钩子

| 钩子 | 作用 |
|------|------|
| **日志初始化**（模块顶层） | `logger.remove() → logger.configure(patcher=redact_text)` → 双 sink：文件（100MB 滚动 / 7天保留）+ 控制台彩色输出 |
| `pytest_addoption(parser)` | 注册自定义组 `ziufile-api`：<br>`--env`（环境名）、`--confirm-prod`（正式环境确认开关） |
| `pytest_generate_tests(metafunc)` | 核心：只对 `case` fixture 生效 → 调用 `collect_all_cases`（含 depends_on 解析+拓扑排序）+ `build_case_ids` → 清空 `CASE_RESULTS` + `build_upstream_map`（依赖闭包表，收集先于执行，安全）→ 用 `pytest.param(rel_path, MaskedDict(case), case_id, id=..., marks=...)` 三值参数化（case_id 透传给执行器登记结果）。<br>**tags → markers 映射**：用例 tags 与 pytest.ini 中注册的 marker 同名者自动挂对应 pytest mark，支持 `-m smoke` 圈选。<br>**MaskedDict**：参数对象 repr 脱敏，防止 pytest 失败回显/Allure 参数泄漏。 |

#### Fixtures

| Fixture | Scope | 说明 |
|---------|-------|------|
| `variable_scope` | **session** | `VariableScopes` 实例（模式/覆盖策略来自 `get_config().variable_scope_config`）；预置变量写入 session 层并注册脱敏；用例间通过 case/链路/文件分层实现变量传递（见 4.12） |
| `http_client` | **function** | 每个用例独立实例，避免 case 级 `env` 覆盖相互污染；结束自动 `session.close()` |
| `yaml_parser` | function | YamlParser 实例 |
| `assertion` | function | Assertion 实例 |
| `db_client` | **function** | 数据库客户端；环境未配置 `db` 段时返回 `None`，用例若使用了 `db_*` 字段会在执行时明确报错；配置后每条用例独立 `DBClient` 实例，结束自动 `close()` |
| `clear_allure_results` | session / autouse | 按 allure.clean 开关清理 `reports/allure-results/*` |

---

### 5.2 test_executor.py · 用例执行主体

**文件**：[testcases/test_executor.py](file:///d:/pythontest/ziufileApi/testcases/test_executor.py)

#### `test_api_executor(case_file, case, case_id, yaml_parser, http_client, assertion, variable_scope, db_client)`

**执行顺序**：依赖判定(depends_on) → 条件判定(run_if) → 文件级 setup → `db_setup` → 请求(可选) → 接口断言(可选) → `db_assertions` → `extract` / `extract_from_db` → `finally: db_teardown`

**结果登记**：执行主体提取到 `_execute_case`；外层 try/except 按退出路径登记 `case_id` 结果——正常返回 → passed；`pytest.skip.Exception` → skipped；`pytest.fail.Exception` 及其他异常 → failed（供下游 depends_on 判定）。

**执行流程**（每条参数化用例走一次）：

```
0. _collect_error 检测 → 有则立即 pytest.fail
0.1 variable_scope.set_context(case_id, case_file)   进入用例作用域上下文（finally clear_context）
0.5 依赖判定：check_dependencies → 上游 failed/skipped/未执行 → pytest.skip（带原因）
0.6 条件判定：run_if 对 variable_scope.view() 求值 → 不满足 → pytest.skip（带原因）
1. Allure 动态打标
     title       = case.name
     description = case.description
     labels      = case_file, env
     tags        = case.tags
2. allure.step("执行文件前置步骤(setup)")
     → setup_runner.ensure_setup(...)（提取写入文件作用域层）
     → 失败则 pytest.fail（同文件后续用例直接命中 _setup_failed 缓存）
3. 断言期望值变量替换：assertions = replace_variables(case.assertions, variable_scope.view())
4. db_setup（可选）：_require_db 检查 → 逐条 SQL 执行（支持 ${var}），attach SQL 与影响行数
5. try:
     请求(可选，纯 DB 用例可无 request)：
       allure.step("发送请求") →
         attach 脱敏请求参数 JSON
         response = send_prepared(...)
         attach 状态码 / 脱敏响应体 JSON
       finally: cleanup_step（确保文件句柄关闭、env 恢复）
6. 接口断言（可选）→ assertion.run_assertions（软断言）
7. db_assertions（可选）：_require_db 检查 → assertion.run_db_assertions（软断言）
     → 每条校验 SQL 的查询结果脱敏后 attach 到 Allure
8. extract（可选，需 response 非空）：
     allure.step("提取变量")
       for var_name, jsonpath:
           variable_scope.extract(var_name, 取值)   写入用例作用域层（含覆盖检测）
           register_extracted（敏感键注册到文本替换）
           log & attach 脱敏后的 key=value（含作用域标签）
9. extract_from_db（可选）：_require_db 检查 → 每条 SQL 取首行首列写入用例作用域层
10. finally: db_teardown（可选）：无论断言成败都执行，防止数据残留
     → 清理失败记录 teardown_error，最终 pytest.fail 提示数据可能残留
```

> 设计要点：
> - `_require_db`：环境未配置 `db` 段时，使用了 `db_*` 字段的用例立即 `pytest.fail` 并给出补充配置的明确指引。
> - `db_setup` 用独立 try（不在大 try 内）：前置造数失败应直接终止用例，不进入请求阶段。
> - `db_teardown` 在 finally 中执行，且清理失败不吞掉原始断言失败（用 `teardown_error` 单独记录，原始异常继续传播）。
> - 纯数据库校验用例可省略 `request` 字段，此时 `response=None`，`extract` 自动跳过。
> - 结果登记覆盖全部退出路径（passed/failed/skipped），setup 失败、依赖 skip、run_if skip 均会被下游 depends_on 正确感知。

---

### 5.3 run_test.py · 统一运行脚本

**文件**：[run_test.py](file:///d:/pythontest/ziufileApi/run_test.py)

| 函数 | 说明 |
|------|------|
| `install_dependencies()` | `pip install -r requirements.txt` |
| `clean_allure_results()` | 删除 allure-results 下旧文件 |
| `run_tests(test_path, allure_clean, env, confirm_prod)` | 组装 pytest args → `pytest.main(args)`；返回 bool |
| `generate_allure_report()` | `allure generate ... --clean`；未装 Allure 给出安装指引 |
| `open_allure_report()` | `allure open` 启动本地预览 |
| `main()` | argparse 入口：`-i/-r/-g/-o/-a/--test-path/--no-clean/-e/--confirm-prod` |

无参默认行为：跑测试 → 成功则生成报告。

---

### 5.4 run_test.bat · Windows 菜单式批处理

**文件**：[run_test.bat](file:///d:/pythontest/ziufileApi/run_test.bat)

交互菜单（chcp 65001 防止中文乱码）：

| 选项 | 动作 |
|------|------|
| 1 | `pip install -r requirements.txt` |
| 2 | `pytest --alluredir=reports/allure-results --clean-alluredir -v -s` |
| 3 | `allure generate ...` |
| 4 | `allure open` |
| 5 | 完整流程：1→2→3→4（任一步失败中断） |
| 6 | 退出 |

---

## 6. 依赖关系

### 6.1 第三方依赖

**文件**：[requirements.txt](file:///d:/pythontest/ziufileApi/requirements.txt)

| 包 | 版本（未锁，pip 解析最新兼容） | 用途 | 被谁使用 |
|----|------------------------------|------|----------|
| `pytest` | 最新 | 测试引擎 + 参数化 + marker + conftest 机制 | conftest.py / test_executor.py / run_test.py |
| `requests` | 最新 | HTTP 请求（Session、连接池） | http_client.py |
| `pyyaml` | 最新 | YAML 加载与解析 | config.py / yaml_parser.py / case_collector.py / conftest.py |
| `allure-pytest` | 最新 | Pytest 生成 Allure 原始结果 JSON；提供 `allure.attach/dynamic.*` | conftest.py / test_executor.py |
| `loguru` | 最新 | 结构化日志；支持 patcher（脱敏注入） | 所有 .py 模块 |
| `jsonschema` | 最新 | 校验 YAML 用例/setup 结构合规性 | case_collector.py |
| `jsonpath-ng` | 最新 | JSONPath 取值引擎（支持 find + compile） | assertion.py |
| `pymysql` | 最新 | MySQL 驱动（仅当 `driver: mysql` 时使用，懒加载 import） | db_client.py |

### 6.2 内部模块依赖图

```
                    ┌────────────────┐
                    │   config.py    │   (零内部依赖，基石)
                    └───────┬────────┘
                            │ 被引用
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐  ┌──────────────────┐  ┌───────────────┐
│ masking.py   │  │ case_collector.py│  │ http_client.py│
│ (零内部依赖) │  │   │              │  │   │           │
└───────┬──────┘  │   ▼              │  │   ▼           │
        │         │ yaml_parser.py   │  │ masking.py    │
        │         │   config.py      │  └───────────────┘
        │         └───────┬──────────┘
        │                 │
        ▼                 ▼
┌──────────────────────────────────────┐
│      step_runner.py                  │
│  yaml_parser + config + masking(间接)│
└───────────────┬──────────────────────┘
                │
    ┌───────────┼──────────────┐
    ▼           ▼              ▼
setup_runner  assertion.py  test_executor
    │       (jsonpath-ng独立)    │
    │   masking(register_extract)│
    └─────────────┬──────────────┘
                  ▼
          conftest.py（编排全部模块）
                  │
                  ▼
    run_test.py  →  pytest.main()  →  test_executor

result_summary.py   ← 独立模块，直接读 allure-results JSON

db_client.py        ← 仅依赖 config.PROJECT_ROOT；被 conftest / test_executor 通过 fixture 注入

dependency.py       ← 仅依赖 masking（skip消息脱敏）；被 case_collector（RUN_IF_OPS 枚举）/
                       conftest（清空注册表）/ test_executor（登记结果+判定）引用

variable_scope.py   ← 无内部依赖（仅 loguru）；被 conftest（构建闭包表+session fixture）/
                       test_executor（上下文+提取）/ setup_runner（文件层写入）引用
```

**依赖表（谁 import 谁）**：

| 模块 | 内部 import |
|------|-------------|
| config.py | （无） |
| masking.py | （无） |
| yaml_parser.py | （无） |
| variable_scope.py | （无） |
| http_client.py | masking.mask_data；config.get_config（懒加载） |
| assertion.py | （无；第三方 jsonpath-ng） |
| dependency.py | masking.mask_data |
| case_collector.py | config.PROJECT_ROOT/Config；yaml_parser.YamlParser；dependency.RUN_IF_OPS；（第三方 jsonschema） |
| step_runner.py | config.PROJECT_ROOT；yaml_parser.YamlParser |
| setup_runner.py | case_collector.FILE_SETUPS；config.PROJECT_ROOT；masking（mask_data/register_extracted）；step_runner（全部） |
| result_summary.py | （无；标准库 argparse/json/html/pathlib） |
| db_client.py | config.PROJECT_ROOT；pymysql（懒加载，仅 mysql 驱动） |
| conftest.py | utils.http_client / yaml_parser / assertion / config / case_collector / dependency / masking / db_client（懒加载） |
| testcases/test_executor.py | utils.setup_runner / config / masking / step_runner / dependency |
| run_test.py | （调用 pytest.main；无直接 import utils） |

---

## 7. 配置与环境

### 7.1 config/config.yaml

**文件**：[config/config.yaml](file:///d:/pythontest/ziufileApi/config/config.yaml)

```yaml
default_env: "client-dev"          # 未指定 --env/TEST_ENV 时使用

environments:
  client-dev:
    base_url: "https://www.ziulife.com/client-api-dev/client"
    caseData_path: "data/client_data"
    db:                              # 可选：数据库连接配置（无则用例的 db_* 字段会失败并提示）
      driver: mysql                  # mysql / sqlite
      host: "127.0.0.1"
      port: 3306
      user: "test_rw"
      password: "$ENV{DB_PASSWORD}"  # 敏感信息外部化到环境变量
      database: "client_dev"
      charset: "utf8mb4"
  client-prod:
    base_url: "https://www.ziulife.com/client-api-prod/client"
    caseData_path: "data/client_data"
    prod: true                     # 标记正式环境
  station-dev:
    base_url: "https://www.ziulife.com/station-api-dev"
    caseData_path: "data/station_data"
  station-prod:
    base_url: "https://www.ziulife.com/station-api-prod"
    caseData_path: "data/station_data"
    prod: true

timeout: 30                        # 请求超时（秒）
retry_times: 3                     # 重试次数（不含首次请求）
retry_delay: 2.0                   # 重试间隔（秒）

variables: {}                      # 预置变量，支持 $ENV{NAME}
# variables:
#   test_mobile: "$ENV{TEST_MOBILE}"

log:
  level: "INFO"
  file_path: "logs/api_test.log"

allure:
  report_dir: "reports/allure-results"
  clean: true
```

> **db 段说明**：
> - `driver: sqlite` 时只需 `path` 一个参数（Python 内置驱动，零依赖，适合演示/离线验证），相对路径按项目根解析。
> - `driver: mysql` 时需安装 `pymysql`（已在 requirements.txt）。
> - 密码等敏感值支持 `$ENV{NAME}` 引用系统环境变量，未设置时该键不生效并打 WARNING 日志。
> - 环境未配置 `db` 段时，用例若使用了 `db_setup`/`db_assertions`/`extract_from_db`/`db_teardown` 字段，会在执行时 `pytest.fail` 并提示补充配置。

**环境选择优先级（高→低）**：
1. CLI：`pytest --env station-dev` 或 `python run_test.py -e station-dev`
2. 系统环境变量：`TEST_ENV=station-dev`
3. `config.yaml` 中 `default_env`

### 7.2 pytest.ini

**文件**：[pytest.ini](file:///d:/pythontest/ziufileApi/pytest.ini)

```ini
[pytest]
testpaths = testcases
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    smoke: 冒烟测试用例
    regression: 回归测试用例
    api: API测试用例
addopts = -v -s --alluredir=reports/allure-results --clean-alluredir
filterwarnings = ignore::DeprecationWarning
```

**tags → marker 映射**：YAML `tags: ["smoke", "用户管理"]`，其中 `smoke` 已在 markers 注册 → 自动挂 `pytest.mark.smoke` → 支持 `pytest -m smoke`。

### 7.3 环境变量

| 变量 | 作用 |
|------|------|
| `TEST_ENV` | 等效于 `--env`；优先级低于命令行 |
| `ALLOW_PROD=1` | 等效于 `--confirm-prod`；CI 中直接设置即可启用正式环境 |
| `TEST_MOBILE` 等（自定义） | 通过 `variables.test_mobile: "$ENV{TEST_MOBILE}"` 注入预置变量 |
| `PATH`（运行时） | 需能找到 `python` 与 `allure`（Jenkinsfile 中 PYTHON_EXE / ALLURE_EXE 可改为绝对路径） |

---

## 8. YAML 用例规范

### 8.1 单接口用例

整个 YAML 文件就是一条用例：

```yaml
name: "示例接口测试"                 # 必须
description: "说明"                 # 可选
tags: ["示例", "GET", "smoke"]      # 可选；含 marker 名的 tag 支持 -m 圈选

env:                                # 可选，覆盖本用例全局 base_url/timeout
  base_url: "https://example.com"
  timeout: 15

request:                            # 必须
  method: "GET"                     # 必须
  url: "/users"                     # 必须；非 http(s) 开头会自动拼接 base_url
  params:   { page: 1, size: 10 }  # 可选，query string
  headers:  { Authorization: "Bearer ${token}" }  # 可选
  json:     { key: "value" }        # 可选，JSON Body
  body:     "form data"             # 可选，raw body (与 json/files 互斥)
  files:
    image: "testdata/a.png"

assertions: []                      # 可选（空数组会打 WARNING 日志）
extract:                            # 可选
  user_id: "data.id"
```

### 8.2 多接口用例集

```yaml
description: "..."
tags: ["..."]
testcases:
  - name: "用例1"
    request: { ... }
    assertions: [...]
    extract:
      token: "data.token"
  - name: "用例2（引用上一步token）"
    depends_on: ["用例1"]             # ${token} 沿依赖链传递；未声明则不可见（strict 作用域）
    request:
      headers: { Authorization: "Bearer ${token}" }
    ...
```

### 8.3 文件级前置步骤 setup

```yaml
setup:
  cache: false                      # 跨文件缓存（同steps内容+同base_url命中）
  steps:
    - name: "登录（前置）"
      request:
        method: POST
        url: /appUser/codeLogin
        json: { mobile: "19999999999", code: "000000" }
      extract:
        token: data.token
      # assertions 可选（setup 里通常用 extract 成功与否即隐含校验）

testcases:
  - name: "获取用户信息"
    request:
      headers: { Authorization: "Bearer ${token}" }   # token 来自 setup
    ...
```

执行语义：同文件所有用例中，仅**第一条被 Pytest 执行时**触发 setup；该文件后续用例跳过 setup，直接复用文件作用域层的变量。若 setup 失败，该文件所有用例直接失败，原因会被缓存。

### 8.4 变量提取与引用

变量按分层作用域管理（详见 [4.12 variable_scope 模块](#412-variable_scopepy--变量作用域)）：

| 方式 | 示例 | 生效范围 |
|------|------|----------|
| `extract:` + `depends_on` 依赖链 | 用例1 `extract.user_id = data.id` → 下游 `depends_on` 后 `${user_id}` | 本用例 + 沿依赖链的下游（传递闭包，跨文件依赖同样生效） |
| 文件 `setup` 提取 | setup `extract.token` → 本文件用例 `${token}` | **本文件**所有用例（文件作用域）；`cache: true` 命中时同样导入目标文件层 |
| `config.yaml variables` 段 + `$ENV{}` | `test_mobile: "$ENV{TEST_MOBILE}"` → 用例中 `${test_mobile}` | 所有用例（session 层） |
| 内置造数函数 | `${uuid()}` / `${timestamp()}` / `${rand_str(8)}` / `${rand_mobile()}` / `${rand_int(1,100)}` | 当前用例内生成且**相同表达式结果稳定**，跨用例重新生成（见 4.3） |
| 整串占位符保留类型 | `expected: "${count}"` 其中 count=5 int → 比较时仍为 int | 断言 expected 中常用 |
| 嵌入占位符做字符串插值 | `"Bearer ${token}"` | URL / Header / JSON 值中任意位置 |

未声明 `depends_on` 却引用上游变量：`${var}` 保持字面量原样发出（strict 模式默认行为，立即暴露漏声明的依赖）。同名覆盖默认告警（`variable_scope.overwrite: warn`，可配 `fail`/`silent`）。

### 8.5 文件上传 files

```yaml
files:
  # 简写：自动取文件名，MIME 由 requests 推断
  image: "testdata/a.png"
  # 完整：[路径, 上传时文件名, Content-Type]（后两个可选）
  avatar: ["testdata/b.png", "custom_name.png", "image/png"]
```

相对路径先按**用例文件所在目录**解析，找不到再回退项目根目录，避免 `data/client_data/x.yaml` 引用 `data/client_data/testdata/a.png` 出错。

### 8.6 断言类型一览

| type | 说明 | 必配字段 |
|------|------|----------|
| `status_code` | 响应状态码相等 | `expected`（int） |
| `equal` | JSONPath 取值严格相等 | `jsonpath`, `expected` |
| `not_equal` | 严格不相等 | 同上 |
| `contains` | 包含（str包含子串/list包含元素/dict包含键；fallback 转字符串） | 同上 |
| `not_contains` | 反向包含 | 同上 |
| `greater_than` | 数值 > | 同上；值可转 float |
| `less_than` | < | 同上 |
| `greater_or_equal` | >= | 同上 |
| `less_or_equal` | <= | 同上 |

> 断言中的 `expected` 同样支持 `${var}` 变量替换，且整串占位符保留类型。

### 8.7 JSONPath 语法

底层 `jsonpath-ng`，前缀 `$` 可省：

| 写法 | 含义 |
|------|------|
| `data.token` / `$.data.token` | 子字段 |
| `[0].id` / `$[0].id` | 数组索引 |
| `$..email` | 所有层级递归查找 |
| `$[*].id` | 数组所有元素 id |
| `$length` / `length` | 数组/字典/字符串长度（扩展语法） |

匹配 0 项 → 断言失败；1 项 → 返回该值；多项 → 返回列表，与 `expected` 比较。

### 8.8 数据库连接与校验

框架支持在用例中直接操作数据库，适用于"接口调用后校验数据是否正确落库"、"前置造数"、"清理测试数据"等场景。

#### 第一步：环境配置

在 `config/config.yaml` 对应环境下增加 `db` 段（密码建议用 `$ENV{}` 外部化）：

```yaml
environments:
  client-dev:
    base_url: "https://..."
    caseData_path: "data/client_data"
    db:
      driver: mysql                  # mysql / sqlite
      host: "127.0.0.1"
      port: 3306
      user: "test_rw"
      password: "$ENV{DB_PASSWORD}"  # 敏感信息外部化
      database: "client_dev"
      charset: "utf8mb4"
```

- `driver: sqlite`：只需 `path` 参数（Python 内置驱动，零依赖，适合演示/离线验证）。
- `driver: mysql`：需安装 `pymysql`（已在 requirements.txt）。

#### 第二步：用例中编写 DB 步骤

```yaml
testcases:
  - name: "创建用户后校验落库"
    request:                          # 接口调用（纯数据库用例可省略 request）
      method: "POST"
      url: "/user/create"
      json: { mobile: "${test_mobile}" }
    extract:
      new_user_id: "data.id"

    db_setup:                         # 前置：请求前执行（建表/造数），支持 ${var}
      - "DELETE FROM t_user WHERE mobile = '${test_mobile}'"

    db_assertions:                    # 请求后执行的数据校验（软断言，失败汇总）
      - type: "row_count"             # 行数校验
        sql: "SELECT id FROM t_user WHERE mobile = '${test_mobile}'"
        op: ">="                      # 支持 == != > >= < <=
        expected: 1
        message: "用户应落库"
      - type: "value"                 # 单值校验（默认取首行第一列，可用 column 指定列名）
        sql: "SELECT status FROM t_user WHERE mobile = '${test_mobile}'"
        expected: "active"
        message: "用户状态应为active"
      - type: "contains_row"          # 查询结果包含（整行字典列表 或 column 指定列的值列表）
        sql: "SELECT role FROM t_user WHERE mobile = '${test_mobile}'"
        column: "role"
        expected: "admin"

    extract_from_db:                  # 从库中提取变量（取首行首列），后续用例可用 ${db_user_id}
      db_user_id: "SELECT id FROM t_user WHERE mobile = '${test_mobile}'"

    db_teardown:                      # 清理：无论断言成败都执行，防止数据残留
      - "DELETE FROM t_user WHERE mobile = '${test_mobile}'"
```

#### 执行顺序

```
文件级 setup → db_setup → 请求(可选) → 接口断言(可选) → db_assertions
              → extract / extract_from_db → finally: db_teardown
```

#### 规则说明

| 规则 | 说明 |
|------|------|
| **时序** | `db_setup` 在请求**之前**执行；若需引用接口返回变量做 DB 校验（如落库校验），正常写在请求后的 `db_assertions` 即可；若需在 `db_setup` 中引用接口变量，请拆成两条用例跨用例传参 |
| **变量替换** | 所有 SQL 均支持 `${var}` 变量替换；`db_assertions` 的 `expected` 整串占位符保留原始类型 |
| **软断言** | `db_assertions` 多条校验全部执行，失败项一次性汇总（与接口断言同风格） |
| **未配置 db** | 环境未配置 `db` 段时，用例使用了 `db_*` 字段会立即 `pytest.fail` 并提示补充配置 |
| **连接生命周期** | 用例级：每条用例独立 `DBClient` 实例，用完即关（`db_client` fixture 的 function scope） |
| **db_teardown** | 在 `finally` 中执行，无论断言成败都跑；清理失败会单独 `pytest.fail` 提示数据可能残留，但不吞掉原始断言失败 |
| **离线演示** | 使用 `driver: sqlite` 可在无数据库环境下验证 DB 校验逻辑 |

#### db_assertions 三种校验类型

| type | 实际值 | 比较方式 | 字段 |
|------|--------|---------|------|
| `row_count` | SQL 查询结果行数 | 按 `op`（默认 `==`）与 `expected` 比较 | `sql`, `op`, `expected` |
| `value` | 首行 `column` 列的值（缺省第一列） | 按 `op` 与 `expected` 比较 | `sql`, `column`, `op`, `expected` |
| `contains_row` | 查询结果列表（或 `column` 指定列的值列表） | `assert_contains(actual, expected)` | `sql`, `column`, `expected` |

### 8.9 用例依赖与条件执行

跨用例传参（`extract` + `${var}`）解决"数据从哪来"，`depends_on` / `run_if` 解决"什么时候该执行"。strict 作用域下 `depends_on` 同时是变量传递通道：传递闭包内上游的 extract 产物对本用例可见。

#### depends_on：显式依赖声明

```yaml
testcases:
  - name: "3. 创建订单"
    depends_on:                           # 可依赖多条，全部 passed 才执行
      - "1. 创建收货地址"                  # 用例名引用（全局唯一时）
      - "data/client_data/goods.yaml::2. 查询商品"   # 重名/跨文件用 文件相对路径::用例名
    request: { method: "POST", url: "/order/create" }
```

| 规则 | 说明 |
|------|------|
| 强依赖 | 上游 failed / skipped（含上游 run_if 不满足、再上游失败）/ 未执行 → 本用例 `pytest.skip`，原因写入报告（`-rs` 查看） |
| skip 沿链传播 | A 失败 → B skip → 依赖 B 的 C 也 skip |
| 执行顺序 | 收集期按依赖图**拓扑排序**，生产者一定先于消费者，跨文件依赖不依赖文件名排序；无依赖用例保持文件名+书写顺序 |
| 收集期校验 | 引用不存在 / 名称不唯一 / 依赖自身 / 循环依赖 → 转为一条失败用例并给出具体原因（循环依赖列出环上所有用例） |
| 圈选过滤 | `-m` / `-k` 把上游过滤掉时，下游以"依赖的用例 [...] 未执行"skip 而非报错 |
| 适用范围 | 仅 `testcases` 用例；`setup` 步骤中写会校验失败（无跳过语义） |

#### run_if：条件执行

```yaml
  - name: "4. 支付订单"
    run_if:
      var: sku_price        # 取自作用域视图（本用例 / 链路上游 / 文件setup / 预置变量）
      op: gt                # 默认 eq
      value: 0              # 支持 ${var} 引用其他变量
```

| op | 说明 |
|----|------|
| `eq` / `ne` | 相等 / 不相等（严格比较，注意 YAML 类型：`"1"` ≠ `1`） |
| `gt` / `ge` / `lt` / `le` | 数值比较（两侧需为数值或数值字符串；bool 不参与数值比较） |
| `in` / `not_in` | `value` 需为列表 |
| `contains` | 实际值（str/list/dict）包含期望值 |
| `exists` / `not_exists` | 变量是否存在（无需 `value`） |

不满足时 skip（不是失败），skip 原因中的实际值自动脱敏。判定发生在依赖判定之后、文件 setup 之前。

> 完整示例：`data/case_template/dependency_chain_test.yaml`；实现细节见 [4.11 dependency 模块](#411-dependencypy-用例依赖与条件执行)。

---

## 9. 项目运行方式

### 9.1 环境准备

1. **Python 3.8+** 并加入 PATH
2. 安装依赖：
   ```powershell
   cd d:\pythontest\ziufileApi
   pip install -r requirements.txt
   ```
3. **Allure 命令行工具**（生成报告需要）：
   - 下载 https://github.com/allure-framework/allure2/releases
   - 解压后把 `bin` 加入 `PATH`；`allure --version` 验证
4. （可选）设置环境变量 `TEST_MOBILE` 等，供 `$ENV{}` 读取

### 9.2 本地运行

**方式 A：统一 Python 脚本（推荐）**
```powershell
# 无参默认：运行测试 + 生成报告
python run_test.py

# 指定环境
python run_test.py -e station-dev

# 正式环境
python run_test.py -e client-prod --confirm-prod

# 仅安装依赖 / 仅生成报告 / 全部+打开
python run_test.py -i
python run_test.py -g
python run_test.py -a
```

**方式 B：Windows 菜单**
```powershell
.\run_test.bat
```

**方式 C：原生 Pytest**
```powershell
python -m pytest testcases/test_executor.py -v -s --env client-dev
python -m pytest -m smoke --env station-dev
python -m pytest "testcases/test_executor.py::example_test.yaml::获取单个用户信息" -v -s
```

### 9.3 命令行参数

| Pytest 参数（conftest 注册） | 说明 |
|----|----|
| `--env NAME` | 切换环境 |
| `--confirm-prod` | 正式环境确认开关 |
| 标准 pytest 参数：`-v/-s/-m/-k/-x/--alluredir/--clean-alluredir` | 同 Pytest |

| run_test.py argparse | 说明 |
|----|----|
| `-i / --install` | 安装依赖 |
| `-r / --run` | 运行测试 |
| `-g / --generate` | 生成 Allure 报告 |
| `-o / --open` | 打开 Allure 报告 |
| `-a / --all` | 完整流程：i→r→g→o |
| `--test-path PATH` | 指定测试文件/目录（默认 testcases/test_executor.py） |
| `--no-clean` | 不清空 allure-results |
| `-e / --env NAME` | 切换环境 |
| `--confirm-prod` | 正式环境确认 |

### 9.4 Allure 报告

```powershell
# 生成静态报告
allure generate reports/allure-results -o reports/allure-report --clean

# 启动本地预览服务器
allure serve reports/allure-results
# 或打开静态报告目录
allure open reports/allure-report
```

附件内容（均脱敏）：请求参数、响应状态码、响应体、提取变量键值。

---

## 10. Jenkins CI/CD

**文件**：[Jenkinsfile](file:///d:/pythontest/ziufileApi/Jenkinsfile)

### 10.1 流水线参数

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `ENV` | choice | client-dev | client-dev / station-dev / client-prod / station-prod |
| `CONFIRM_PROD` | boolean | false | 正式环境必须勾选 |
| `RECIPIENTS` | text | 空 | 邮件收件人，英文逗号分隔；空时发给触发者/订阅者 |
| `PYTEST_ARGS` | string | 空 | 附加 pytest 参数，如 `-m smoke` |

### 10.2 Stages 顺序

1. **准备依赖**：创建 `.venv-ci` → 清华镜像装 requirements → pip list
2. **运行测试**：`returnStatus: true` 保证失败也继续，记录 `env.TEST_RC`
3. **生成Allure报告**：`allure generate ... --clean`（允许失败不中断）
4. **生成邮件摘要**：`python utils/result_summary.py --env XXX` → 产出 email_summary.txt / .html
5. **归档产物**：打 allure-report.zip → 归档 4 个文件：email_summary.txt / .html / allure-report.zip / logs/api_test.log
6. **标记构建结果**：按 TEST_RC 标记 SUCCESS / FAILURE

### 10.3 Post

- `always`：发送邮件；主题 `[接口自动化][ENV] 构建#N - SUCCESS/FAILURE`；正文内嵌 email_summary.txt；附件 3 项：html 明细 / allure-report.zip / api_test.log；收件人：`RECIPIENTS` + requestor() + developers()
- `cleanup`：`rmdir /s /q .venv-ci`（每次构建重建）
- **注意**：流水线用 `customWorkspace 'D:\\pythontest\\ziufileApi'` 指向项目目录（非 SCM），**绝不能**调用 `deleteDir()`，否则项目源文件被删。后续改用 SCM Pipeline script from SCM 时删除 customWorkspace 行即可。

---

## 11. 扩展开发指南

### 11.1 新增断言类型

在 [utils/assertion.py](file:///d:/pythontest/ziufileApi/utils/assertion.py)：

```python
def assert_regex_match(self, actual, expected: str, message: str = "") -> None:
    import re
    if not re.search(expected, str(actual)):
        raise AssertionError(f"{message} 断言失败: {actual!r} 不匹配正则 {expected!r}")
    logger.info(f"{message} 断言成功")
```

YAML 中直接用：
```yaml
assertions:
  - type: "regex_match"
    jsonpath: "data.orderNo"
    expected: "^ORD\\d{14}$"
    message: "订单号格式"
```

`run_assertions` 会通过 `getattr(self, "assert_regex_match")` 自动找到，无需其他改动。

### 11.2 新增预置变量解析规则

在 [utils/config.py](file:///d:/pythontest/ziufileApi/utils/config.py) `Config.variables` property 中扩展 `_ENV_VAR_PATTERN` 类似分支即可。若要支持 `${ENV:NAME}` 或内嵌拼接，同步扩展正则和逻辑。

### 11.3 新增脱敏键

直接在 [utils/masking.py](file:///d:/pythontest/ziufileApi/utils/masking.py) `SENSITIVE_KEYS` / `CONDITIONAL_KEYS` 添加，匹配方式为**子串匹配**且不区分大小写。

### 11.4 新增 HTTP 认证/签名插件

在 [utils/http_client.py](file:///d:/pythontest/ziufileApi/utils/http_client.py) `HttpClient.__init__` 或在 `request()` 发请求前做 kwargs 预加工（例如加上 timestamp + sign），或者为 HttpClient 增加 `register_hook(callback)` 机制即可。

### 11.5 YAML 结构校验扩展

[utils/case_collector.py](file:///d:/pythontest/ziufileApi/utils/case_collector.py) 中 `CASE_SCHEMA` 允许新增属性，例如 `sleep_ms: {type: number}` 后，在 `step_runner.send_prepared` 前 `time.sleep(step.get("sleep_ms", 0))` 即可实现用例间等待。

---

## 12. 常见问题 FAQ

### Q1. `ConfigError: 环境 [client-prod] 标记为正式环境！`
A：命令行追加 `--confirm-prod` 或设置环境变量 `ALLOW_PROD=1`。CI 中直接在任务里勾选 CONFIRM_PROD 参数。

### Q2. YAML 里 `${user_id}` 替换后成了字符串 "123"，断言报错 "123" != 123？
A：确保写的是整串占位符 `expected: "${user_id}"` 而非 `expected: "id=${user_id}"`（后者是插值）。整串占位符会保留变量原始类型。

### Q3. setup 里拿的 token 过一会报失效？
A：检查 YAML 顶部 `setup.cache: true` 是否开了。若文件间存在注销/登出等改变账号状态的操作，必须关掉缓存。

### Q4. Jenkins 里报 `python 不是内部命令` 或 `allure 不是内部命令`？
A：编辑 Jenkinsfile 顶部 `environment`，把 `PYTHON_EXE` / `ALLURE_EXE` 改为安装绝对路径（注释里有示例）。

### Q5. Allure 报告里 token/手机号仍是明文？
A：检查字段 key 是否在 `masking.SENSITIVE_KEYS` 的子串命中范围；提取到的自定义敏感字段可在 setup / extract 时确保 key 命名包含 `token`、`mobile` 等即可自动走 `register_extracted`。

### Q6. 一条 YAML 里多个用例失败，但只想看到某条失败原因？
A：用 Pytest 按用例 ID 单独执行：
```
python -m pytest "testcases/test_executor.py::data/client_data/login_test.yaml::验证用户登录" -v -s
```
ID 可在首次跑失败的 pytest 输出中看到。

### Q7. 日志体积太大？
A：修改 `config.yaml → log.level` 为 `WARNING`，或调小 `rotation`（已默认 100MB 滚动 + 7 天保留，见 conftest.py logger.add 参数）。

---

## 附录：关键文件速查表

| 名称 | 路径 |
|------|------|
| 全局配置 | [config/config.yaml](file:///d:/pythontest/ziufileApi/config/config.yaml) |
| Pytest 配置 | [pytest.ini](file:///d:/pythontest/ziufileApi/pytest.ini) |
| Pytest 钩子 + Fixtures | [conftest.py](file:///d:/pythontest/ziufileApi/conftest.py) |
| 用例执行函数 | [testcases/test_executor.py](file:///d:/pythontest/ziufileApi/testcases/test_executor.py) |
| 配置模块 | [utils/config.py](file:///d:/pythontest/ziufileApi/utils/config.py) |
| HTTP 客户端 | [utils/http_client.py](file:///d:/pythontest/ziufileApi/utils/http_client.py) |
| YAML 解析 | [utils/yaml_parser.py](file:///d:/pythontest/ziufileApi/utils/yaml_parser.py) |
| 断言引擎 | [utils/assertion.py](file:///d:/pythontest/ziufileApi/utils/assertion.py) |
| 用例收集 | [utils/case_collector.py](file:///d:/pythontest/ziufileApi/utils/case_collector.py) |
| 步骤执行 | [utils/step_runner.py](file:///d:/pythontest/ziufileApi/utils/step_runner.py) |
| Setup 执行 | [utils/setup_runner.py](file:///d:/pythontest/ziufileApi/utils/setup_runner.py) |
| 脱敏工具 | [utils/masking.py](file:///d:/pythontest/ziufileApi/utils/masking.py) |
| 邮件摘要 | [utils/result_summary.py](file:///d:/pythontest/ziufileApi/utils/result_summary.py) |
| 数据库客户端 | [utils/db_client.py](file:///d:/pythontest/ziufileApi/utils/db_client.py) |
| 统一运行脚本 | [run_test.py](file:///d:/pythontest/ziufileApi/run_test.py) |
| Windows 批处理 | [run_test.bat](file:///d:/pythontest/ziufileApi/run_test.bat) |
| Jenkins 流水线 | [Jenkinsfile](file:///d:/pythontest/ziufileApi/Jenkinsfile) |
| 依赖清单 | [requirements.txt](file:///d:/pythontest/ziufileApi/requirements.txt) |
| 用户手册 | [README.md](file:///d:/pythontest/ziufileApi/README.md) |
| 本 Code Wiki | [CODE_WIKI.md](file:///d:/pythontest/ziufileApi/CODE_WIKI.md) |
