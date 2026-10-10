#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试脚本：手动运行测试用例
"""
from utils.yaml_parser import YamlParser
from utils.http_client import HttpClient
from utils.assertion import Assertion
from utils.config import get_config

# 加载全局配置（可指定环境，如 get_config("client-dev")）
config = get_config()

# 初始化组件
yaml_parser = YamlParser()
http_client = HttpClient(
    base_url=config.base_url,
    timeout=config.timeout
)
assertion = Assertion()

# 测试用例文件路径
file_path = 'data/client_data/selectUser_test.yaml'

# 全局变量（预置配置 variables 段）
global_vars = dict(config.variables)

print(f"开始调试测试用例文件: {file_path}")

# 解析测试用例
test_cases = yaml_parser.parse_test_cases(file_path)
print(f"解析到的测试用例数量: {len(test_cases)}")

for i, case in enumerate(test_cases):
    print(f"\n=== 执行测试用例 {i+1}: {case.get('name', '未命名测试用例')} ===")
    
    # 替换变量
    print(f"当前全局变量: {global_vars}")
    request_data = yaml_parser.replace_variables(case['request'], global_vars)
    print(f"替换后的请求数据: {request_data}")
    
    # 发送请求
    method = request_data['method'].upper()
    url = request_data['url']
    
    # 准备请求参数
    kwargs = {}
    if 'params' in request_data:
        kwargs['params'] = request_data['params']
    if 'headers' in request_data:
        kwargs['headers'] = request_data['headers']
    if 'body' in request_data:
        kwargs['data'] = request_data['body']
    if 'json' in request_data:
        kwargs['json'] = request_data['json']
    if 'files' in request_data:
        kwargs['files'] = request_data['files']
    
    print(f"发送请求: {method} {url}")
    print(f"请求参数: {kwargs}")
    
    # 发送请求
    response = http_client.request(method, url, **kwargs)
    print(f"响应状态码: {response['status_code']}")
    print(f"响应体: {response['body']}")
    
    # 执行断言
    if 'assertions' in case:
        print(f"\n执行断言: {case['assertions']}")
        try:
            assertion.run_assertions(response, case['assertions'])
            print("断言通过")
        except AssertionError as e:
            print(f"断言失败: {e}")
    
    # 提取变量
    if 'extract' in case:
        print(f"\n提取变量: {case['extract']}")
        for var_name, jsonpath in case['extract'].items():
            try:
                var_value = assertion.get_value_from_jsonpath(response['body'], jsonpath)
                global_vars[var_name] = var_value
                print(f"成功提取变量: {var_name} = {var_value}")
                print(f"更新后的全局变量: {global_vars}")
            except Exception as e:
                print(f"提取变量失败: {var_name}, 错误: {str(e)}")
                raise

# 关闭HTTP客户端
try:
    http_client.session.close()
except:
    pass

print("\n=== 调试结束 ===")
