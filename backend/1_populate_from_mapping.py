# 2_populate_from_mapping.py
import json
import sqlite3
import os

# --- 配置区: 定义所有输入文件 ---
DB_NAME = 'military_data.db'
INPUT_PLATFORMS_LIST_FILE = 'platforms_list_clean.json'
INPUT_PLATFORMS_DETAILS_FILE = 'platforms_details.json'

# 关键：使用您指定的、手动清洗过的最终文件作为权威数据源
INPUT_MAPPING_FILE = 'equipment_mapping_clean.json' 

def main():
    """
    将平台和校对过的装备数据填充到数据库中，并建立关联。
    这是数据加载（Load）阶段的核心脚本。
    """
    # --- 检查先决条件 ---
    required_files = [DB_NAME, INPUT_PLATFORMS_LIST_FILE, INPUT_PLATFORMS_DETAILS_FILE, INPUT_MAPPING_FILE]
    for f in required_files:
        if not os.path.exists(f):
            print(f"[错误] 必需文件 '{f}' 不存在。请确保所有准备和校对步骤已完成。")
            if f == DB_NAME:
                print("-> 请先运行 'python database.py'")
            elif f.endswith('.json'):
                 print(f"-> 请先确保 '{f}' 文件存在于当前目录。")
            return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # --- 1. 填充平台数据 ---
    print("--- 1. 正在填充平台数据 ---")
    try:
        # 清空现有平台数据，以防重复运行导致问题
        cursor.execute("DELETE FROM platforms;")
        cursor.execute("DELETE FROM platform_equipment_link;") # 清空旧关联
        print("  -> 已清空旧的平台和关联数据。")

        with open(INPUT_PLATFORMS_LIST_FILE, 'r', encoding='utf-8') as f_list, \
             open(INPUT_PLATFORMS_DETAILS_FILE, 'r', encoding='utf-8') as f_details:
            
            platform_list = json.load(f_list)
            platform_details = json.load(f_details)
            
            for item in platform_list:
                platform_id = item.get('id')
                details_data = platform_details.get(str(platform_id), {})
                details_json = json.dumps(details_data, ensure_ascii=False)
                
                cursor.execute(
                    "INSERT INTO platforms (id, name, category, model_type, country, service_date, details) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (platform_id, item.get('name'), item.get('category'), item.get('model_type'), item.get('country'), item.get('service_date'), details_json)
                )
        print(f"成功填充 {len(platform_list)} 条平台数据。")
    except Exception as e:
        print(f"错误: 填充平台数据时出错: {e}")
        conn.close()
        return

    # --- 2. 填充装备数据 (从干净的源文件) ---
    print("\n--- 2. 正在填充装备数据 ---")
    try:
        # 清空现有装备数据
        cursor.execute("DELETE FROM equipments;")
        print("  -> 已清空旧的装备数据。")

        with open(INPUT_MAPPING_FILE, 'r', encoding='utf-8') as f:
            mapping_data = json.load(f)

        # 提取所有唯一的、非空的 cleaned_name
        clean_equipments = {} # name -> {type_code, category_text}
        for raw_name, data in mapping_data.items():
            cleaned_name = data.get('cleaned_name')
            if cleaned_name: # 过滤掉被设为 null 或空字符串的条目
                if cleaned_name not in clean_equipments:
                    clean_equipments[cleaned_name] = {
                        "type_code": data.get("type_code"),
                        "category_text": data.get("category_text")
                    }
        
        for name, data in clean_equipments.items():
            cursor.execute(
                "INSERT INTO equipments (name, type_code, category_text) VALUES (?, ?, ?)",
                (name, data["type_code"], data["category_text"])
            )
        print(f"成功从 '{INPUT_MAPPING_FILE}' 填充了 {len(clean_equipments)} 条干净的装备数据。")
    except Exception as e:
        print(f"错误: 填充装备数据时出错: {e}")
        conn.close()
        return

    # --- 3. 根据映射文件创建平台-装备关联 ---
    print("\n--- 3. 正在根据映射文件创建关联 ---")
    
    # 首先，加载所有刚刚插入的干净装备及其ID到内存中，方便快速查找
    cursor.execute("SELECT id, name FROM equipments")
    db_equipments_map = {name: id for id, name in cursor.fetchall()}
    
    link_count = 0
    # 再次遍历映射文件
    for raw_name, data in mapping_data.items():
        cleaned_name = data.get('cleaned_name')
        if not cleaned_name:
            continue # 跳过被删除的条目
            
        # 查找这个干净名称在数据库中的ID
        equipment_id = db_equipments_map.get(cleaned_name)
        if not equipment_id:
            print(f"警告: 找不到装备 '{cleaned_name}' 的ID，跳过关联。")
            continue
            
        # 为这个原始名称关联的所有平台创建链接
        for platform_id_str in data.get("platforms", []):
            platform_id = int(platform_id_str)
            try:
                cursor.execute(
                    "INSERT INTO platform_equipment_link (platform_id, equipment_id) VALUES (?, ?)",
                    (platform_id, equipment_id)
                )
                if cursor.rowcount > 0:
                    link_count += 1
            except sqlite3.IntegrityError:
                # 关联已存在，忽略 (例如多个原始条目合并为一个干净条目，可能会重复插入)
                pass

    print(f"成功创建了 {link_count} 条平台与装备的关联。")
    
    conn.commit()
    conn.close()
    print("\n核心数据填充完成！")

if __name__ == '__main__':
    main()