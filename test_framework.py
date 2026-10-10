#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
框架功能验证脚本
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.yaml_parser import YamlParser
from utils.http_client import HttpClient
from utils.assertion import Assertion
from utils.config import Config, get_config


def test_yaml_parser():
    """测试YAML解析器"""
    print("\n=== 测试YAML解析器 ===")
    try:
        yaml_parser = YamlParser()
        test_file = "testcases/mock_test.yaml"
        
        if not os.path.exists(test_file):
            print(f"❌ 测试文件不存在: {test_file}")
            return False
            
        test_cases = yaml_parser.parse_test_cases(test_file)
        print(f"✅ 成功解析测试用例文件，共{len(test_cases)}个测试用例")
        
        for i, case in enumerate(test_cases, 1):
            print(f"  测试用例{i}: {case.get('name')}")
            print(f"    方法: {case['request'].get('method')}")
            print(f"    URL: {case['request'].get('url')}")
        
        return True
    except Exception as e:
        print(f"❌ YAML解析器测试失败: {str(e)}")
        return False


def test_config_loader():
    """测试配置加载器"""
    print("\n=== 测试配置加载器 ===")
    try:
        config = get_config()
        print(f"✅ 成功加载配置")
        print(f"  当前环境: {config.env}")
        print(f"  超时时间: {config.timeout}")
        print(f"  重试次数: {config.retry_times}")
        return True
    except Exception as e:
        print(f"❌ 配置加载器测试失败: {str(e)}")
        return False


def test_http_client():
    """测试HTTP客户端"""
    print("\n=== 测试HTTP客户端 ===")
    try:
        config = get_config()
        http_client = HttpClient(
            base_url=config.base_url,
            timeout=config.timeout
        )
        print(f"✅ HTTP客户端初始化成功")
        print(f"  基础URL: {http_client.base_url}")
        print(f"  超时时间: {http_client.timeout}")
        return True
    except Exception as e:
        print(f"❌ HTTP客户端测试失败: {str(e)}")
        return False


def test_assertion():
    """测试断言模块"""
    print("\n=== 测试断言模块 ===")
    try:
        assertion = Assertion()
        
        # 测试基本断言功能
        response = {
            'status_code': 200,
            'body': {
                'name': 'test',
                'value': 123,
                'data': [1, 2, 3]
            }
        }
        
        assertions = [
            {'type': 'status_code', 'expected': 200, 'message': '测试状态码'},
            {'type': 'equal', 'jsonpath': 'name', 'expected': 'test', 'message': '测试相等'},
            {'type': 'contains', 'jsonpath': 'data', 'expected': 2, 'message': '测试包含'}
        ]
        
        assertion.run_assertions(response, assertions)
        print("✅ 断言模块测试成功")
        return True
    except Exception as e:
        print(f"❌ 断言模块测试失败: {str(e)}")
        return False


if __name__ == "__main__":
    print("🔍 开始验证接口自动化测试框架功能")
    print(f"项目路径: {os.path.dirname(os.path.abspath(__file__))}")
    
    results = []
    results.append(test_config_loader())
    results.append(test_yaml_parser())
    results.append(test_http_client())
    results.append(test_assertion())
    
    print("\n=== 测试结果汇总 ===")
    passed = sum(results)
    total = len(results)
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("🎉 框架功能验证通过！")
        sys.exit(0)
    else:
        print("❌ 框架功能验证失败！")
        sys.exit(1)