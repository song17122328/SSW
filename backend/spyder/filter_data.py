import json
import re

# --- 配置区 ---
INPUT_FILE = 'military_equipment_data.json'
OUTPUT_FILE = 'military_equipment_cleaned.json'
# 定义一个阈值，如果一个装备的有效信息板块少于这个数，就将其过滤掉
MINIMUM_SECTIONS_THRESHOLD = 2

def normalize_key(key):
    """
    标准化字典的键（节标题）。
    - 移除括号及其内容
    - 统一相似的名称
    """
    # 移除括号和其中的内容
    key = re.sub(r'（.*?）|\(.*?\)|\[.*?\]', '', key).strip()
    
    # 统一化处理
    if '概' in key:
        return '概况'
    if '技术数据' in key:
        return '技术数据'
    if '性能' in key:
        return '性能数据'
    if '武器' in key or '武装' in key:
        return '武器装备'
    
    return key

def clean_equipment_data(data):
    """
    清洗单个装备的数据字典。
    - 移除空字典
    - 标准化节标题
    - 移除无意义的顶层键
    """
    cleaned_data = {}
    
    # 定义一些无意义的、通常是重复标题的顶层键的模式
    junk_key_patterns = [
        r'uss', r'hms', r'cvn', r'r09', r'ddg', 'class', r'[a-zA-Z]{1,2}-\d+',
        r'号', r'艦', r'機', r'级', '式', '型', '（', '）', '「', '」',
        'Frégates', 'ТАКР'
    ]

    for section_title, section_content in data.items():
        # 过滤掉空的子字典
        if not isinstance(section_content, dict) or not section_content:
            continue

        # 检查节标题是否是无意义的重复标题
        is_junk = False
        # 将标题转为小写以进行不区分大小写的匹配
        lower_title = section_title.lower()
        for pattern in junk_key_patterns:
            if re.search(pattern, lower_title):
                is_junk = True
                break
        
        if is_junk:
            # 如果标题被识别为垃圾信息，跳过这个部分
            # 这可以有效去除像 "F-14「雄貓」F-14 Tomcat": {} 这样的条目
            continue
            
        # 标准化有效的节标题
        normalized_title = normalize_key(section_title)
        cleaned_data[normalized_title] = section_content
        
    return cleaned_data

def main():
    """主函数，加载、过滤并保存数据"""
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        print(f"成功从 '{INPUT_FILE}' 加载了 {len(raw_data)} 条装备数据。")
    except FileNotFoundError:
        print(f"[错误] 输入文件 '{INPUT_FILE}' 未找到。请确保文件名正确且文件在同一目录下。")
        return
    except json.JSONDecodeError as e:
        print(f"[错误] 解析JSON文件时出错: {e}")
        return

    filtered_data = {}
    removed_items = []

    for name, data in raw_data.items():
        # 第一步：清洗单个装备内部的数据
        cleaned_item = clean_equipment_data(data)
        
        # 第二步：检查清洗后的数据是否满足阈值要求
        if len(cleaned_item) >= MINIMUM_SECTIONS_THRESHOLD:
            # 如果有效板块数量足够，则保留
            filtered_data[name] = cleaned_item
            print(f"  [保留] {name} (包含 {len(cleaned_item)} 个有效板块)")
        else:
            # 否则，记录为被移除项
            removed_items.append(name)
            print(f"  [移除] {name} (有效板块不足)")
            
    # 保存过滤后的数据
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(filtered_data, f, ensure_ascii=False, indent=4)
        
        print("\n--- 过滤完成 ---")
        print(f"保留了 {len(filtered_data)} 条数据。")
        print(f"移除了 {len(removed_items)} 条数据: {', '.join(removed_items)}")
        print(f"清洗后的数据已保存到 '{OUTPUT_FILE}'。")

    except IOError as e:
        print(f"\n[错误] 写入文件时出错: {e}")


if __name__ == "__main__":
    main()