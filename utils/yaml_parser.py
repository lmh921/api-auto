import os
import re
from typing import Any, Dict, List

import yaml
from loguru import logger

# ${var} 占位符
VAR_PATTERN = re.compile(r"\$\{([^}]+)\}")


class YamlParser:
    """YAML测试用例解析器"""

    def __init__(self):
        pass

    def load_file(self, file_path: str) -> Dict[str, Any]:
        """加载YAML文件"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"测试用例文件不存在: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def parse_test_cases(self, file_path: str) -> List[Dict[str, Any]]:
        """解析测试用例"""
        data = self.load_file(file_path)
        test_cases = []

        # 增加类型检查和验证
        if isinstance(data, dict):
            if 'name' in data and 'request' in data:
                # 处理单接口用例
                if isinstance(data['request'], dict):
                    test_cases.append(data)
                else:
                    print(f"警告: request字段类型错误: {type(data['request'])}")

            elif 'testcases' in data:
                # 处理多接口用例集
                if isinstance(data['testcases'], list):
                    for case in data['testcases']:
                        if isinstance(case, dict) and 'name' in case and 'request' in case:
                            test_cases.append(case)
                        else:
                            print(f"警告: 跳过无效用例: {case}")
                else:
                    print(f"错误: testcases应该是列表，实际是{type(data['testcases'])}")

        return test_cases

    def replace_variables(self, data: Any, variables: Dict[str, Any]) -> Any:
        """替换变量

        规则：
        - 字符串整体就是一个占位符（如 "${user_id}"）时，替换为变量的原始值，保留类型
          （数字、布尔、字典、列表等不会被转成字符串，用于断言比较不会出现 "1" != 1）
        - 占位符嵌在字符串中间（如 "Bearer ${token}"）时，做字符串插值
        - 未定义的变量保留原文，便于排查
        """
        if isinstance(data, str):
            return self._replace_in_string(data, variables)
        elif isinstance(data, dict):
            return {k: self.replace_variables(v, variables) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.replace_variables(item, variables) for item in data]
        else:
            return data

    def _replace_in_string(self, text: str, variables: Dict[str, Any]) -> Any:
        """对单个字符串做变量替换"""
        # 整串占位符：保留变量原始类型
        full_match = VAR_PATTERN.fullmatch(text)
        if full_match:
            key = full_match.group(1)
            if key in variables:
                return variables[key]
            logger.debug(f"变量未定义，保留原文: {text}")
            return text

        # 嵌入式占位符：字符串插值
        def _sub(match: "re.Match") -> str:
            key = match.group(1)
            if key in variables:
                return str(variables[key])
            logger.debug(f"变量未定义，保留原文: {match.group(0)}")
            return match.group(0)

        return VAR_PATTERN.sub(_sub, text)
