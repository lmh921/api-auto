# Code Wiki · ziufileApi 接口自动化测试框架

> 版本：v1.0 · 更新时间：2026-10-10
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
5. [入口与执行层](#5-入口与执行层)
   - 5.1 [conftest.py · Pytest 配置与 Fixtures](#51-conftestpy-pytest-配置与-fixtures)
   - 5.2 [test_executor.py · 用例执行主体](#52-test_executorpy-用例执行主体)
   - 5.3 [run_test.py · 统一运行脚本](#53-run_testpy-统一运行脚本)
   - 5.4 [run_test.bat · Windows 菜单式批处理](#54-run_testbat-windows-菜单式批处理)
   - 5.5 [debug_test.py · 手动调试脚本](#55-debug_testpy-手动调试脚本)
   - 5.6 [test_framework.py · 框架功能自检](#56-test_frameworkpy-框架功能自检)
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
       → parametrize("case_file,case")  每一条用例独立参数化 + tag→marker 映射
  → conftest.clear_allure_results        session 级清理
  → 对每个参数化用例：
       → test_api_executor(case_file, case, yaml_parser, http_client, assertion, global_vars)
            → allure 动态打标
            → setup_runner.ensure_setup  文件级setup（首次触发，支持缓存）
                 → prepare_step → send_prepared → cleanup_step
                 → run_assertions → extract → register_extracted
            → prepare_step(case)         变量替换 + 组装files
            → send_prepared(case)        发送 + env覆盖
            → cleanup_step               恢复env + 关闭文件句柄
            → assertion.run_assertions   软断言
            → extract 写 global_vars     + 注册脱敏
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
│   └── _archived_ziulife/          # 旧产品归档用例（当前目录演示用）
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
├── utils/                          # 核心模块（9 个子模块）
│   ├── config.py                   # 全局配置：多环境/正式环境保护/预置变量
│   ├── http_client.py              # HTTP 客户端：幂等重试策略
│   ├── yaml_parser.py              # YAML 解析 + ${var} 变量替换（保留类型）
│   ├── assertion.py                # 软断言 + JSONPath 取值引擎
│   ├── case_collector.py           # 用例发现 / jsonschema 校验 / setup 注册 / 用例ID
│   ├── step_runner.py              # 单步骤准备-发送-清理三件套
│   ├── setup_runner.py             # 文件级 setup 执行 + 跨文件缓存
│   ├── masking.py                  # 三层脱敏：字典/Repr/文本替换
│   └── result_summary.py           # Allure 结果 → 邮件正文+HTML附件
│
├── conftest.py                     # Pytest 入口：参数化 + Fixtures + 日志脱敏
├── pytest.ini                      # Pytest 静态配置：markers / addopts / testpaths
├── requirements.txt                # 第三方依赖清单
├── run_test.py                     # argparse 统一运行脚本（推荐入口）
├── run_test.bat                    # Windows 菜单式批处理
├── debug_test.py                   # 开发者手动调试脚本
├── test_framework.py               # 框架 4 大模块自检脚本
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

#### 关键类 `YamlParser`

| 方法 | 签名 | 说明 |
|------|------|------|
| `load_file` | `(file_path: str) -> dict` | 读取 YAML；不存在抛 `FileNotFoundError` |
| `parse_test_cases` | `(file_path: str) -> List[dict]` | 统一返回用例列表；自动识别单接口/多接口形式 |
| `replace_variables` | `(data: Any, variables: dict) -> Any` | 递归：字符串 / dict / list 替换变量；其他类型原样返回 |
| `_replace_in_string` | `(text: str, variables: dict) -> Any` | 单个字符串：整串占位符保留类型，嵌入占位符做 `sub` |

#### 变量替换规则（核心设计）

```python
# 规则1：整串占位符 → 保留原始类型
expected: "${user_id}"    # 若 global_vars["user_id"] = 123 (int) → 结果为 123 int
                          # 避免 "123" != 123 的断言误判

# 规则2：嵌入占位符 → 字符串插值
Authorization: "Bearer ${token}"   # → "Bearer xxxx"

# 规则3：未定义变量 → 保留原文 + DEBUG 日志
url: "/users/${undefined_var}"     # → "/users/${undefined_var}"
```

#### 常量

| 常量 | 正则 | 说明 |
|------|------|------|
| `VAR_PATTERN` | `\$\{([^}]+)\}` | `${var}` 占位符 |

---

### 4.4 assertion.py · 断言模块

**文件**：[utils/assertion.py](file:///d:/pythontest/ziufileApi/utils/assertion.py)

#### 职责

- 基于 jsonpath-ng 的响应体取值引擎
- 8 种断言方法 + 状态码断言 + **软断言汇总**
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

---

### 4.5 case_collector.py · 用例收集器

**文件**：[utils/case_collector.py](file:///d:/pythontest/ziufileApi/utils/case_collector.py)

#### 职责

- 根据环境配置的 `case_data_path` 扫描所有 `.yaml/.yml`（排除 `*_template.yaml`）
- 用 **JSON Schema** 校验 setup 与 单条 case 的结构合规性
- 结构错误 / YAML 解析错误 → 生成显式失败用例（带 `_collect_error` 字段），不会静默丢失
- 注册文件级 setup 到全局字典 `FILE_SETUPS`
- 生成形如 `路径::用例名` 的唯一用例 ID（重名追加 `#2`、`#3`）

#### 常量与 Schema

| 名称 | 类型 | 说明 |
|------|------|------|
| `FILE_SETUPS` | `Dict[str, dict]` | 全局注册表：`rel_path → {cache, steps}` |
| `CASE_SCHEMA` | JSON Schema | 要求 `name` + `request(method,url)`；允许 `tags/env/assertions/extract` |
| `SETUP_SCHEMA` | JSON Schema | 要求 `steps[]`；可选 `cache: bool` |

#### 关键函数

| 函数 | 签名 | 说明 |
|------|------|------|
| `get_test_case_files(config)` | `(Config) -> List[Path]` | 按文件名排序；排除模板文件 |
| `_validate_schema(instance, schema)` | `(Any, dict) -> List[str]` | 返回错误列表；空列表=通过 |
| `collect_all_cases(config)` | `(Config) -> List[Tuple[str, dict]]` | 核心：返回 `(相对路径, 用例dict)` 列表 |
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
| `prepare_step(step, global_vars, yaml_parser, base_dir)` | 核心：变量替换 + 组装 requests kwargs + 打开 files + 返回 attach_kwargs（报告用，内容是路径不包含句柄） |
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
- 执行成功：提取的变量写入 `global_vars`，注册脱敏 → 本文件所有用例可用
- 执行失败：该文件的后续所有用例直接失败，原因来自 `_setup_failed[case_file]`
- 跨文件缓存（`cache: true`）：**相同 steps 内容 + 相同 base_url** → 用签名命中缓存跳过执行
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
| `ensure_setup(case_file, global_vars, http_client, assertion, yaml_parser) -> Optional[str]` | 返回 `None` 成功；返回 str = 错误信息；失败会写入 `_setup_failed`，后续同文件用例直接拿缓存错误 |

**执行顺序**：
1. `spec = FILE_SETUPS.get(case_file)` 不存在 / 已 done → 跳过
2. 计算签名 → 命中缓存且 `cache: true` → `global_vars.update(缓存)` → done
3. 依次执行 steps：`prepare_step` → `send_prepared` → `cleanup_step`
4. 执行断言（如有）→ 提取变量 → `register_extracted` 注册脱敏
5. 成功 → `_done_files`；失败 → `_setup_failed[case_file] = error`

> 注意：业务会改变账号状态（如注销登录）时务必不要开启 `cache: true`，否则后续文件会拿到失效 token。

---

### 4.8 masking.py · 敏感信息脱敏

**文件**：[utils/masking.py](file:///d:/pythontest/ziufileApi/utils/masking.py)

三层防护架构：

| 层级 | 实现 | 作用于 | 效果 |
|------|------|--------|------|
| 第1层 | `mask_data(data)` | 结构化字典/列表（请求参数、响应体、Allure 附件） | 深拷贝后替换敏感键值为 `******` |
| 第2层 | `MaskedDict(dict)` | pytest 失败回显 / Allure 参数记录（global_vars、case 参数） | `__repr__` 输出时调用 mask_data |
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

## 5. 入口与执行层

### 5.1 conftest.py · Pytest 配置与 Fixtures

**文件**：[conftest.py](file:///d:/pythontest/ziufileApi/conftest.py)

#### 关键钩子

| 钩子 | 作用 |
|------|------|
| **日志初始化**（模块顶层） | `logger.remove() → logger.configure(patcher=redact_text)` → 双 sink：文件（100MB 滚动 / 7天保留）+ 控制台彩色输出 |
| `pytest_addoption(parser)` | 注册自定义组 `ziufile-api`：<br>`--env`（环境名）、`--confirm-prod`（正式环境确认开关） |
| `pytest_generate_tests(metafunc)` | 核心：只对 `case` fixture 生效 → 调用 `collect_all_cases` + `build_case_ids` → 用 `pytest.param(rel_path, MaskedDict(case), id=case_id, marks=marker_list)` 做参数化。<br>**tags → markers 映射**：用例 tags 与 pytest.ini 中注册的 marker 同名者自动挂对应 pytest mark，支持 `-m smoke` 圈选。<br>**MaskedDict**：参数对象 repr 脱敏，防止 pytest 失败回显/Allure 参数泄漏。 |

#### Fixtures

| Fixture | Scope | 说明 |
|---------|-------|------|
| `global_vars` | **session** | 来自 `get_config().variables`（含 `$ENV{}` 展开），`MaskedDict` 包装；用例间通过 extract 写入实现变量传递 |
| `http_client` | **function** | 每个用例独立实例，避免 case 级 `env` 覆盖相互污染；结束自动 `session.close()` |
| `yaml_parser` | function | YamlParser 实例 |
| `assertion` | function | Assertion 实例 |
| `clear_allure_results` | session / autouse | 按 allure.clean 开关清理 `reports/allure-results/*` |

---

### 5.2 test_executor.py · 用例执行主体

**文件**：[testcases/test_executor.py](file:///d:/pythontest/ziufileApi/testcases/test_executor.py)

#### `test_api_executor(case_file, case, yaml_parser, http_client, assertion, global_vars)`

**执行流程**（每条参数化用例走一次）：

```
0. _collect_error 检测 → 有则立即 pytest.fail
1. Allure 动态打标
     title       = case.name
     description = case.description
     labels      = case_file, env
     tags        = case.tags
2. allure.step("执行文件前置步骤(setup)")
     → setup_runner.ensure_setup(...)
     → 失败则 pytest.fail（同文件后续用例直接命中 _setup_failed 缓存）
3. 断言期望值变量替换：assertions = replace_variables(case.assertions, global_vars)
4. prepare_step(case) 组装请求
5. try:
     allure.step("发送请求") →
       attach 脱敏请求参数 JSON
       response = send_prepared(...)
       attach 状态码 / 脱敏响应体 JSON
   finally: cleanup_step（确保文件句柄关闭、env 恢复）
6. allure.step("执行断言") → assertion.run_assertions（软断言）
7. case.extract 存在时：
     allure.step("提取变量")
       for var_name, jsonpath:
           global_vars[var_name] = 取值
           register_extracted（敏感键注册到文本替换）
           log & attach 脱敏后的 key=value
```

> 设计要点：`try-finally` 包 request + cleanup，确保任何异常（断言失败、网络错误）下文件句柄不泄漏，env 覆盖总能恢复。

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

### 5.5 debug_test.py · 手动调试脚本

**文件**：[debug_test.py](file:///d:/pythontest/ziufileApi/debug_test.py)

开发者可直接编辑脚本里的 `file_path`，按以下流程跑单个 YAML 文件逐条用例：
`parse_test_cases → replace_variables → request → run_assertions → extract → update global_vars`。
用于在无 pytest 环境下快速验证单个 YAML 的逻辑正确性。

---

### 5.6 test_framework.py · 框架功能自检

**文件**：[test_framework.py](file:///d:/pythontest/ziufileApi/test_framework.py)

4 个用例的自检脚本：
1. `test_config_loader` → Config 加载
2. `test_yaml_parser` → 解析 mock_test.yaml
3. `test_http_client` → 初始化 HttpClient
4. `test_assertion` → 内存断言模拟

结束输出 `通过: X/4`，退出码按结果。用于搭建新环境时快速验证框架基本能力。

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
```

**依赖表（谁 import 谁）**：

| 模块 | 内部 import |
|------|-------------|
| config.py | （无） |
| masking.py | （无） |
| yaml_parser.py | （无） |
| http_client.py | masking.mask_data；config.get_config（懒加载） |
| assertion.py | （无；第三方 jsonpath-ng） |
| case_collector.py | config.PROJECT_ROOT/Config；yaml_parser.YamlParser；（第三方 jsonschema） |
| step_runner.py | config.PROJECT_ROOT；yaml_parser.YamlParser |
| setup_runner.py | case_collector.FILE_SETUPS；config.PROJECT_ROOT；masking（mask_data/register_extracted）；step_runner（全部） |
| result_summary.py | （无；标准库 argparse/json/html/pathlib） |
| conftest.py | utils.http_client / yaml_parser / assertion / config / case_collector / masking |
| testcases/test_executor.py | utils.setup_runner / config / masking / step_runner |
| run_test.py | （调用 pytest.main；无直接 import utils） |
| debug_test.py | utils.yaml_parser / http_client / assertion / config |
| test_framework.py | utils.yaml_parser / http_client / assertion / config |

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
global_vars:                        # 注释占位（当前由 setup / extract 注入，global_vars 暂未直接使用，见 README）
testcases:
  - name: "用例1"
    request: { ... }
    assertions: [...]
    extract:
      token: "data.token"
  - name: "用例2（引用上一步token）"
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

执行语义：同文件所有用例中，仅**第一条被 Pytest 执行时**触发 setup；该文件后续用例跳过 setup，直接复用 `global_vars`。若 setup 失败，该文件所有用例直接失败，原因会被缓存。

### 8.4 变量提取与引用

| 方式 | 示例 | 生效范围 |
|------|------|----------|
| `extract:` + `global_vars` session fixture | 用例1 `extract.user_id = data.id` → 用例2 `${user_id}` | **本次 pytest session**，跨文件也可用 |
| `config.yaml variables` 段 + `$ENV{}` | `test_mobile: "$ENV{TEST_MOBILE}"` → 用例中 `${test_mobile}` | 所有用例 |
| 整串占位符保留类型 | `expected: "${count}"` 其中 count=5 int → 比较时仍为 int | 断言 expected 中常用 |
| 嵌入占位符做字符串插值 | `"Bearer ${token}"` | URL / Header / JSON 值中任意位置 |

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
| 统一运行脚本 | [run_test.py](file:///d:/pythontest/ziufileApi/run_test.py) |
| Windows 批处理 | [run_test.bat](file:///d:/pythontest/ziufileApi/run_test.bat) |
| 调试脚本 | [debug_test.py](file:///d:/pythontest/ziufileApi/debug_test.py) |
| 框架自检 | [test_framework.py](file:///d:/pythontest/ziufileApi/test_framework.py) |
| Jenkins 流水线 | [Jenkinsfile](file:///d:/pythontest/ziufileApi/Jenkinsfile) |
| 依赖清单 | [requirements.txt](file:///d:/pythontest/ziufileApi/requirements.txt) |
| 用户手册 | [README.md](file:///d:/pythontest/ziufileApi/README.md) |
| 本 Code Wiki | [CODE_WIKI.md](file:///d:/pythontest/ziufileApi/CODE_WIKI.md) |
