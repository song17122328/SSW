# database.py - Schema Definition Only
import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_NAME = 'military_data.db'

def init_db():
    """初始化数据库，仅创建所有表结构。"""
    
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
        print(f"已删除旧数据库 {DB_NAME}")

    conn = sqlite3.connect(DB_NAME)
    # ** 关键：开启外键约束支持 **
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    # --- 用户表 ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    )
    ''')
    print("已创建 'users' 表")
    # 预置账户
    cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ('admin', generate_password_hash('admin123'), 'admin'))
    cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ('user', generate_password_hash('user123'), 'user'))
    print("已预置 admin/admin123 和 user/user123 账户")

    # --- 平台表 ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS platforms (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT,
        model_type TEXT,
        country TEXT,
        service_date TEXT,
        status TEXT NOT NULL DEFAULT '可用', -- 新增 status 字段
        details TEXT
    )
    ''')
    print("已创建 'platforms' 表 (含status字段)")
  
  
      # --- 装备表 ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS equipments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        type_code TEXT,
        category_text TEXT,
        status TEXT NOT NULL DEFAULT '可用', -- 新增 status 字段
        details TEXT
    )
    ''')
    print("已创建 'equipments' 表 (含status字段)")


    # --- 平台-装备关联表 (核心修正) ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS platform_equipment_link (
            platform_id INTEGER,
            equipment_id INTEGER,
            PRIMARY KEY (platform_id, equipment_id),
            FOREIGN KEY (platform_id) REFERENCES platforms (id) ON DELETE CASCADE,
            FOREIGN KEY (equipment_id) REFERENCES equipments (id) ON DELETE CASCADE
        )
    ''')
    print("已创建 'platform_equipment_link' 关联表 (已修正)")

    # --- 合同相关表 (保留) ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS contract_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        scenario TEXT,
        start_time TEXT,
        end_time TEXT,
        details TEXT 
    )
    ''')
    print("已创建 'contract_templates' 表")

# ** 核心修改：更新 contracts 表的结构 **
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            
            -- 核心顶层字段
            name TEXT NOT NULL,
            description TEXT,
            contract_type TEXT,          -- 新增: 'patrol', 'strike', etc.
            scenario_id INTEGER,         -- 新增: 关联的想定 ID
            side TEXT,                   -- 新增: 'RED' or 'BLUE'
            
            start_time TEXT,
            end_time TEXT,
            
            -- 其他所有内容都放入 details
            details TEXT, 
            
            -- 元数据
            status TEXT DEFAULT 'pending',
            creater TEXT,
            create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (scenario_id) REFERENCES sim_scenarios (id)
        )
    ''')
    print("已创建 'contracts' 表")

    # --- 作战想定相关表 (保留) ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sim_scenarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        scenario_code TEXT UNIQUE,
        type TEXT,
        creator TEXT,
        create_time TEXT,
        force_count INTEGER,
        details TEXT
    )
    ''')
    print("已创建 'sim_scenarios' 表")

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sim_platforms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scenario_id INTEGER,
        platform_id TEXT NOT NULL,
        name TEXT NOT NULL,
        team TEXT,
        type_name TEXT,
        lon REAL,
        lat REAL,
        alt REAL,
        heading REAL,
        FOREIGN KEY (scenario_id) REFERENCES sim_scenarios (id)
    )
    ''')
    print("已创建 'sim_platforms' 表")

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sim_equipments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        platform_db_id INTEGER,
        equipment_id TEXT,
        name TEXT NOT NULL,
        category TEXT,
        details TEXT,
        FOREIGN KEY (platform_db_id) REFERENCES sim_platforms (id)
    )
    ''')
    print("已创建 'sim_equipments' 表")
    conn.commit()
    conn.close()
    print("\n数据库表结构初始化完成！")
    print("下一步：请运行 python 1_populate_from_mapping.py 和 python 2_populate_extra_data.py 来填充数据。")

if __name__ == '__main__':
    init_db()
