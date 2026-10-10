#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
接口自动化测试框架运行脚本
"""

import sys
import os
import subprocess
import argparse
import shutil
from pathlib import Path
from loguru import logger
import pytest

# 以本文件位置定位项目根目录，避免依赖启动时的当前工作目录
PROJECT_ROOT = Path(__file__).resolve().parent

ALLURE_RESULTS_DIR = PROJECT_ROOT / "reports" / "allure-results"
ALLURE_REPORT_DIR = PROJECT_ROOT / "reports" / "allure-report"

# 配置日志
logger.remove()
logger.add(
    sink=sys.stdout,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> <level>{level}</level> <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)


def install_dependencies():
    """安装依赖"""
    logger.info("开始安装项目依赖...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(PROJECT_ROOT / "requirements.txt")],
            check=True,
            shell=True
        )
        logger.success("依赖安装完成！")
    except subprocess.CalledProcessError as e:
        logger.error(f"依赖安装失败: {e}")
        sys.exit(1)


def clean_allure_results():
    """清理allure-results目录中的旧文件"""
    if ALLURE_RESULTS_DIR.exists():
        logger.info(f"清理Allure结果目录: {ALLURE_RESULTS_DIR}...")
        for file_name in os.listdir(ALLURE_RESULTS_DIR):
            file_path = ALLURE_RESULTS_DIR / file_name
            try:
                if file_path.is_file():
                    file_path.unlink()
                elif file_path.is_dir():
                    shutil.rmtree(file_path)
            except Exception as e:
                logger.error(f"清理文件 {file_path} 失败: {e}")


def run_tests(test_path="", allure_clean=True, env=None, confirm_prod=False):
    """运行测试"""
    logger.info("开始运行测试用例...")

    if allure_clean:
        clean_allure_results()

    # 构建pytest参数
    args = []

    # 添加测试路径
    if test_path:
        args.append(test_path)
    else:
        args.append(str(PROJECT_ROOT / "testcases" / "test_executor.py"))

    # 环境与正式环境确认（透传给conftest.py的自定义参数）
    if env:
        args.append(f"--env={env}")
    if confirm_prod:
        args.append("--confirm-prod")

    # 添加Allure参数
    args.append(f"--alluredir={ALLURE_RESULTS_DIR}")
    if allure_clean:
        args.append("--clean-alluredir")

    # 添加其他参数
    args.extend(["-v", "-s"])

    logger.info(f"Pytest 运行参数: {args}")

    try:
        # 直接在当前进程中运行pytest
        result = pytest.main(args)
        if result == 0:
            logger.success("测试运行完成！")
            return True
        else:
            logger.error(f"测试运行失败: 退出码 {result}")
            return False
    except Exception as e:
        logger.error(f"测试运行失败: {e}")
        return False


def generate_allure_report():
    """生成Allure报告"""
    logger.info("开始生成Allure报告...")

    try:
        # 检查allure是否安装
        result = subprocess.run(
            ["allure", "--version"],
            capture_output=True,
            text=True,
            shell=True
        )

        if result.returncode != 0:
            logger.error("Allure命令行工具未安装，请先安装Allure命令行工具")
            logger.info("Allure命令行工具安装方法:")
            logger.info("1. 下载Allure Commandline工具: https://github.com/allure-framework/allure2/releases")
            logger.info("2. 解压到本地目录")
            logger.info("3. 将解压目录下的bin文件夹添加到系统环境变量PATH中")
            logger.info("4. 重启命令行窗口后运行 'allure --version' 验证安装")
            logger.info(f"测试结果数据已保存在 {ALLURE_RESULTS_DIR} 目录中，安装Allure后可手动生成报告")
            return False

        # 生成报告
        subprocess.run(
            ["allure", "generate", str(ALLURE_RESULTS_DIR), "-o", str(ALLURE_REPORT_DIR), "--clean"],
            check=True,
            shell=True
        )
        logger.success("Allure报告生成完成！")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Allure报告生成失败: {e}")
        logger.info(f"测试结果数据已保存在 {ALLURE_RESULTS_DIR} 目录中，可手动生成报告")
        return False


def open_allure_report():
    """打开Allure报告"""
    logger.info("开始打开Allure报告...")

    try:
        subprocess.run(
            ["allure", "open", str(ALLURE_REPORT_DIR)],
            check=True,
            shell=True
        )
        logger.success("Allure报告已打开！")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Allure报告打开失败: {e}")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="接口自动化测试框架运行脚本")
    parser.add_argument("-i", "--install", action="store_true", help="安装项目依赖")
    parser.add_argument("-r", "--run", action="store_true", help="运行测试用例")
    parser.add_argument("-g", "--generate", action="store_true", help="生成Allure报告")
    parser.add_argument("-o", "--open", action="store_true", help="打开Allure报告")
    parser.add_argument("-a", "--all", action="store_true", help="执行完整流程：安装依赖 -> 运行测试 -> 生成报告 -> 打开报告")
    parser.add_argument("--test-path", type=str, default="", help="指定测试用例路径")
    parser.add_argument("--no-clean", action="store_true", help="不清理Allure报告结果目录")
    parser.add_argument("-e", "--env", type=str, default=None, help="测试环境名称，见 config/config.yaml 的 environments 段")
    parser.add_argument("--confirm-prod", action="store_true", help="确认在正式环境执行")

    args = parser.parse_args()

    # 执行完整流程
    if args.all:
        install_dependencies()
        if run_tests(args.test_path, not args.no_clean, args.env, args.confirm_prod):
            if generate_allure_report():
                open_allure_report()
        return

    # 安装依赖
    if args.install:
        install_dependencies()

    # 运行测试
    if args.run:
        run_tests(args.test_path, not args.no_clean, args.env, args.confirm_prod)

    # 生成报告
    if args.generate:
        generate_allure_report()

    # 如果没有指定任何参数，默认运行测试用例并生成报告
    if not any([args.all, args.install, args.run, args.generate, args.open]):
        logger.info("未指定参数，默认运行测试用例并生成报告...")
        if run_tests(args.test_path, not args.no_clean, args.env, args.confirm_prod):
            generate_allure_report()

    # 打开报告
    if args.open:
        open_allure_report()


if __name__ == "__main__":
    main()
