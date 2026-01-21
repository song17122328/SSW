# convert_json.py

import json
from opencc import OpenCC

# 创建一个从繁体到简体的转换器实例
# 't2s.json' 是库内置的配置文件，代表 Traditional to Simplified
cc = OpenCC('t2s')  

# 定义输入和输出文件名
input_filename = 'platforms_details_fan.json'  # <--- 请将您的JSON数据保存到这个文件中
output_filename = 'platforms_details.json'
def convert_value(value):
    """递归地转换值，处理字符串、列表和字典。"""
    if isinstance(value, str):
        return cc.convert(value)
    elif isinstance(value, dict):
        # 键名也需要转换
        return {cc.convert(key): convert_value(val) for key, val in value.items()}
    elif isinstance(value, list):
        return [convert_value(item) for item in value]
    else:
        return value

try:
    with open(input_filename, 'r', encoding='utf-8') as f:
        data = json.load(f)

    simplified_data = convert_value(data)

    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(simplified_data, f, ensure_ascii=False, indent=4)

    print(f"✅ 转换成功！简体中文数据已保存到 '{output_filename}' 文件中。")

except FileNotFoundError:
    print(f"❌ 错误：找不到输入文件 '{input_filename}'。")
except json.JSONDecodeError:
    print(f"❌ 错误：'{input_filename}' 的JSON格式不正确。")
except Exception as e:
    print(f"❌ 发生未知错误: {e}")