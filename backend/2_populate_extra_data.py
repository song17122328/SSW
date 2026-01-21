# populate_extra_data.py - Script to populate ancillary data like templates and scenarios
import json
import sqlite3
import os
import time

# --- 配置区 ---
DB_NAME = 'military_data.db'
CONTRACT_TEMPLATES_DIR = 'mock_data/contract_templates'
SCENARIOS_DIR = 'mock_data/scenarios'

def process_scenario_file(cursor, filepath):
    """处理单个想定文件并将其内容插入到数据库中"""
    print(f"  -> Processing scenario file: {os.path.basename(filepath)}")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            experiment = data.get('experiment', {})
            forces_info = data.get('forcesInfo', [])
            
            name = experiment.get('name')
            if not name:
                print(f"     [Warning] File {os.path.basename(filepath)} lacks scenario name. Skipping.")
                return

            description = experiment.get('description')
            scenario_code = experiment.get('scenarioCode')
            type_name = experiment.get('typeName')
            creator = experiment.get('creator', '未知')
            create_time = experiment.get('createTime') or time.strftime("%Y-%m-%d %H:%M:%S")
            force_count = experiment.get('forcesCount') or len(forces_info)
            
            details_data = { k: v for k, v in data.items() if k not in ['experiment', 'forcesInfo'] }
            details_json = json.dumps(details_data, ensure_ascii=False)

            cursor.execute(
                "INSERT INTO sim_scenarios (name, description, scenario_code, type, creator, create_time, force_count, details) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (name, description, scenario_code, type_name, creator, create_time, force_count, details_json)
            )
            scenario_db_id = cursor.lastrowid

            for force in forces_info:
                if not isinstance(force, dict): continue
                cursor.execute(
                    "INSERT INTO sim_platforms (scenario_id, platform_id, name, team, type_name, lon, lat, alt, heading) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (scenario_db_id, force.get('id'), force.get('name'), force.get('team'), force.get('equipmentTypeName'),
                     force.get('lon'), force.get('lat'), force.get('alt'), force.get('heading'))
                )
                platform_db_id = cursor.lastrowid
                
                for item in force.get('parameterList', []):
                    if isinstance(item, dict):
                        details = {k: v for k, v in item.items() if k not in ['id', 'name']}
                        cursor.execute("INSERT INTO sim_equipments (platform_db_id, equipment_id, name, category, details) VALUES (?, ?, ?, ?, ?)",
                            (platform_db_id, item.get('id'), item.get('name'), 'sensor', json.dumps(details, ensure_ascii=False)))
                
                for item in force.get('relations', []):
                    if isinstance(item, dict):
                        details = {k: v for k, v in item.items() if k not in ['id', 'name']}
                        cursor.execute("INSERT INTO sim_equipments (platform_db_id, equipment_id, name, category, details) VALUES (?, ?, ?, ?, ?)",
                            (platform_db_id, item.get('id'), item.get('name'), 'weapon', json.dumps(details, ensure_ascii=False)))
    except json.JSONDecodeError:
        print(f"     [Error] Invalid JSON in file: {os.path.basename(filepath)}")
    except Exception as e:
        print(f"     [Error] Failed to process {os.path.basename(filepath)}: {e}")

def populate_extra_data():
    """将合同模板和作战想定数据填充到数据库中"""
    if not os.path.exists(DB_NAME):
        print(f"[错误] 数据库 '{DB_NAME}' 不存在。")
        print("请先运行 'python database.py' 和 'python populate_data.py'。")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # --- 1. 填充合同模板数据 ---
    print("\n--- 1. 正在填充合同模板数据 ---")
    try:
        if os.path.exists(CONTRACT_TEMPLATES_DIR) and os.path.isdir(CONTRACT_TEMPLATES_DIR):
            count = 0
            for filename in os.listdir(CONTRACT_TEMPLATES_DIR):
                if filename.endswith('.json'):
                    filepath = os.path.join(CONTRACT_TEMPLATES_DIR, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = json.load(f)
                        name = content.get('名称') or filename.replace('.json', '')
                        description = content.get('任务描述')
                        scenario = content.get('作战场景')
                        start_time = content.get('作战时间', {}).get('开始时间')
                        end_time = content.get('作战时间', {}).get('结束时间')
                        details_data = {k: v for k, v in content.items() if k not in ['名称', '任务描述', '作战场景', '作战时间']}
                        details_json = json.dumps(details_data, ensure_ascii=False)
                        
                        cursor.execute(
                            "INSERT INTO contract_templates (name, description, scenario, start_time, end_time, details) VALUES (?, ?, ?, ?, ?, ?)",
                            (name, description, scenario, start_time, end_time, details_json)
                        )
                        count += 1
            print(f"成功填充 {count} 条合同模板数据。")
        else:
            print(f"[信息] 未找到目录 '{CONTRACT_TEMPLATES_DIR}'，跳过填充合同模板。")
    except Exception as e:
        print(f"[错误] 填充合同模板数据时出错: {e}")
        conn.rollback()

    # --- 2. 填充作战想定数据 ---
    print("\n--- 2. 正在填充作战想定数据 ---")
    try:
        if os.path.exists(SCENARIOS_DIR) and os.path.isdir(SCENARIOS_DIR):
            count = 0
            for filename in os.listdir(SCENARIOS_DIR):
                if filename.endswith('.json'):
                    filepath = os.path.join(SCENARIOS_DIR, filename)
                    process_scenario_file(cursor, filepath)
                    count += 1
            print(f"处理了 {count} 个想定文件。")
        else:
            print(f"[信息] 未找到目录 '{SCENARIOS_DIR}'，跳过填充想定数据。")
    except Exception as e:
        print(f"[错误] 填充想定数据时出错: {e}")
        conn.rollback()
    
    finally:
        conn.commit()
        conn.close()
        print("\n附加数据填充完成！")


if __name__ == '__main__':
    populate_extra_data()