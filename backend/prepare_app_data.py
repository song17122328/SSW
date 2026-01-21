import json
import uuid # 也可以使用 uuid，但自增整数更简洁

# --- 配置区 ---
# 输入文件现在是清洗后的原始数据
INPUT_FILE = 'military_equipment_cleaned.json' 
# 输出两个独立的文件
OUTPUT_LIST_FILE = 'platforms_list.json'
OUTPUT_DETAILS_FILE = 'platforms_details.json'

# --- 辅助函数 (保持不变) ---
def get_classification(name, details):
    CLASSIFICATION_MAP = {
        '航空母舰': '舰艇', '驱逐舰': '舰艇', '巡防舰': '舰艇',
        '护卫舰': '舰艇', '攻击舰': '舰艇', '潜艇': '舰艇', '核潜艇': '舰艇',
        '战斗机': '飞机', '攻击机': '飞机', '轰炸机': '飞机', '运输机': '飞机',
        '侦察机': '飞机', '预警机': '飞机', '直升机': '飞机', '无人机': '飞机'
    }
    for keyword, category in CLASSIFICATION_MAP.items():
        if keyword in name:
            return category, keyword
    overview = details.get('概况', {})
    model_type_str = overview.get('舰种') or overview.get('类型') or overview.get('類型')
    if model_type_str:
        for keyword, category in CLASSIFICATION_MAP.items():
            if keyword in model_type_str:
                return category, keyword
    return '未知', '未知'

def get_country(details):
    overview = details.get('概况', {})
    country_str = overview.get('拥有国') or overview.get('主要用户') or overview.get('原产国')
    if country_str:
        return country_str.split('/')[0].split(' ')[0].strip()
    return '未知'

def get_service_date(details):
    overview = details.get('概况', {})
    history = details.get('历史', {})
    date_str = overview.get('服役') or overview.get('入役日期') or history.get('起役日期')
    if date_str:
        return date_str.strip()
    return '未知'

def main():
    """主函数，加载、处理并保存为两个独立的、带唯一ID的JSON文件"""
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            # 输入文件现在是清洗后的数据，结构是 { "平台名": {详情...} }
            cleaned_data = json.load(f)
        print(f"成功从 '{INPUT_FILE}' 加载了 {len(cleaned_data)} 条装备数据。")
    except FileNotFoundError:
        print(f"[错误] 输入文件 '{INPUT_FILE}' 未找到。请先运行数据过滤脚本。")
        return

    platform_list = []
    platform_details = {}
    
    # *** 核心改动：引入自增 ID ***
    current_id = 1

    for name, details in cleaned_data.items():
        # 为每个平台提取摘要信息
        category, model_type = get_classification(name, details)
        country = get_country(details)
        service_date = get_service_date(details)
        
        summary = {
            # *** 使用新的数字 ID ***
            "id": current_id, 
            "name": name, # platform_name 简化为 name
            "category": category,
            "model_type": model_type,
            "country": country,
            "service_date": service_date,
        }
        platform_list.append(summary)
        
        # *** 使用新的数字 ID 作为 details 字典的键 ***
        platform_details[str(current_id)] = details
        
        print(f"  处理完成: {name} -> 分配 ID: {current_id}")
        
        # ID自增
        current_id += 1

    # --- 保存为两个独立的文件 ---

    # 1. 保存列表文件
    try:
        with open(OUTPUT_LIST_FILE, 'w', encoding='utf-8') as f:
            json.dump(platform_list, f, ensure_ascii=False, indent=4)
        print(f"\n摘要列表已保存到 '{OUTPUT_LIST_FILE}' ({len(platform_list)} 条记录)。")
    except IOError as e:
        print(f"\n[错误] 写入列表文件时出错: {e}")

    # 2. 保存详情文件
    try:
        with open(OUTPUT_DETAILS_FILE, 'w', encoding='utf-8') as f:
            json.dump(platform_details, f, ensure_ascii=False, indent=4)
        print(f"详细数据已保存到 '{OUTPUT_DETAILS_FILE}' ({len(platform_details)} 条记录)。")
    except IOError as e:
        print(f"\n[错误] 写入详情文件时出错: {e}")


if __name__ == "__main__":
    main()