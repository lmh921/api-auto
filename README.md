# 接口自动化测试框架

## 1. 框架介绍

本框架是一个基于Python开发的接口自动化测试框架，采用零代码封装设计，测试人员只需编写YAML格式的测试用例即可执行接口测试，无需编写Python代码。

### 1.1 主要特性

- **零代码封装**：测试人员只需编写YAML格式测试用例
- **用例级隔离**：每个YAML测试用例是独立的pytest用例，单条失败不影响其他用例
- **灵活的断言机制**：支持多种断言类型（状态码、相等、包含等），软断言汇总所有失败项
- **变量提取与传递**：支持在测试用例间提取和传递变量，保留原始类型
- **多环境支持**：`--env` 一键切换环境，正式环境需 `--confirm-prod` 显式确认
- **文件级setup**：登录等前置步骤写一次，同一文件所有用例复用
- **自动生成报告**：集成Allure生成美观的测试报告，敏感信息自动脱敏
- **完善的日志记录**：使用Loguru记录详细的测试过程
- **接口+数据库双校验**：支持用例级 db_setup 造数、db_assertions 落库校验（行数/单值/包含，软断言）、extract_from_db 提取、db_teardown 清理，支持 MySQL（pymysql）与 SQLite（内置）
- **易于扩展**：模块化设计，方便扩展新功能

## 2. 技术栈

- **Python 3.8+**：开发语言
- **Pytest**：测试执行引擎
- **Requests**：HTTP请求发送
- **YAML**：测试用例编写格式
- **Allure**：测试报告生成
- **Loguru**：日志管理

## 3. 项目结构

```
ziufileApi/
├── config/                  # 配置文件目录
│   └── config.yaml         # 全局配置文件（多环境定义）
├── data/                   # 真实业务测试用例目录（由 config.yaml 的 caseData_path 指向）
│   ├── client_data/        # 客户端测试用例（client-* 环境执行）
│   └── station_data/       # 驿站端测试用例（station-* 环境执行）
├── logs/                   # 日志文件目录
├── reports/                # 测试报告目录
├── testcases/              # Pytest Python 执行入口 + 用例模板/示例
│   └── test_executor.py    # 唯一的 Python 测试函数，将 data/ 下的 YAML 用例参数化执行
├── utils/                  # 工具类目录
│   ├── http_client.py      # HTTP客户端（重试策略）
│   ├── yaml_parser.py      # YAML解析器（变量替换）
│   ├── assertion.py        # 断言工具（软断言+JSONPath）
│   ├── config.py           # 全局配置（多环境+正式环境保护）
│   ├── case_collector.py   # 用例收集（结构校验+setup注册）
│   ├── step_runner.py      # 步骤执行（env覆盖+文件上传）
│   ├── setup_runner.py     # 文件级前置步骤
│   ├── masking.py          # 敏感信息脱敏
│   ├── db_client.py        # 数据库客户端（MySQL/SQLite，用例级连接）
│   └── result_summary.py   # 测试结果摘要（CI邮件正文/附件生成）
├── conftest.py             # Pytest配置（--env参数+用例参数化）
├── pytest.ini              # Pytest配置
├── requirements.txt        # 依赖包列表
├── run_test.py             # Python运行脚本
├── run_test.bat            # Windows批处理脚本
├── Jenkinsfile             # Jenkins CI流水线（测试→报告→邮件通知）
├── .gitignore              # git忽略规则
└── README.md               # 框架使用说明
```

## 4. 安装步骤

### 4.1 环境要求

- Python 3.8 或更高版本
- pip 包管理器

### 4.2 安装依赖

```bash
# 安装项目依赖
pip install -r requirements.txt
```

### 4.3 安装Allure命令行工具

Allure报告生成需要安装Allure Commandline工具。以下是不同操作系统的安装方法：

#### Windows系统
1. 下载Allure Commandline工具：[https://github.com/allure-framework/allure2/releases](https://github.com/allure-framework/allure2/releases)
2. 选择最新版本的`allure-*-zip.zip`文件下载
3. 解压到本地目录（如：`C:\allure-2.24.1`）
4. 将解压目录下的`bin`文件夹添加到系统环境变量`PATH`中
5. 重启命令行窗口
6. 验证安装：运行`allure --version`命令，显示版本信息则安装成功

#### macOS系统
```bash
# 使用Homebrew安装
brew install allure

# 验证安装
allure --version
```

#### Linux系统
```bash
# 下载并安装
wget https://github.com/allure-framework/allure2/releases/download/2.24.1/allure-2.24.1.tgz
tar -zxvf allure-2.24.1.tgz
mv allure-2.24.1 /opt/
ln -s /opt/allure-2.24.1/bin/allure /usr/local/bin/

# 验证安装
allure --version
```

**注意**：需要将上述命令中的版本号替换为最新版本。

## 5. 配置说明

### 5.1 全局配置文件

配置文件路径：`config/config.yaml`

```yaml
# 默认执行环境（未指定 --env 时使用）
default_env: "client-dev"

# 环境列表
environments:
  client-dev:
    base_url: "https://www.ziulife.com/client-api-dev/client"
    caseData_path: "data/client_data"
  client-prod:
    base_url: "https://www.ziulife.com/client-api-prod/client"
    caseData_path: "data/client_data"
    prod: true          # 标记正式环境，执行必须追加 --confirm-prod
  station-dev:
    base_url: "https://www.ziulife.com/station-api-dev"
    caseData_path: "data/station_data"

# 请求超时时间（秒）
timeout: 30

# 请求失败重试次数（5xx仅对幂等方法GET/HEAD/OPTIONS重试；连接类错误对所有方法重试）
retry_times: 3

# 重试间隔（秒）
retry_delay: 2.0

# 预置变量：所有用例可通过 ${变量名} 引用；值支持 $ENV{环境变量名}（敏感数据外部化）
# variables:
#   test_mobile: "$ENV{TEST_MOBILE}"
variables: {}

# 日志配置
log:
  level: "INFO"
  file_path: "logs/api_test.log"

# Allure报告配置
allure:
  report_dir: "reports/allure-results"
  clean: true
```

**多环境切换**：`pytest --env station-dev`（或 `python run_test.py -e station-dev`），也可以设置环境变量 `TEST_ENV`。未指定时使用 `default_env`。

**正式环境保护**：标记 `prod: true` 的环境默认拒绝执行，必须显式追加 `--confirm-prod`（CI中可设置环境变量 `ALLOW_PROD=1`），防止误跑生产。

### 5.2 Pytest配置

配置文件路径：`pytest.ini`

```ini
[pytest]
# 测试用例发现路径
testpaths = testcases
# 测试文件匹配规则
python_files = test_*.py
# 测试函数匹配规则
python_functions = test_*
# 参数标记
markers =
    smoke: 冒烟测试
    regression: 回归测试
    api: API测试
# Allure报告配置
addopts = -v -s --alluredir=reports/allure-results
```

## 6. 测试用例编写

### 6.1 测试用例格式

测试用例采用YAML格式编写，**存放在 `config.yaml` 中各环境 `caseData_path` 指定的目录下**（默认 `data/client_data` 与 `data/station_data`），以 `.yaml` 为后缀（模板文件除外）。

> ⚠️ 注意区分两个目录：
> - `data/*_data/`：**真实业务测试用例**所在目录，由 `case_collector.py` 按 `caseData_path` 递归扫描。
> - `testcases/`：存放 Pytest 的 Python 执行入口 `test_executor.py` 。框架通过 `test_executor.py` 这个唯一的 Python 测试函数，把 `data/` 下的每条 YAML 用例参数化为独立的 Pytest 用例来执行。

### 6.2 单接口测试用例示例

```yaml
# 测试用例描述
description: "用户管理接口测试"
# 测试标签
tags: ["用户管理", "GET", "冒烟测试"]

# 测试用例列表
testcases:
  # 测试用例1：获取用户列表
  - name: "获取用户列表"
    description: "测试获取所有用户信息"
    # 环境配置（可选，覆盖全局配置）
    env:
      base_url: "https://jsonplaceholder.typicode.com"
      timeout: 15
    # 请求配置
    request:
      method: "GET"  # 请求方法
      url: "/users"  # 请求URL（可拼接base_url）
      params:  # 请求参数（可选）
        page: 1
        limit: 10
      headers:  # 请求头（可选）
        Content-Type: "application/json"
        Authorization: "Bearer token123"
    # 断言配置
    assertions:
      - type: "status_code"  # 断言类型：状态码
        expected: 200  # 期望结果
        message: "检查响应状态码"
      - type: "contains"  # 断言类型：包含
        jsonpath: "[0].name"  # JSONPath表达式
        expected: "Leanne Graham"  # 期望结果
        message: "检查第一个用户名称包含"
      - type: "equal"  # 断言类型：相等
        jsonpath: "[0].id"  # JSONPath表达式
        expected: 1  # 期望结果
        message: "检查第一个用户ID"
    # 变量提取（可选）
    extract:
      first_user_id: "[0].id"  # 提取第一个用户的ID
      first_user_name: "[0].name"  # 提取第一个用户的名称
```

### 6.3 多接口测试用例示例

```yaml
# 测试用例描述
description: "用户管理流程测试"
# 测试标签
tags: ["用户管理", "流程测试"]

# 全局变量
global_vars:
  username: "testuser"
  password: "testpass123"

# 测试用例列表
testcases:
  # 测试用例1：用户登录
  - name: "用户登录"
    request:
      method: "POST"
      url: "/login"
      json:
        username: "${username}"
        password: "${password}"
    assertions:
      - type: "status_code"
        expected: 200
    extract:
      token: "data.token"  # 提取登录令牌

  # 测试用例2：获取用户信息
  - name: "获取用户信息"
    request:
      method: "GET"
      url: "/user/info"
      headers:
        Authorization: "Bearer ${token}"  # 使用上一个用例提取的token
    assertions:
      - type: "status_code"
        expected: 200
      - type: "equal"
        jsonpath: "data.username"
        expected: "${username}"
```

### 6.4 文件级前置步骤（setup）

登录等前置步骤只需在文件顶部写一次，同一文件的所有用例自动复用提取的变量，不再需要每个用例文件重复维护登录用例：

```yaml
# 文件级前置步骤：在本文件所有用例前执行一次
setup:
  cache: false        # 可选，true表示跨文件缓存执行结果（相同环境+相同setup内容只执行一次）
  steps:
    - name: "用户登录（前置）"
      request:
        method: "POST"
        url: "/appUser/codeLogin"
        json:
          mobile: "19999999999"
          code: "000000"
      extract:
        token: "data.token"

testcases:
  - name: "获取用户信息"
    request:
      method: "GET"
      url: "/appUser/info"
      headers:
        Authorization: "Bearer ${token}"   # token来自setup
```

**注意**：业务会改变账号状态（如注销登录）时不要开启 `cache: true`，否则后续文件可能拿到失效的token。

### 6.5 文件上传（files）

`files` 支持从本地路径上传文件，相对路径优先相对于用例文件所在目录解析：

```yaml
request:
  method: "POST"
  url: "/upload"
  files:
    image: "testdata/a.png"                        # 简写：自动取文件名
    avatar: ["testdata/a.png", "my.png", "image/png"]  # 完整写法：路径、文件名、Content-Type
```

### 6.6 敏感信息与脱敏

- 日志和Allure报告附件中的 `token`、`password`、`mobile`、`phone`、`Authorization` 等敏感字段会自动替换为 `******`（断言内部仍使用真实值）；
- 建议通过配置的 `variables` 段 + 环境变量外部化账号数据：`test_mobile: "$ENV{TEST_MOBILE}"`，用例中写 `mobile: "${test_mobile}"`。

### 6.7 断言类型

| 断言类型 | 描述 | 示例 |
|---------|------|------|
| status_code | 断言响应状态码 | `{"type": "status_code", "expected": 200}` |
| equal | 断言相等 | `{"type": "equal", "jsonpath": "name", "expected": "test"}` |
| contains | 断言包含 | `{"type": "contains", "jsonpath": "url", "expected": "http://"}` |

**软断言**：同一用例配置的多条断言会全部执行，任何一条失败都不会中断后续断言；执行结束后一次性汇总所有失败项，便于一次定位多个问题。

**断言中的变量替换**：`expected` 同样支持 `${var}` 变量。整串占位符（如 `expected: "${user_id}"`）会保留提取变量的原始类型，数字/布尔等类型比较不会因转成字符串而误判。

### 6.8 JSONPath使用

JSONPath底层基于 `jsonpath-ng` 实现，`$` 前缀可以省略：

- `$`：根节点（可省略）
- `.`：子节点
- `..`：递归子节点
- `[]`：数组索引
- `*`：通配符
- `$length`：特殊路径，返回响应体（数组/字典/字符串）的长度

示例：
- `data.token` / `$.data.token`：data下的token字段
- `[0].id` / `$[0].id`：数组第一个元素的id字段
- `$..email`：所有层级的email字段
- `$[*].id`：数组所有元素的id字段
- `$length`：响应体长度（常用于列表数量断言）

匹配到单个值时返回该值；匹配到多个值时返回列表；匹配不到时该条断言失败。

### 6.9 数据库连接与校验

框架支持在用例中直接操作数据库：前置造数（`db_setup`）、数据落库校验（`db_assertions`）、库内变量提取（`extract_from_db`）、清理（`db_teardown`），适用于"接口调用后校验数据是否正确落库"等场景。

**第一步：环境配置**（`config/config.yaml` 环境下增加 `db` 段，密码支持 `$ENV{DB_PASSWORD}` 外部化）：

```yaml
environments:
  client-dev:
    base_url: "https://..."
    caseData_path: "data/client_data"
    db:
      driver: mysql            # mysql / sqlite
      host: "127.0.0.1"
      port: 3306
      user: "test_rw"
      password: "$ENV{DB_PASSWORD}"   # 敏感信息外部化到环境变量
      database: "client_dev"
      charset: "utf8mb4"
```

`driver: sqlite` 时只需 `path` 一个参数（Python 内置驱动，零依赖，适合演示/离线验证）。mysql 驱动需安装 `pip install pymysql`（已在 requirements.txt）。

**第二步：用例中编写 DB 步骤**：

```yaml
testcases:
  - name: "创建用户后校验落库"
    request:                       # 接口调用（纯数据库用例可省略 request）
      method: "POST"
      url: "/user/create"
      json: { mobile: "${test_mobile}" }
    extract:
      new_user_id: "data.id"

    db_setup:                      # 前置：请求前执行（建表/造数），支持 ${var}
      - "DELETE FROM t_user WHERE mobile = '${test_mobile}'"

    db_assertions:                 # 请求后执行的数据校验（软断言，失败汇总）
      - type: "row_count"          # 行数校验
        sql: "SELECT id FROM t_user WHERE mobile = '${test_mobile}'"
        op: ">="                   # 支持 == != > >= < <=
        expected: 1
        message: "用户应落库"
      - type: "value"              # 单值校验（默认取首行第一列，可用 column 指定列名）
        sql: "SELECT status FROM t_user WHERE mobile = '${test_mobile}'"
        expected: "active"
        message: "用户状态应为active"
      - type: "contains_row"       # 查询结果包含（整行字典列表 或 column 指定列的值列表）
        sql: "SELECT role FROM t_user WHERE mobile = '${test_mobile}'"
        column: "role"
        expected: "admin"

    extract_from_db:               # 从库中提取变量（取首行首列），后续用例可用 ${db_user_id}
      db_user_id: "SELECT id FROM t_user WHERE mobile = '${test_mobile}'"

    db_teardown:                   # 清理：无论断言成败都执行，防止数据残留
      - "DELETE FROM t_user WHERE mobile = '${test_mobile}'"
```

**规则说明**：

- 执行顺序：文件setup → `db_setup` → 请求（可选）→ 接口断言（可选）→ `db_assertions` → `extract` / `extract_from_db` → `finally: db_teardown`；
- **时序**：`db_setup` 在请求之前执行，若需要引用接口返回的变量（如落库校验），请拆成两条用例跨用例传参（参考 `data/client_data/db_demo_test.yaml`）；
- 所有 SQL 均支持 `${var}` 变量替换；`db_assertions` 的 `expected` 整串占位符保留原始类型；
- 环境未配置 `db` 段时，用例使用了 db_* 字段会直接失败并提示补充配置；
- 连接为用例级生命周期（每条用例独立连接，用完即关）；
- 离线演示：`data/case_template/db_demo_test.yaml`（sqlite 驱动），`python run_test.py -e client-dev` 可直接运行。

### 6.10 用例依赖与条件执行（depends_on / run_if）

跨用例传参（`extract` + `${var}`）只解决了"数据从哪来"，`depends_on` / `run_if` 解决"什么时候该执行"：

- **显式依赖** `depends_on`：声明的上游用例 failed / skipped / 未执行时，本用例自动 **skip**（带具体原因），不再带着未替换的字面量 `${var}` 发请求产生误导性失败；
- **可靠执行顺序**：收集期按依赖图**拓扑排序**，生产者一定先于消费者执行，跨文件依赖**不再依赖文件名排序**（无需 `01_`、`02_` 前缀约定）；无依赖关系的用例仍按文件名 + 书写顺序执行，顺序稳定；
- **条件执行** `run_if`：`global_vars` 中的变量满足条件才执行，不满足时 skip（**不满足不是失败**）。

```yaml
testcases:
  - name: "1. 创建收货地址"
    request: { method: "POST", url: "/address/create" }
    extract:
      address_id: "data.addressId"        # 产出变量

  - name: "3. 创建订单"
    depends_on:                           # 显式依赖：可依赖多条，全部 passed 才执行
      - "1. 创建收货地址"                  # 用例名引用（全局唯一时）
      - "data/client_data/order_test.yaml::2. 查询商品"   # 重名/跨文件时用 文件相对路径::用例名
    request: { method: "POST", url: "/order/create" }

  - name: "4. 支付订单"
    depends_on: ["3. 创建订单"]
    run_if:                               # 条件执行：商品价格大于0才支付
      var: sku_price                      # 取自 global_vars（extract/extract_from_db/setup/预置变量）
      op: gt                              # eq(默认) ne gt ge lt le in not_in contains exists not_exists
      value: 0                            # 支持 ${var} 引用其他变量
    request: { method: "POST", url: "/order/pay" }
```

**规则说明**：

- 执行顺序（新增判定在前）：**依赖判定(depends_on) → 条件判定(run_if)** → 文件setup → `db_setup` → 请求 → 断言 → `db_assertions` → `extract` / `extract_from_db` → `finally: db_teardown`；
- 依赖语义为**强依赖**：上游 failed、skipped（含上游自身的 run_if 不满足、再上游失败）都会导致本用例 skip；skip 原因会写进 pytest/Allure 报告（`-rs` 查看）；
- 收集期校验并给出明确失败原因（转为一条失败用例而非静默丢弃）：**依赖的用例不存在**、**用例名不唯一**（改用 `文件路径::用例名`）、**依赖自身**、**循环依赖**（列出环上所有用例）；
- 用 `-m` / `-k` 圈选时，若上游被过滤掉未执行，下游会以"依赖的用例 [...] 未执行"skip，而不是报错；
- `depends_on` / `run_if` 仅对 `testcases` 用例生效，`setup` 步骤中写会直接校验失败；
- 与 pytest-xdist 并行不兼容（session 级 `global_vars` 的既有约束，非本功能引入）；
- 完整示例参考 `data/case_template/dependency_chain_test.yaml`。

## 7. 运行测试

### 7.1 使用Python脚本

```bash
# 运行所有测试用例（默认环境）
python run_test.py

# 指定环境运行
python run_test.py -e station-dev

# 正式环境需显式确认
python run_test.py -e client-prod --confirm-prod

# 运行指定测试用例文件
python run_test.py --file testcases/example_test.yaml

# 仅安装依赖
python run_test.py --install

# 仅生成报告
python run_test.py --report
```

### 7.2 使用Windows批处理脚本

```bash
# 运行批处理脚本
run_test.bat
```

批处理脚本提供了菜单选择：
1. 安装依赖
2. 运行测试
3. 生成Allure报告
4. 打开Allure报告
5. 执行完整流程（安装依赖→运行测试→生成报告→打开报告）
6. 退出

### 7.3 使用Pytest命令

```bash
# 运行所有测试用例（每个YAML测试用例是独立的pytest用例，单条失败不影响其他用例）
python -m pytest testcases/test_executor.py -v -s --alluredir=reports/allure-results

# 运行指定测试用例（用例ID = 用例文件路径::用例名）
python -m pytest "testcases/test_executor.py::data/client_data/login_test.yaml::验证用户登录" -v -s

# 切换环境
python -m pytest --env station-dev

# 按marker圈选用例（用例tags中包含对应标记时生效，见pytest.ini的markers定义）
python -m pytest -m smoke -v

# 生成并打开报告
allure serve reports/allure-results
```

## 8. 查看报告

### 8.1 生成Allure报告

```bash
# 生成报告
allure generate reports/allure-results -o reports/allure-report --clean

# 打开报告
allure open reports/allure-report
```

### 8.2 报告内容

Allure报告包含以下内容：
- 测试结果概览
- 测试用例执行详情
- 请求和响应信息
- 断言结果
- 错误信息
- 日志记录

## 9. 日志查看

日志文件路径：`logs/api_test.log`

日志格式包含：时间戳、日志级别、模块名、函数名、行号、日志信息

示例：
```
2025-12-11 20:43:46.449 | INFO     | utils.assertion:assert_equal:37 - 测试状态码 状态码 断言成功: 200 等于 200
```

## 10. 常见问题

### 10.1 安装依赖失败

**问题**：`pip install -r requirements.txt` 安装失败

**解决方法**：
- 检查Python版本是否为3.8或更高
- 检查网络连接
- 尝试使用国内镜像源：`pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`

### 10.2 Allure报告无法生成

**问题**：运行测试后无法生成Allure报告

**解决方法**：
- 检查Allure是否已正确安装并添加到系统环境变量
- 检查测试是否正常执行，生成了报告结果文件
- 检查报告结果目录配置是否正确

### 10.3 测试用例执行失败

**问题**：测试用例执行失败

**解决方法**：
- 查看日志文件了解详细错误信息
- 检查测试用例中的请求参数、URL、断言是否正确
- 检查接口是否正常可用
- 检查网络连接

## 11. 扩展开发

### 11.1 添加新的断言类型

在`utils/assertion.py`文件中添加新的断言方法：

```python
def assert_new_type(self, actual: Any, expected: Any, message: str = "") -> None:
    """新的断言类型"""
    # 实现断言逻辑
    if not condition:
        raise AssertionError(f"{message} 断言失败")
    logger.info(f"{message} 断言成功")

# 在run_assertions方法中添加对应的处理
```

### 11.2 扩展HTTP请求方法

在`utils/http_client.py`文件中扩展请求方法：

```python
def request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
    """发送HTTP请求"""
    # 扩展请求方法处理
    pass
```

## 12. Jenkins 持续集成（完全自动 + 邮件通知）

项目已内置 CI 所需的全部项目侧文件，部署时只需在 Jenkins 上完成一次性配置：

| 文件 | 作用 |
|------|------|
| `Jenkinsfile` | 声明式流水线：装依赖 → 跑测试 → 生成Allure报告 → 生成邮件摘要 → 归档产物 → 发邮件；失败不中断，报告和邮件照发 |
| `utils/result_summary.py` | 解析 Allure 结果，生成邮件正文（`reports/email_summary.txt`）和HTML明细附件（`reports/email_summary.html`） |
| `.gitignore` | 忽略虚拟环境/日志/报告，供 git + SCM 方式使用 |

### 12.1 安装 Jenkins（本机已有 Java 17 可直接用）

1. 下载 LTS 版 `jenkins.war`：https://www.jenkins.io/download/
2. 启动：`java -jar jenkins.war --httpPort=8080`（或使用 Windows MSI 安装为服务）
3. 浏览器打开 http://localhost:8080，按提示用初始密码解锁、创建管理员账号
4. 插件选择"选择插件来安装"，确认包含 **Email Extension**（邮件通知必需）；可选装 **Allure**（在Jenkins页面内直接浏览Allure报告）

### 12.2 配置 SMTP 发件账号（以163邮箱为例）

> 注意：Jenkins 2.580 自带的 email-ext 插件较新，**没有"Use SMTP Authentication"勾选框**，认证改由 Credentials（凭据）承载，步骤如下。

Manage Jenkins → System：

1. **Jenkins Location** 区：System Admin e-mail address 填发件邮箱完整地址（如 `xxx@163.com`）；
2. **Extended E-mail Notification** 区（靠下，不是上面的"E-mail Notification"旧区）：
   - SMTP Server：`smtp.163.com`
   - SMTP Port：`465`
   - 点开 **Advanced** 展开：在 **Credentials** 下拉旁点 **+ Add → Jenkins**，弹窗中 Username 填完整邮箱地址、Password 填**授权码**（163邮箱网页版 → 设置 → POP3/SMTP/IMAP → 开启SMTP服务时生成，不是登录密码），Add 确认后下拉框选中该凭据
   - 勾选 **Use SSL**（Use TLS 不勾）；Charset：`UTF-8`
3. 上面旧的 **E-mail Notification** 区填同样的服务器/账号/授权码，可用其"Test configuration"按钮发测试邮件验证；
4. 页面拉到最底 **Save** 保存。

> 排查：构建日志出现 `553 authentication is required` 或 `Not sent to the following valid addresses` 说明凭据未生效，回到第2步确认 Credentials 已选中新建的凭据。

### 12.3 创建流水线任务

1. New Item → 输入任务名（如 `api-auto-test`）→ 选择 **Pipeline** → 确定
2. Pipeline 区域：Definition 选 **Pipeline script**，把 `Jenkinsfile` 的内容整段粘贴进 Script
3. 保存后先构建一次（让参数和定时触发注册到任务上），之后用 **Build with Parameters** 选择环境执行：
   - `ENV`：测试环境（来自 config.yaml）
   - `CONFIRM_PROD`：正式环境必须勾选才允许执行
   - `RECIPIENTS`：收件人邮箱，多个用英文逗号分隔；留空发给构建触发人
   - `PYTEST_ARGS`：附加pytest参数（如 `-m smoke`）

任务默认每天上午8点自动执行（Jenkinsfile 中 `triggers { cron('H 8 * * *') }`，按需修改）。无论成功失败都会发邮件：正文内嵌结果统计与未通过用例明细，附件带HTML明细、Allure报告压缩包和执行日志。

### 12.4 常见问题

- **Jenkins 找不到 python / allure**：Jenkins 服务账户的 PATH 与桌面环境不同。编辑 Jenkinsfile 顶部 `environment` 段，把 `PYTHON_EXE` / `ALLURE_EXE` 改成绝对路径（文件内已给出本机示例，取消注释即可）。
- **代码入 git 后改用 SCM 方式**：`git init` + 提交 + 推送到远端后，任务 Definition 改为 **Pipeline script from SCM** 指向仓库，并删除 Jenkinsfile 中 `customWorkspace` 那行（改为由 SCM 检出代码到工作区）。适合 Jenkins 与代码不同机或团队共用的情况。
- **邮件中文乱码**：确认 Extended E-mail Notification 的 Charset 为 UTF-8；仍乱码时给 Jenkins JVM 加 `-Dfile.encoding=UTF-8`。
- **Jenkins 部署在 Linux**：Jenkinsfile 中的 `bat` 步骤需改为 `sh`，并确认节点上已安装 Python 与 Allure。

## 13. 联系与反馈

如有问题或建议，欢迎反馈！

---

**版本**：v1.0.0  
**更新时间**：2025-12-11