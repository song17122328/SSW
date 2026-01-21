# 1_extract_for_mapping.py
import json
import re
from collections import defaultdict

# --- 配置区 ---
INPUT_DETAILS_FILE = 'platforms_details.json' 
OUTPUT_MAPPING_FILE = 'equipment_mapping.json'

# --- 辅助函数 (与之前类似，但现在只用于初步分类) ---
def classify_equipment(name):
    name_lower = name.lower()
    if any(k in name_lower for k in ['雷达', '声纳', '侦搜', 'irst', 'rwr', 'maws', 'esm', '光电', 'sps', 'spq', 'spy', 'sqs', 'slq-32']): return 'S', '感知系统'
    if any(k in name_lower for k in ['导弹', '机炮', '鱼雷', '火箭', '炸弹', '砲', '炮', '飛彈', '发射器', '發射器', 'rim-', 'mk ', 'ak-']): return 'A', '武器系统'
    if any(k in name_lower for k in ['電戰', 'ecm', '干扰', '数据链', '反制', '诱饵', 'slq-25']): return 'C', '指控/电战'
    return 'U', '其他'

def extract_raw_names(text_blob):
    """只做最基础的分割，保留原始的、未清洗的名称片段"""
    if not isinstance(text_blob, str):
        return set()
    normalized_text = text_blob.replace('、', '\n').replace(';', '\n').replace('/', '\n')
    raw_names = set()
    for line in normalized_text.split('\n'):
        candidate = line.strip()
        if candidate:
            raw_names.add(candidate)
    return raw_names

def main():
    """从平台详情中提取原始装备名称及其来源平台，生成映射文件供人工校对。"""
    try:
        with open(INPUT_DETAILS_FILE, 'r', encoding='utf-8') as f:
            platform_details = json.load(f)
    except FileNotFoundError:
        print(f"错误: 输入文件 '{INPUT_DETAILS_FILE}' 未找到。")
        return

    # 使用 defaultdict 来自动处理新键
    equipment_map = defaultdict(lambda: {"platforms": set()})

    for platform_id_str, details in platform_details.items():
        platform_name = details.get('概况', {}).get('舰种', details.get('概况', {}).get('類型', f"平台ID {platform_id_str}"))

        text_blob = " \n ".join(filter(None, [
            details.get('武器装备', {}).get('武器裝備', ''),
            details.get('技术数据', {}).get('偵搜系统', ''),
            details.get('技术数据', {}).get('電戰系统', ''),
            details.get('技术数据', {}).get('電子設備', '')
        ]))
        
        raw_names = extract_raw_names(text_blob)
        for raw_name in raw_names:
            equipment_map[raw_name]["platforms"].add(platform_id_str)

    # 转换成最终的JSON结构
    final_mapping = {}
    for raw_name, data in sorted(equipment_map.items()):
        type_code, category_text = classify_equipment(raw_name)
        final_mapping[raw_name] = {
            "cleaned_name": raw_name, # 初始值设为原始名称
            "type_code": type_code,
            "category_text": category_text,
            "platforms": sorted(list(data["platforms"]))
        }

    try:
        with open(OUTPUT_MAPPING_FILE, 'w', encoding='utf-8') as f:
            json.dump(final_mapping, f, ensure_ascii=False, indent=4)
        print(f"成功提取 {len(final_mapping)} 条原始装备记录。")
        print(f"数据已保存到 '{OUTPUT_MAPPING_FILE}'，请打开此文件进行人工校对。")
        print("说明：请修改每个条目的 'cleaned_name', 'type_code', 'category_text'。")
        print("将 'cleaned_name' 设为 null 或空字符串来删除该条目。")
        print("将多个条目的 'cleaned_name' 设为同一个标准名称来进行合并。")
    except IOError as e:
        print(f"错误: 写入文件失败: {e}")

if __name__ == '__main__':
    main()