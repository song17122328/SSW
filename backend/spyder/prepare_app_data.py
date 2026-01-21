import json

# --- 配置区 ---
INPUT_FILE = 'military_equipment_cleaned.json'
OUTPUT_FILE = 'platform_data_for_app.json'

# --- 辅助函数：用于从复杂数据中提取信息 ---

def get_classification(name, details):
    """
    智能推断平台的分类和型号。
    返回一个元组 (category, model_type)
    """
    # 定义关键字和其对应的分类
    CLASSIFICATION_MAP = {
        # 舰艇类
        '航空母舰': '舰艇', '驱逐舰': '舰艇', '巡防舰': '舰艇',
        '护卫舰': '舰艇', '攻击舰': '舰艇', '潜艇': '舰艇', '核潜艇': '舰艇',
        # 飞机类
        '战斗机': '飞机', '攻击机': '飞机', '轰炸机': '飞机', '运输机': '飞机',
        '侦察机': '飞机', '预警机': '飞机', '直升机': '飞机', '无人机': '飞机'
    }
    
    # 1. 优先从平台名称中匹配关键字
    for keyword, category in CLASSIFICATION_MAP.items():
        if keyword in name:
            return category, keyword
            
    # 2. 如果名称中没有，则从“概况”详情中查找
    overview = details.get('概况', {})
    # 舰艇通常用 '舰种', 飞机用 '类型' 或 '類型'
    model_type_str = overview.get('舰种') or overview.get('类型') or overview.get('類型')
    
    if model_type_str:
        # 再次用关键字匹配提取出的型号字符串
        for keyword, category in CLASSIFICATION_MAP.items():
            if keyword in model_type_str:
                return category, keyword
    
    # 3. 如果都找不到，返回未知
    return '未知', '未知'

def get_country(details):
    """从详情中提取国别信息"""
    overview = details.get('概况', {})
    # 检查多个可能的键
    country_str = overview.get('拥有国') or overview.get('主要用户') or overview.get('原产国')
    if country_str:
        # 有些国别是 "美国 / 澳大利亚" 这种格式，我们只取第一个
        return country_str.split('/')[0].split(' ')[0].strip()
    return '未知'

def get_service_date(details):
    """从详情中提取服役时间"""
    overview = details.get('概况', {})
    history = details.get('历史', {})
    # 检查多个可能的键
    date_str = overview.get('服役') or overview.get('入役日期') or history.get('起役日期')
    if date_str:
        return date_str.strip()
    return '未知'


def main():
    """主函数，加载、处理并保存应用所需的数据"""
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            cleaned_data = json.load(f)
        print(f"成功从 '{INPUT_FILE}' 加载了 {len(cleaned_data)} 条装备数据。")
    except FileNotFoundError:
        print(f"[错误] 输入文件 '{INPUT_FILE}' 未找到。请先运行数据过滤脚本。")
        return

    platform_list = []
    
    for name, details in cleaned_data.items():
        # 为每个平台提取摘要信息
        category, model_type = get_classification(name, details)
        country = get_country(details)
        service_date = get_service_date(details)
        
        summary = {
            # 增加一个唯一ID，方便前端处理（例如在React中用作key）
            "id": name, 
            "platform_name": name,
            "category": category,
            "model_type": model_type,
            "country": country,
            "service_date": service_date,
        }
        platform_list.append(summary)
        print(f"  处理完成: {name}")

    # 构建最终的输出结构
    app_data = {
        # 用于列表页的数据
        "platform_list": platform_list,
        # 用于详情页的数据，直接使用我们清洗后的完整数据
        "platform_details": cleaned_data
    }

    # 保存为新的JSON文件
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(app_data, f, ensure_ascii=False, indent=4)
        print(f"\n处理成功！应用所需的数据已保存到 '{OUTPUT_FILE}'。")
        print(f"文件包含 'platform_list' ({len(platform_list)} 条摘要) 和 'platform_details' ({len(cleaned_data)} 条详情)。")

    except IOError as e:
        print(f"\n[错误] 写入文件时出错: {e}")

if __name__ == "__main__":
    main()