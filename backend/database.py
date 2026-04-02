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

    print("\n" + "=" * 70)
    print("  ✅ 数据库表结构初始化完成！")
    print("=" * 70)
    print("\n📋 接下来请按顺序运行以下脚本来填充数据：\n")

    print("  步骤 1️⃣  填充平台和装备基础数据")
    print("  ─────────────────────────────────────────────────────")
    print("    python3 1_populate_from_mapping.py")
    print("")
    print("    ✓ 填充 20 个平台（航母、驱逐舰、护卫舰、潜艇、飞机等）")
    print("    ✓ 填充 63 个装备（雷达、导弹、电子战系统等）")
    print("    ✓ 创建平台与装备的关联关系")
    print("")

    print("  步骤 2️⃣  填充合同模板和作战想定")
    print("  ─────────────────────────────────────────────────────")
    print("    python3 2_populate_extra_data.py")
    print("")
    print("    ✓ 填充 8 个合同模板（打击、巡逻、侦察、防御等）")
    print("    ✓ 填充 2 个作战想定（对海、对空场景）")
    print("")

    print("  步骤 3️⃣  填充装备详细参数 (Details)")
    print("  ─────────────────────────────────────────────────────")
    print("    python3 3_populate_equipment_details.py")
    print("")
    print("    ✓ 为 63 个装备生成详细技术参数")
    print("    ✓ 感知类(S): 探测距离、频率范围、目标容量等")
    print("    ✓ 控制类(C): 传输速率、加密等级、网络拓扑等")
    print("    ✓ 执行类(A): 射程、制导方式、速度、打击能力等")
    print("")

    print("  步骤 4️⃣  初始化 PCCS 资源池")
    print("  ─────────────────────────────────────────────────────")
    print("    python3 init_pccs_pool.py")
    print("")
    print("    ✓ 从数据库加载平台和装备")
    print("    ✓ 转换为 PCCS 四维度资源（Perception/Control/Capability/State）")
    print("    ✓ 注册到全局资源池，支持智能任务匹配")
    print("")

    print("=" * 70)
    print("  💡 提示：启动后端服务时会自动执行步骤 4")
    print("       运行 python3 app.py 即可启动完整系统")
    print("=" * 70)
    print("")

if __name__ == '__main__':
    init_db()
