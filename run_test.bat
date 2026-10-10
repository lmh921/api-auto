@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: 脚本名称
set SCRIPT_NAME=接口自动化测试框架

:: 颜色设置
color 0A

echo ====================================================
echo %SCRIPT_NAME%
echo ====================================================
echo.

:: 安装依赖
echo 1. 安装项目依赖
echo 2. 运行测试用例
echo 3. 生成Allure报告
echo 4. 打开Allure报告
echo 5. 执行完整流程（安装依赖->运行测试->生成报告->打开报告）
echo 6. 退出
echo.

:menu
set /p choice=请选择操作 (1-6): 

if "%choice%"=="1" goto install
if "%choice%"=="2" goto run
if "%choice%"=="3" goto generate
if "%choice%"=="4" goto open
if "%choice%"=="5" goto all
if "%choice%"=="6" goto exit

:install
echo.
echo ====================================================
echo 正在安装项目依赖...
echo ====================================================
pip install -r requirements.txt
if %errorlevel%==0 (
    echo 依赖安装完成！
) else (
    echo 依赖安装失败！
)
echo.
goto menu

:run
echo.
echo ====================================================
echo 正在运行测试用例...
echo ====================================================
python -m pytest --alluredir=reports/allure-results --clean-alluredir -v -s
if %errorlevel%==0 (
    echo 测试运行完成！
) else (
    echo 测试运行失败！
)
echo.
goto menu

:generate
echo.
echo ====================================================
echo 正在生成Allure报告...
echo ====================================================
allure generate reports/allure-results -o reports/allure-report --clean
if %errorlevel%==0 (
    echo Allure报告生成完成！
) else (
    echo Allure报告生成失败！请确保已安装Allure命令行工具。
)
echo.
goto menu

:open
echo.
echo ====================================================
echo 正在打开Allure报告...
echo ====================================================
allure open reports/allure-report
if %errorlevel%==0 (
    echo Allure报告已打开！
) else (
    echo Allure报告打开失败！请确保已安装Allure命令行工具。
)
echo.
goto menu

:all
echo.
echo ====================================================
echo 执行完整流程...
echo ====================================================
echo 1/4: 安装依赖...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo 依赖安装失败！
    goto menu
)

echo 2/4: 运行测试...
python -m pytest --alluredir=reports/allure-results --clean-alluredir -v -s
if %errorlevel% neq 0 (
    echo 测试运行失败！
    goto menu
)

echo 3/4: 生成报告...
allure generate reports/allure-results -o reports/allure-report --clean
if %errorlevel% neq 0 (
    echo Allure报告生成失败！
    goto menu
)

echo 4/4: 打开报告...
allure open reports/allure-report
echo.
echo 完整流程执行完成！
echo.
goto menu

:exit
echo.
echo 感谢使用%SCRIPT_NAME%！
echo 按任意键退出...
pause >nul
endlocal