import sqlite3
import json
import time
from flask import Flask, jsonify, g, request
from flask_cors import CORS
import database
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session # 引入 session 用于状态管理
import traceback
import os
from flask_socketio import SocketIO, join_room, emit
import threading, json
from train import train_stream
from eval import eval_run
from pathlib import Path
import tempfile
import requests
import shutil  # ★ 新增：用于在评估时复用训练任务的 Task/Resource
import re, hashlib

ADMIN_INVITE_CODE = '9999'
app = Flask(__name__)
Path("jobs").mkdir(parents=True, exist_ok=True)
app.config['JSON_AS_ASCII'] = False
app.secret_key = 'a_very_secret_and_complex_key_for_session' 


# ==========================================================
# *** 核心修改：添加 Session Cookie 配置 ***
# ==========================================================
# 判断是否在生产环境，虽然你现在是开发环境，但这是个好习惯
# IS_PRODUCTION = os.environ.get('FLASK_ENV') == 'production'

# app.config.update(
#     # 设置 SameSite=None 允许跨域发送Cookie
#     SESSION_COOKIE_SAMESITE='None', 
#     # SameSite=None 必须配合 Secure=True (只能通过HTTPS发送)
#     # 在本地HTTP开发中，这是一个难题。
#     # 大多数现代浏览器对 localhost 有豁免，允许 Secure=False 和 SameSite=None 共存。
#     SESSION_COOKIE_SECURE=True if IS_PRODUCTION else False
# )
# ==========================================================

CORS(app, supports_credentials=True, origins=['http://localhost:8080']) # 允许跨域携带cookie

socketio = SocketIO(
    app,
    cors_allowed_origins=['http://localhost:8080'],  # 与前端域一致
    async_mode='eventlet',
    ping_timeout=120,
    ping_interval=25,
)

# --- 新增：任务管理（房间=job:{job_id}） ---
JOBS = {}  # job_id -> {"task": <bg task>, "stop": threading.Event()}

def _emit_job(job_id: str, event: str, payload: dict):
    """向 job 房间广播，并在 eventlet 下让出执行权，保障心跳"""
    room = f"job:{job_id}"
    socketio.emit(event, payload, room=room)
    try:
        socketio.sleep(0)
    except Exception:
        pass


def _fs_job_id(job_id: str) -> str:
    """
    把任意 job_id 安全化为文件系统可用的 ASCII 名称：
    - 非 [A-Za-z0-9._-] 的字符替换为 '_'
    - 若发生变化，追加 6 位 md5 以避免重名
    仅用于磁盘目录名；socket 房间名/事件里仍然用原始 job_id。
    """
    s = str(job_id)
    safe = re.sub(r'[^A-Za-z0-9._-]+', '_', s)
    if safe != s:
        suf = hashlib.md5(s.encode('utf-8')).hexdigest()[:6]
        safe = f"{safe}_{suf}"
    return safe

def _as_bool(x, default=False):
    if x is None: 
        return default
    if isinstance(x, bool): 
        return x
    if isinstance(x, (int, float)): 
        return x != 0
    if isinstance(x, str): 
        return x.strip().lower() in ("1","true","yes","y","on","t")
    return default

def _materialize_job_dirs_from_db(job_id: str, meta: dict) -> tuple[str, str]:
    """
    直接从 DB 读取合同与想定，落地为:
      jobs/{job_id}/Task/*.json
      jobs/{job_id}/Resource/作战想定-飞机数据.json, 作战想定-水面舰艇.json
    支持多个合同 (task_contract_ids)；若只给了 task_contract_id 也支持。
    【修改A】：若评估时未带 task_contract_ids，则自动复用训练 job 的 Task/Resource。
    """
    db = get_db()

    # 1) 合同 ID 列表
    ids = meta.get("task_contract_ids") or []
    if not ids and meta.get("task_contract_id"):
        ids = [meta.get("task_contract_id")]
    if isinstance(ids, int):
        ids = [ids]
    if not ids:
        # ★ 评估容错：若未提供合同ID，但提供了来源训练job或 *_eval 命名，则复用其 Task/Resource
        base_train_id = (meta.get("from_train_job") or (job_id[:-5] if job_id.endswith("_eval") else None))
        if base_train_id:
            base_src = Path("jobs") / str(base_train_id)
            t_src = base_src / "Task"
            r_src = base_src / "Resource"
            base_dst = Path("jobs") / _fs_job_id(job_id)
            t_dst = base_dst / "Task"
            r_dst = base_dst / "Resource"
            t_dst.mkdir(parents=True, exist_ok=True)
            r_dst.mkdir(parents=True, exist_ok=True)
            copied = False
            if t_src.exists():
                for f in t_src.glob("*.json"):
                    shutil.copy2(f, t_dst / f.name)
                    copied = True
            if r_src.exists():
                for f in r_src.glob("*.json"):
                    shutil.copy2(f, r_dst / f.name)
                    copied = True
            if copied:
                return str(t_dst), str(r_dst)
        # 若没有可复用来源，仍然报错
        raise RuntimeError("meta.task_contract_ids 为空")

    # 2) 解析想定/阵营（用于资源）
    scenario_id = meta.get("scenario_id")
    side = (meta.get("side") or "").upper()

    base = Path("jobs") / _fs_job_id(job_id)
    tdir = base / "Task"
    rdir = base / "Resource"
    tdir.mkdir(parents=True, exist_ok=True)
    rdir.mkdir(parents=True, exist_ok=True)

    # 3) 写 Task：每个合同一份 JSON
    for cid in ids:
        row = db.execute("SELECT * FROM contracts WHERE id = ?", (int(cid),)).fetchone()
        if not row:
            raise RuntimeError(f"合同 {cid} 不存在")

        c = dict(row)
        details = _json_try_load(c.get("details"))
        # 还原为算法所需结构（顶层字段写全，再合并 details）
        task_json = {
            "合同名称": c.get("name") or f"合同{cid}",
            "任务描述": c.get("description") or "",
            "作战类型": c.get("contract_type") or (details.get("作战类型") if isinstance(details, dict) else ""),
            "作战场景": (details.get("作战场景") if isinstance(details, dict) else "") or "",
            "作战时间": {
                "开始时间": c.get("start_time") or "",
                "结束时间": c.get("end_time") or ""
            },
            "scenarioId": c.get("scenario_id") if c.get("scenario_id") is not None else scenario_id,
            "side": c.get("side") or side or "RED"
        }
        if isinstance(details, dict):
            # 先合并 details，再用顶层覆盖，避免被 details 里的旧键值顶掉
            merged = dict(details)
            merged.update(task_json)
            task_json = merged

        with open(tdir / f"task_{cid}.json", "w", encoding="utf-8") as f:
            json.dump(task_json, f, ensure_ascii=False, indent=2)

        # 若没给 scenario_id/side，用合同表中的当作默认值
        if scenario_id is None:
            scenario_id = c.get("scenario_id")
        if not side:
            side = (c.get("side") or "").upper()

    # 4) 写 Resource：从 sim_platforms/sim_equipments 构建
    air, sea = {}, []
    if scenario_id is not None:
        try:
            choice = (meta.get("resource_choice") or "auto").lower()
            air, sea = _build_resources_from_db(db, int(scenario_id), side, choice)
        except Exception as e:
            print(f"[resource] build failed: {e}")

    with open(rdir / "作战想定-飞机数据.json", "w", encoding="utf-8") as f:
        json.dump(air, f, ensure_ascii=False, indent=2)
    with open(rdir / "作战想定-水面舰艇.json", "w", encoding="utf-8") as f:
        json.dump(sea, f, ensure_ascii=False, indent=2)

    return str(tdir), str(rdir)


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(database.DB_NAME)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_connection(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.cli.command('init-db')
def init_db_command():
    database.init_db()

# *** 核心修复 1：确保 process_query_result 能处理 details ***
def process_query_result(rows):
    processed_rows = []
    for row in rows:
        row_dict = dict(row)
        # 确保 details 和 params 都能被正确解析
        if 'details' in row_dict and row_dict['details']:
            try:
                row_dict['details'] = json.loads(row_dict['details'])
            except (json.JSONDecodeError, TypeError):
                pass # 如果解析失败，保持为字符串
        if 'params' in row_dict and row_dict['params']:
            try:
                row_dict['params'] = json.loads(row_dict['params'])
            except (json.JSONDecodeError, TypeError):
                pass
        processed_rows.append(row_dict)
    return processed_rows

@app.route('/api/register', methods=['POST'])
def register():
    """用户注册。需要 username, password。如果 role='admin', 还需要 inviteCode。"""
    db = get_db()
    data = request.get_json()
    role = data.get('role', 'user') # 获取角色，默认为 'user'
    if role not in ['user', 'admin']:
        return jsonify({"error": "无效的角色"}), 400
    username = data.get('username')
    password = data.get('password')
    invite_code = data.get('inviteCode') # 获取邀请码

    if not username or not password:
        return jsonify({"error": "用户名和密码不能为空"}), 400
    
        # ** 核心修改：邀请码验证逻辑 **
    if role == 'admin':
        if not invite_code:
            return jsonify({"error": "缺少管理员邀请码"}), 403 # 403 Forbidden
        if invite_code != ADMIN_INVITE_CODE:
            return jsonify({"error": "管理员邀请码不正确"}), 403
        
    # 检查用户是否已存在
    if db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone() is not None:
        return jsonify({"error": "用户名已存在"}), 409

    # 加密密码并插入数据库
    hashed_password = generate_password_hash(password)
    db.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, hashed_password, role))
    db.commit()
    
    return jsonify({"message": "注册成功"}), 201

@app.route('/api/login', methods=['POST'])
def login():
    """用户登录。需要 username 和 password。成功后设置 session。"""
    db = get_db()
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

    if user is None or not check_password_hash(user['password'], password):
        return jsonify({"error": "用户名或密码错误"}), 401
    
    # 登录成功，使用 session 记录用户状态
    session['user_id'] = user['id']
    session['username'] = user['username']
    session['role'] = user['role']
    
    return jsonify({
        "id": user['id'],
        "username": user['username'],
        "role": user['role']
    }), 200

@app.route('/api/logout', methods=['POST'])
def logout():
    """用户登出。清除 session。"""
    session.clear() # 清除 session
    return jsonify({"message": "登出成功"}), 200

# 一个受保护的接口，用于检查当前登录状态
@app.route('/api/user/session', methods=['GET'])
def check_session():
    """检查当前用户的 session 状态。"""
    if 'user_id' in session:
        return jsonify({
            "isLoggedIn": True,
            "userInfo": {
                "id": session['user_id'],
                "name": session['username'],
                "role": session['role']
            }
        }), 200
    else:
        return jsonify({"isLoggedIn": False}), 200


# ==========================================================
# ===                平台资源管理 (Platforms)                ===
# ==========================================================

@app.route('/api/platforms', methods=['GET', 'POST'])
def handle_platforms():
    """
    GET: 获取平台列表，支持分页。
    POST: 创建一个新平台。
    """
    db = get_db()
    
    # --- 创建新平台 (POST) ---
    if request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求体不能为空"}), 400
        name = data.get('name')
        if not name:
            return jsonify({"error": "平台名称 (name) 是必填项"}), 400
        
        equipment_ids = data.get('equipment_ids', [])
        
        details_to_store = data.get('details', {})
        
        try:
            cursor = db.cursor()
            # *** 核心修复 2：将 INSERT 语句中的 params 列改为 details ***
            cursor.execute(
                "INSERT INTO platforms (name, category, model_type, country, service_date, status, details) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (name, data.get('category'), data.get('model_type'), data.get('country'), data.get('service_date'), data.get('status', '可用'), json.dumps(details_to_store))
            )
            platform_id = cursor.lastrowid

            if equipment_ids:
                for eq_id in equipment_ids:
                    cursor.execute("INSERT INTO platform_equipment_link (platform_id, equipment_id) VALUES (?, ?)", (platform_id, eq_id))

            db.commit()
            new_platform = db.execute("SELECT * FROM platforms WHERE id = ?", (platform_id,)).fetchone()
            return jsonify(process_query_result([new_platform])[0]), 201
        except sqlite3.IntegrityError as e:
            db.rollback()
            return jsonify({"error": f"创建失败: {e}"}), 409
        except sqlite3.Error as e:
            db.rollback()
            traceback.print_exc() # 打印详细错误以备调试
            return jsonify({"error": "数据库操作失败", "details": str(e)}), 500

    # --- 获取平台列表 (GET) ---
    if request.method == 'GET':
        """获取平台列表，支持分页和按名称搜索。"""
        try:
            page = int(request.args.get('page', 1))
            page_size = int(request.args.get('pageSize', 10))
            # *** 核心修复 1：获取 search 查询参数 ***
            search_keyword = request.args.get('search', '') 
        except ValueError:
            return jsonify({"error": "无效的分页参数"}), 400

        offset = (page - 1) * page_size
        db = get_db()
        
        try:
            # --- 构建查询条件 ---
            base_query = "FROM platforms"
            conditions = []
            params = []

            if search_keyword:
                # 使用 LIKE 进行模糊查询，%...% 表示匹配任意字符
                conditions.append("name LIKE ?")
                params.append(f"%{search_keyword}%")

            where_clause = ""
            if conditions:
                where_clause = " WHERE " + " AND ".join(conditions)

            # --- 查询总数 ---
            total_query = "SELECT COUNT(id) " + base_query + where_clause
            total_row = db.execute(total_query, tuple(params)).fetchone()
            total_items = total_row[0] if total_row else 0

            # --- 查询当页数据 ---
            data_query = "SELECT id, name, category, model_type, country, service_date, status " + base_query + where_clause + " ORDER BY name LIMIT ? OFFSET ?"
            # ** 关键：将分页参数附加到查询参数列表的末尾 **
            params.extend([page_size, offset])
            platforms = db.execute(data_query, tuple(params)).fetchall()

            return jsonify({
                'items': [dict(row) for row in platforms],
                'total': total_items,
                'page': page,
                'pageSize': page_size
            })
        except sqlite3.Error as e:
            return jsonify({"error": "数据库查询失败", "details": str(e)}), 500


@app.route('/api/platforms/<int:platform_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_single_platform(platform_id):
    """获取单个平台详情 (GET)，更新平台信息 (PUT)，或删除平台 (DELETE)。"""
    db = get_db()

    # --- 删除平台 (DELETE) ---
    if request.method == 'DELETE':
        try:
            cursor = db.cursor()
            # 由于设置了 ON DELETE CASCADE, 我们只需要删除 platforms 表中的记录
            cursor.execute("DELETE FROM platforms WHERE id = ?", (platform_id,))
            db.commit()
            if cursor.rowcount == 0:
                return jsonify({"error": "平台未找到"}), 404
            return jsonify({"message": f"平台 ID:{platform_id} 已成功删除"}), 200
        except sqlite3.Error as e:
            db.rollback()
            return jsonify({"error": "数据库删除失败", "details": str(e)}), 500

    # --- 更新平台 (PUT) ---
    if request.method == 'PUT':
        # *** 核心修复 1：在执行更新前，先检查平台是否存在 ***
        existing_platform = db.execute("SELECT id FROM platforms WHERE id = ?", (platform_id,)).fetchone()
        if not existing_platform:
            return jsonify({"error": "平台未找到"}), 404

        data = request.get_json()
        equipment_ids = data.get('equipment_ids')

        try:
            cursor = db.cursor()
            cursor.execute(
                """
                UPDATE platforms SET 
                name = ?, category = ?, model_type = ?, country = ?, 
                service_date = ?, status = ?, details = ? 
                WHERE id = ?
                """,
                (
                    data.get('name'), data.get('category'), data.get('model_type'),
                    data.get('country'), data.get('service_date'), data.get('status'),
                    json.dumps(data.get('details', {})), platform_id
                )
            )
            
            if equipment_ids is not None:
                cursor.execute("DELETE FROM platform_equipment_link WHERE platform_id = ?", (platform_id,))
                if equipment_ids:
                    for eq_id in equipment_ids:
                        cursor.execute("INSERT INTO platform_equipment_link (platform_id, equipment_id) VALUES (?, ?)", (platform_id, eq_id))

            db.commit()
            
            # *** 核心修复 2：不再依赖 cursor.rowcount 来判断是否存在 ***
            #    我们已经在前面检查过了，所以这里只需要返回成功即可。
            
            updated_platform = db.execute("SELECT * FROM platforms WHERE id = ?", (platform_id,)).fetchone()
            return jsonify(process_query_result([updated_platform])[0]), 200
            
        except sqlite3.IntegrityError as e:
            db.rollback()
            return jsonify({"error": f"更新失败: {e}"}), 409
        except sqlite3.Error as e:
            db.rollback()
            traceback.print_exc()
            return jsonify({"error": "数据库更新失败", "details": str(e)}), 500

    # --- 获取平台详情 (GET) ---
    if request.method == 'GET':
        """根据ID获取单个平台的完整详细信息，并附带其结构化的装备列表。"""
        db = get_db()
        
        # 1. 获取平台基本信息
        platform_query = "SELECT * FROM platforms WHERE id = ?"
        platform = db.execute(platform_query, (platform_id,)).fetchone()
        
        if platform is None:
            return jsonify({"error": "Platform not found"}), 404
            
        platform_data = process_query_result([platform])[0]

        # 2. 获取关联的装备列表
        equipment_query = """
            SELECT e.id, e.name, e.type_code, e.category_text
            FROM equipments e
            JOIN platform_equipment_link pel ON e.id = pel.equipment_id
            WHERE pel.platform_id = ?
        """
        equipments = db.execute(equipment_query, (platform_id,)).fetchall()
        
        # 3. 将装备列表添加到返回数据中
        platform_data['equipments'] = [dict(row) for row in equipments]
        
        return jsonify(platform_data)

# *** 新增：更新平台状态的API ***
@app.route('/api/platforms/<int:platform_id>/status', methods=['PUT'])
def update_platform_status(platform_id):
    """(管理员) 更新单个平台的状态。"""
    # 可以在这里添加权限检查
    # if 'role' not in session or session['role'] != 'admin':
    #     return jsonify({"error": "权限不足"}), 403

    data = request.get_json()
    new_status = data.get('status')
    if new_status not in ['可用', '停用', '维护']:
        return jsonify({"error": "无效的状态值"}), 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE platforms SET status = ? WHERE id = ?", (new_status, platform_id))

    if cursor.rowcount == 0:
        db.rollback()
        return jsonify({"error": "平台未找到"}), 404

    db.commit()
    return jsonify({"message": "平台状态更新成功", "id": platform_id, "status": new_status}), 200



# ==========================================================
# ===                装备资源管理 (Equipments)               ===
# ==========================================================

@app.route('/api/equipments', methods=['GET', 'POST'])
def handle_equipments():
    """获取装备列表 (GET) 或创建新装备 (POST)。"""
    db = get_db()
    
    # --- 创建新装备 (POST) ---
    if request.method == 'POST':
        data = request.get_json()
        name = data.get('name')
        if not name:
            return jsonify({"error": "装备名称 (name) 是必填项"}), 400
        
                # *** 核心修复 1：从 data 中获取 details ***
        details_to_store = data.get('details', {})

        try:
            cursor = db.cursor()
            # *** 核心修复 2：将 INSERT 语句中的 params 列改为 details ***
            cursor.execute(
                "INSERT INTO equipments (name, type_code, category_text, status, details) VALUES (?, ?, ?, ?, ?)",
                (name, data.get('type_code'), data.get('category_text'), data.get('status', '可用'), json.dumps(details_to_store))
            )
            equipment_id = cursor.lastrowid
            db.commit()
            new_equipment = db.execute("SELECT * FROM equipments WHERE id = ?", (equipment_id,)).fetchone()
            return jsonify(process_query_result([new_equipment])[0]), 201
        except sqlite3.IntegrityError:
            db.rollback()
            return jsonify({"error": f"创建失败，可能装备名称 '{name}' 已存在"}), 409
        except sqlite3.Error as e:
            db.rollback()
            traceback.print_exc()
            return jsonify({"error": "数据库操作失败", "details": str(e)}), 500
    
    # --- 获取装备列表 (GET) ---
    if request.method == 'GET':
        """获取装备列表，支持分页和按名称搜索。"""
        try:
            page = int(request.args.get('page', 1))
            page_size = int(request.args.get('pageSize', 10))
            # *** 核心修复 2：获取 search 查询参数 ***
            search_keyword = request.args.get('search', '')
        except ValueError:
            return jsonify({"error": "无效的分页参数"}), 400

        offset = (page - 1) * page_size
        db = get_db()
        
        # --- 构建查询条件 (与 platforms 逻辑完全相同) ---
        base_query = "FROM equipments"
        conditions = []
        params = []

        if search_keyword:
            conditions.append("name LIKE ?")
            params.append(f"%{search_keyword}%")

        where_clause = ""
        if conditions:
            where_clause = " WHERE " + " AND ".join(conditions)

        # --- 查询总数 ---
        total_query = "SELECT COUNT(id) " + base_query + where_clause
        total = db.execute(total_query, tuple(params)).fetchone()[0]

        # --- 查询当页数据 ---
        data_query = "SELECT id, name, type_code, category_text, status " + base_query + where_clause + " ORDER BY name LIMIT ? OFFSET ?"
        params.extend([page_size, offset])
        items = db.execute(data_query, tuple(params)).fetchall()

        return jsonify({
            'items': [dict(row) for row in items],
            'total': total,
            'page': page,
            'pageSize': page_size
        })

@app.route('/api/equipments/<int:equipment_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_single_equipment(equipment_id):
    """获取单个装备详情 (GET)，更新装备信息 (PUT)，或删除装备 (DELETE)。"""
    db = get_db()

    # --- 删除装备 (DELETE) ---
    if request.method == 'DELETE':
        try:
            cursor = db.cursor()
            # 由于设置了 ON DELETE CASCADE, 我们只需要删除 equipments 表中的记录
            cursor.execute("DELETE FROM equipments WHERE id = ?", (equipment_id,))
            db.commit()
            if cursor.rowcount == 0:
                return jsonify({"error": "装备未找到"}), 404
            return jsonify({"message": f"装备 ID:{equipment_id} 已成功删除"}), 200
        except sqlite3.Error as e:
            db.rollback()
            return jsonify({"error": "数据库删除失败", "details": str(e)}), 500

    # --- 更新装备 (PUT) ---
    if request.method == 'PUT':
        data = request.get_json()
        details_to_store = data.get('details', {})
        try:
            cursor = db.cursor()
            # *** 核心修复 4：将 UPDATE 语句中的 params 列改为 details ***
            cursor.execute(
                """
                UPDATE equipments SET 
                name = ?, type_code = ?, category_text = ?, status = ?, details = ? 
                WHERE id = ?
                """,
                (
                    data.get('name'), data.get('type_code'), data.get('category_text'),
                    data.get('status'), json.dumps(details_to_store),
                    equipment_id
                )
            )
            db.commit()
            if cursor.rowcount == 0:
                return jsonify({"error": "装备未找到"}), 404

            updated_equipment = db.execute("SELECT * FROM equipments WHERE id = ?", (equipment_id,)).fetchone()
            return jsonify(process_query_result([updated_equipment])[0]), 200
        except sqlite3.IntegrityError:
            db.rollback()
            return jsonify({"error": "更新失败，可能装备名称已存在"}), 409
        except sqlite3.Error as e:
            db.rollback()
            traceback.print_exc()
            return jsonify({"error": "数据库更新失败", "details": str(e)}), 500

    # --- 获取装备详情 (GET) ---
    if request.method == 'GET':
        """根据ID获取单个装备的详情，并附带可使用该装备的平台列表。"""
        db = get_db()
        
        # 1. 获取装备基本信息
        equipment = db.execute("SELECT * FROM equipments WHERE id = ?", (equipment_id,)).fetchone()
        if equipment is None:
            return jsonify({"error": "Equipment not found"}), 404
        equipment_data = process_query_result([equipment])[0]
        
        # 2. 获取使用该装备的平台列表
        platform_query = """
            SELECT p.id, p.name, p.category, p.model_type
            FROM platforms p
            JOIN platform_equipment_link pel ON p.id = pel.platform_id
            WHERE pel.equipment_id = ?
        """
        platforms = db.execute(platform_query, (equipment_id,)).fetchall()
        
        # 3. 将平台列表添加到返回数据中
        equipment_data['used_by_platforms'] = [dict(row) for row in platforms]
        
        return jsonify(equipment_data)

# *** 新增：更新装备状态的API ***
@app.route('/api/equipments/<int:equipment_id>/status', methods=['PUT'])
def update_equipment_status(equipment_id):
    """(管理员) 更新单个装备的状态。"""
    # 权限检查...
    data = request.get_json()
    new_status = data.get('status')
    if new_status not in ['可用', '停用', '维护']:
        return jsonify({"error": "无效的状态值"}), 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE equipments SET status = ? WHERE id = ?", (new_status, equipment_id))

    if cursor.rowcount == 0:
        db.rollback()
        return jsonify({"error": "装备未找到"}), 404

    db.commit()
    return jsonify({"message": "装备状态更新成功", "id": equipment_id, "status": new_status}), 200

# --- 合同模板 API (保持不变) ---
@app.route('/api/contract-templates', methods=['GET'])
def get_all_contract_templates():
    """获取合同模板列表（仅含核心字段）。"""
    db = get_db()
    templates = db.execute("SELECT id, name, description, scenario FROM contract_templates").fetchall()
    return jsonify(process_query_result(templates))

@app.route('/api/contract-templates/<int:template_id>', methods=['GET'])
def get_template_by_id(template_id):
    """通过ID获取单个合同模板的完整详情。"""
    db = get_db()
    template = db.execute("SELECT * FROM contract_templates WHERE id = ?", (template_id,)).fetchone()
    if not template: return jsonify({"error": "模板未找到"}), 404
    return jsonify(process_query_result([template])[0])
    
# --- 用户合同核心 API ---

# --- 创建合同 (POST) ---
@app.route('/api/contracts', methods=['POST'])
def handle_contracts_post():
    db = get_db()
    data = request.get_json()
    contract_data = data.get('contract_data', {})
    creater = data.get('creater')

    if not contract_data or not creater:
        return jsonify({"error": "请求体缺少 contract_data 或 creater 字段"}), 400

    # 1. **从前端数据中精确提取顶层字段**
    name = contract_data.get('合同名称')
    description = contract_data.get('任务描述')
    contract_type = contract_data.get('作战类型') 
    scenario_id = contract_data.get('scenarioId')
    side = contract_data.get('side')
    start_time = contract_data.get('作战时间', {}).get('开始时间')
    end_time = contract_data.get('作战时间', {}).get('结束时间')

    # 2. **构建 details 对象，只包含那些非顶层字段**
    #    这是一个白名单，确保了数据结构的纯净
    top_level_keys = ['名称', '任务描述', '作战类型', 'scenarioId', 'side', '作战时间']
    details_data = {
        key: value for key, value in contract_data.items() 
        if key not in top_level_keys
    }
    details_json = json.dumps(details_data, ensure_ascii=False)
    
    try:
        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO contracts 
            (name, description, contract_type, scenario_id, side, start_time, end_time, details, creater) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (name, description, contract_type, scenario_id, side, start_time, end_time, details_json, creater)
        )
        new_id = cursor.lastrowid
        db.commit()
        new_contract = db.execute("SELECT * FROM contracts WHERE id = ?", (new_id,)).fetchone()
        return jsonify(process_query_result([new_contract])[0]), 201
    except sqlite3.Error as e:
        db.rollback()
        return jsonify({"error": "数据库操作失败", "details": str(e)}), 500

# --- 获取合同列表 (GET) ---
@app.route('/api/contracts', methods=['GET'])
def handle_contracts_get():
    status = request.args.get('status')
    creater = request.args.get('creater')
    db = get_db()
    
    # **查询所有核心字段，但不包括庞大的 details**
    query = "SELECT id, name, description, contract_type, scenario_id, side, start_time, end_time, status, creater FROM contracts"
    params = []
    conditions = []

    if status:
        conditions.append("status = ?")
        params.append(status)
    if creater:
        conditions.append("creater = ?")
        params.append(creater)
        
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY id DESC"
    
    contracts = db.execute(query, tuple(params)).fetchall()
    return jsonify(process_query_result(contracts))

# 获取、删除单个合同
@app.route('/api/contracts/<int:contract_id>', methods=['GET', 'DELETE'])
def handle_single_contract(contract_id):
    """处理单个合同的获取与删除。GET获取详情，DELETE用于撤回/删除。"""
    # --- 删除合同 (DELETE) ---
    if request.method == 'DELETE':
        db = get_db()
        try:
            cursor = db.cursor()
            cursor.execute("DELETE FROM contracts WHERE id = ?", (contract_id,))
            db.commit()
            if cursor.rowcount == 0:
                return jsonify({"error": "合同未找到或已被处理"}), 404
            return jsonify({"message": "合同删除成功"}), 200
        except sqlite3.Error as e:
            db.rollback()
            return jsonify({"error": "数据库操作失败", "details": str(e)}), 500

    # --- 获取单个合同详情 (GET) ---
    if request.method == 'GET':
        db = get_db()
        contract = db.execute("SELECT * FROM contracts WHERE id = ?", (contract_id,)).fetchone()
        if not contract: return jsonify({"error": "合同未找到"}), 404
        return jsonify(process_query_result([contract])[0])

# 更新合同状态（审批）
@app.route('/api/contracts/<int:contract_id>/status', methods=['PUT'])
def update_contract_status(contract_id):
    """更新合同状态（审批通过/驳回）。"""
    db = get_db()
    data = request.get_json()
    new_status = data.get('status')
    if new_status not in ['approved', 'rejected']:
        return jsonify({"error": "无效的状态值"}), 400
    
    try:
        cursor = db.cursor()
        cursor.execute("UPDATE contracts SET status = ? WHERE id = ? AND status = 'pending'", (new_status, contract_id))
        db.commit()
        if cursor.rowcount == 0:
            return jsonify({"error": "合同未找到或状态不是'待审批'"}), 404
        return jsonify({"message": "状态更新成功"}), 200
    except sqlite3.Error as e:
        db.rollback()
        return jsonify({"error": "数据库操作失败", "details": str(e)}), 500




@app.route('/api/sim/scenarios', methods=['GET'])
def get_sim_scenarios():
    """获取所有作战想定的列表 (不含兵力详情)"""
    db = get_db()
    
    # ** 核心修正：在 SELECT 语句中加入所有需要的字段 **
    # 这些字段现在都真实存在于 sim_scenarios 表中
    scenarios = db.execute(
        "SELECT id, name, description, scenario_code, type, creator, create_time, force_count FROM sim_scenarios ORDER BY id DESC"
    ).fetchall()
    
    return jsonify(process_query_result(scenarios))

@app.route('/api/sim/scenarios/<int:scenario_id>', methods=['GET'])
def get_sim_scenario_details(scenario_id):
    """获取单个想定的详细信息，并附带其所有兵力平台"""
    db = get_db()
    
    # 1. 获取想定元数据
    scenario_row = db.execute("SELECT * FROM sim_scenarios WHERE id = ?", (scenario_id,)).fetchone()
    if not scenario_row:
        return jsonify({"error": "想顶未找到"}), 404
    
    scenario_data = process_query_result([scenario_row])[0]
    
    # 2. 获取该想定下的所有兵力平台
    platforms_rows = db.execute(
        "SELECT * FROM sim_platforms WHERE scenario_id = ?", (scenario_id,)
    ).fetchall()
    
    # ** 关键：将兵力平台数据嵌入到想定数据中 **
    scenario_data['platforms'] = process_query_result(platforms_rows)
    
    return jsonify(scenario_data)

@app.route('/api/sim/platforms/<int:platform_db_id>/equipments', methods=['GET'])
def get_sim_platform_equipments(platform_db_id):
    """获取单个兵力平台挂载的所有装备 (传感器和武器)"""
    db = get_db()
    
    # 检查平台是否存在
    platform = db.execute("SELECT id FROM sim_platforms WHERE id = ?", (platform_db_id,)).fetchone()
    if not platform:
        return jsonify({"error": "兵力平台未找到"}), 404

    equipments = db.execute(
        "SELECT * FROM sim_equipments WHERE platform_db_id = ?", (platform_db_id,)
    ).fetchall()
    
    return jsonify(process_query_result(equipments))

@app.route('/api/sim/scenarios/upload', methods=['POST'])
def upload_sim_scenario():
    """通过上传JSON文件来创建一个新的作战想定。"""
    if 'file' not in request.files:
        return jsonify({"error": "请求中没有文件部分"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "没有选择文件"}), 400

    if not file.filename.endswith('.json'):
        return jsonify({"error": "只允许上传JSON文件"}), 400

    db = get_db()
    try:
        content_string = file.stream.read().decode('utf-8')
        data = json.loads(content_string)
        
        experiment = data.get('experiment', {})
        forces_info = data.get('forcesInfo', [])
        
        name = experiment.get('name')
        scenario_code = experiment.get('scenarioCode')

        if not name or not scenario_code:
            return jsonify({"error": "JSON文件中缺少想定名称(name)或想定代码(scenarioCode)"}), 400
        
        existing_scenario = db.execute("SELECT id FROM sim_scenarios WHERE scenario_code = ?", (scenario_code,)).fetchone()
        if existing_scenario:
            return jsonify({"error": f"上传失败：具有相同想定代码 '{scenario_code}' 的想定已存在。"}), 409

        cursor = db.cursor()
        
        description = experiment.get('description')
        type_name = experiment.get('typeName')
        creator = experiment.get('creator') or session.get('username', '未知用户')
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
        
        db.commit()
        
        return jsonify({"message": f"想定 '{name}' 已成功上传并创建！", "id": scenario_db_id}), 201

    except json.JSONDecodeError:
        return jsonify({"error": "无效的JSON文件格式"}), 400
    except Exception as e:
        db.rollback()
        traceback.print_exc() 
        return jsonify({"error": "处理文件时发生内部错误", "details": str(e)}), 500


@app.route('/api/sim/scenarios/<int:scenario_id>', methods=['DELETE'])
def delete_sim_scenario(scenario_id):
    """删除一个作战想定及其所有关联的兵力平台和装备。"""
    db = get_db()
    try:
        cursor = db.cursor()
        
        # 0. 检查想定是否存在
        scenario = cursor.execute("SELECT id FROM sim_scenarios WHERE id = ?", (scenario_id,)).fetchone()
        if not scenario:
            return jsonify({"error": "想顶未找到"}), 404

        # 1. 找出该想定下的所有平台ID
        platform_rows = cursor.execute("SELECT id FROM sim_platforms WHERE scenario_id = ?", (scenario_id,)).fetchall()
        platform_ids = [row['id'] for row in platform_rows]

        if platform_ids:
            # 2. 删除所有关联的装备 (sim_equipments)
            # 使用 IN 子句可以一次性删除所有相关装备
            placeholders = ','.join(['?'] * len(platform_ids))
            cursor.execute(f"DELETE FROM sim_equipments WHERE platform_db_id IN ({placeholders})", platform_ids)
            
            # 3. 删除所有关联的兵力平台 (sim_platforms)
            cursor.execute("DELETE FROM sim_platforms WHERE scenario_id = ?", (scenario_id,))

        # 4. 最后删除想定本身 (sim_scenarios)
        cursor.execute("DELETE FROM sim_scenarios WHERE id = ?", (scenario_id,))
        
        db.commit()
        
        return jsonify({"message": f"想定 ID:{scenario_id} 已被成功删除。"}), 200

    except sqlite3.Error as e:
        db.rollback()
        traceback.print_exc()
        return jsonify({"error": "数据库操作失败", "details": str(e)}), 500
# ==========================================================
# *** 新增：API 文档路由 ***
# ==========================================================
@app.route('/api/doc')
def get_api_doc():
    """生成并返回一个结构化的API文档。"""
    api_docs = []
    
    # 遍历 Flask app 中所有已注册的路由规则
    for rule in app.url_map.iter_rules():
        # 排除 Flask 默认的 /static 路由和文档自身
        if rule.endpoint == 'static' or rule.endpoint == 'get_api_doc':
            continue
            
        # 获取与路由关联的视图函数
        view_function = app.view_functions[rule.endpoint]
        
        # 从函数的文档字符串中提取描述
        docstring = view_function.__doc__
        description = docstring.strip() if docstring else "暂无描述"
        
        api_docs.append({
            'endpoint': rule.endpoint,
            'methods': sorted(list(rule.methods)),
            'path': rule.rule,
            'description': description
        })
        
    # 按路径排序，方便查看
    sorted_docs = sorted(api_docs, key=lambda x: x['path'])
    
    return jsonify({
        "title": "对海作战仿真平台 API 文档",
        "version": "1.0.0",
        "endpoints": sorted_docs
    })


@app.route('/')
def index():
    """生成一个更新的、内容丰富的HTML导航页面，作为API的入口。"""
    
    # 动态生成可点击的GET请求链接
    get_links_html = ''
    # 挑选出所有无参数的核心GET请求作为示例
    endpoints_to_show = [
        'get_api_doc',
        'check_session',
        'handle_platforms',
        'handle_equipments',
        'get_all_contract_templates',
        'handle_contracts', # 合同列表
        'get_sim_scenarios'
    ]
    
    for rule in app.url_map.iter_rules():
        if rule.endpoint in endpoints_to_show and 'GET' in rule.methods and not rule.arguments:
            docstring = app.view_functions[rule.endpoint].__doc__
            description = docstring.strip().split('\n')[0] if docstring else "点击查看"
            get_links_html += f'<li><a href="{rule.rule}" target="_blank">{rule.rule}</a> - {description}</li>'

    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>对海作战仿真平台 - 后端 API</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; line-height: 1.6; color: #333; max-width: 960px; margin: 40px auto; padding: 0 20px; background-color: #f9fafb; }}
            h1, h2, h3 {{ color: #111827; }}
            a {{ color: #2563eb; text-decoration: none; font-weight: 500; }}
            a:hover {{ text-decoration: underline; color: #1d4ed8;}}
            .container {{ background-color: #fff; padding: 40px; border-radius: 12px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05); }}
            ul {{ list-style-type: none; padding-left: 0; }}
            li {{ margin-bottom: 12px; display: flex; align-items: baseline; }}
            li::before {{ content: '✓'; color: #22c55e; margin-right: 12px; font-weight: bold; }}
            code {{ background-color: #e5e7eb; padding: 3px 6px; border-radius: 4px; font-family: "SF Mono", "Courier New", monospace; font-size: 0.9em; }}
            .note {{ background-color: #eff6ff; border-left: 4px solid #3b82f6; padding: 20px; margin-top: 30px; border-radius: 0 4px 4px 0; }}
            .note p, .note ul {{ margin: 0; }}
            .note li {{ margin-bottom: 8px; }}
            .section {{ margin-bottom: 40px; }}
            hr {{ border: none; border-top: 1px solid #e5e7eb; margin: 40px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <header style="text-align: center; margin-bottom: 40px;">
                <h1>🚀 对海作战仿真平台 - 后端 API</h1>
                <p style="color: #6b7280; font-size: 1.1em;">服务正在运行中，为前端应用提供全面的数据与实时通信支持。</p>
            </header>

            <div class="section">
                <h2>核心功能模块</h2>
                <ul>
                    <li><b>用户认证:</b> 提供用户注册、登录、登出及会话保持功能 (<code>/api/register</code>, <code>/api/login</code>)。</li>
                    <li><b>资源库管理:</b> 支持对武器平台 (<code>/api/platforms</code>) 和挂载装备 (<code>/api/equipments</code>) 的数据库管理。</li>
                    <li><b>作战想定管理:</b> 允许通过 JSON 文件上传、查询和删除复杂的作战想定 (<code>/api/sim/scenarios</code>)。</li>
                    <li><b>任务合同管理:</b> 支持从模板创建、提交、审批和查询各类作战任务合同 (<code>/api/contracts</code>)。</li>
                    <li><b>强化学习接口 (WebSocket):</b> 通过 Socket.IO 提供实时的训练/评估任务提交、进度监控和结果回传。</li>
                </ul>
            </div>
            
            <hr>

            <div class="section">
                <h2>API 文档与快速访问</h2>
                <p>以下是一些可以直接在浏览器中访问的 <code>GET</code> 请求端点，用于快速查看数据。完整的 API 列表请访问 <code>/api/doc</code>。</p>
                <ul>
                    {get_links_html}
                </ul>
            </div>

            <div class="note">
                <h3>如何测试需要认证和特定请求方法的 API?</h3>
                <p>许多接口（如创建合同 <code>POST /api/contracts</code>）需要您先登录以获取会话 Cookie，并且不能通过浏览器直接访问。请使用专业的 API 测试工具：</p>
                <ul>
                    <li><b>Postman / Insomnia:</b> 强大的图形化工具，可以方便地管理 Cookie、设置请求头和请求体。</li>
                    <li><b>浏览器开发者工具 (F12):</b> 在前端页面进行操作时，打开“网络(Network)”面板，可以查看到所有实际发出的 API 请求及其详细信息，是调试前后端交互的最佳方式。</li>
                </ul>
                <p><b>典型测试流程:</b></p>
                <ol style="padding-left: 20px;">
                    <li>使用工具向 <code>/api/login</code> 发送一个 <code>POST</code> 请求，请求体为 <code>{{"username": "your_user", "password": "your_password"}}</code>。</li>
                    <li>成功登录后，工具会自动保存后端返回的 <code>session</code> Cookie。</li>
                    <li>后续所有请求（如 <code>GET /api/contracts</code>）都会自动携带这个 Cookie，从而通过身份验证。</li>
                </ol>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content

# ================== 合同→素材落地（桥接层，内嵌版） ==================
def _json_try_load(x):
    if isinstance(x, (dict, list)): 
        return x
    try:
        return json.loads(x) if x else {}
    except Exception:
        return {}

def _classify_domain_by_type(type_name: str) -> str:
    """非常保守的分类：仅基于 type_name / 关键词"""
    t = (type_name or "").lower()
    if any(k in t for k in ["驱逐", "护卫", "巡逻舰", "潜艇", "航母", "两栖", "frigate", "destroyer", "sub", "carrier", "ship", "vessel", "舰", "船"]):
        return "sea"
    if any(k in t for k in ["战斗机", "轰炸机", "攻击机", "预警机", "无人机", "运输机", "直升机", "helicopter", "fighter", "bomber", "awacs", "uav", "air"]):
        return "air"
    return "air"  # 默认按空中算（更通用，也符合适配器默认 900km/h）

def _ship_equipment_rows_to_list(equip_rows):
    """把 sim_equipments -> 适配器期望的 ship.equipment[]; 尽量给出 'type' 关键词（含 missile）"""
    out = []
    for r in equip_rows:
        name = r.get("name") or ""
        details = _json_try_load(r.get("details"))
        etype = details.get("type") or details.get("category") or r.get("category") or ""
        # 尽量打上 missile 关键词，便于适配器识别打击能力
        nlow = (name or "").lower()
        elow = (etype or "").lower()
        if ("missile" not in elow) and any(k in nlow for k in ["导弹", "反舰", "missile"]):
            etype = (etype + " missile").strip() if etype else "missile"
        out.append({"name": name, "type": etype})
    return out

def _build_resources_from_db(db, scenario_id: int, team: str, choice: str):
    """
    从 sim_platforms/sim_equipments 构建适配器旧格式：
      air: dict  {key: {"vehicle": {"name": str, "params": {"maxSpeed": int|float}}}}
      ship: list  [{"name":..., "type":..., "params": {"maxSpeed": 30}, "equipment":[...]}, ...]
    team: 'RED' | 'BLUE'（如果为空则不过滤）
    choice: 'auto' | 'air_only' | 'ship_only' | 'both'
    """
    # 拉平台
    rows = db.execute("SELECT * FROM sim_platforms WHERE scenario_id = ?", (scenario_id,)).fetchall()
    plats = [dict(r) for r in rows]
    # 过滤己方
    if team:
        plats = [p for p in plats if str(p.get("team") or "").upper() == str(team).upper()]

    # 预取所有装备
    equip_map = {}  # platform_db_id -> [rows]
    if plats:
        ids = [p["id"] for p in plats]
        placeholders = ",".join("?" for _ in ids)
        all_eq = db.execute(f"SELECT * FROM sim_equipments WHERE platform_db_id IN ({placeholders})", ids).fetchall()
        for r in all_eq:
            d = dict(r)
            equip_map.setdefault(d["platform_db_id"], []).append(d)

    air_dict = {}
    ship_list = []

    # 是否写入
    ch = (choice or "auto").lower()
    use_air  = ch in ("auto", "both", "air_only")
    use_ship = ch in ("auto", "both", "ship_only")

    # 粗略构造
    for p in plats:
        name = p.get("name") or f"plat-{p.get('id')}"
        type_name = p.get("type_name") or ""
        domain = _classify_domain_by_type(type_name)
        eqs = equip_map.get(p["id"], [])

        if domain == "air" and use_air:
            # 适配器默认没有速度也能跑（内置 900km/h）；给个保守默认值
            air_dict[str(p["id"])] = {
                "vehicle": {
                    "name": name,
                    "params": {
                        "maxSpeed": 900   # km/h；adapters._extract_caps_from_air_item 里有默认 900
                    }
                }
            }
        elif domain == "sea" and use_ship:
            ship_list.append({
                "name": name,
                "type": type_name or "舰艇",
                "params": { "maxSpeed": 30 },   # 节：adapters 里 <80 会按节换算
                "equipment": _ship_equipment_rows_to_list(eqs)
            })

    return air_dict, ship_list

# def _materialize_contract_and_resources(job_id: str, meta: dict):
#     """
#     读取 DB 的合同与想定，落地到一个 job 专属临时目录：
#       <tmp>/rl_job_{job}/Task/task_*.json
#       <tmp>/rl_job_{job}/Resource/air.json, ship.json
#     返回：task_dir, resource_dir
#     """
#     db = get_db()
#     contract_id = meta.get("task_contract_id")
#     if not contract_id:
#         raise RuntimeError("meta.task_contract_id 缺失")

#     row = db.execute("SELECT * FROM contracts WHERE id = ?", (int(contract_id),)).fetchone()
#     if not row:
#         raise RuntimeError(f"合同 {contract_id} 不存在")
#     c = dict(row)
#     c_details = _json_try_load(c.get("details"))

#     # 任务 JSON（最大限度兼容 adapters.load_tasks）
#     task_json = {
#         "名称": c.get("name") or f"合同{contract_id}",
#         "任务描述": c.get("description") or "",
#         "作战场景": c.get("scenario") or "",
#         "作战时间": {
#             "开始时间": c.get("start_time") or "",
#             "结束时间": c.get("end_time") or ""
#         }
#     }
#     # 合并原 details（里面通常包含 敌方目标/巡逻区域/装备要求/...）
#     if isinstance(c_details, dict):
#         task_json.update(c_details)

#     # side / scenarioId 优先走 meta，其次 details
#     side = (meta.get("side") 
#             or c_details.get("details", {}).get("side") 
#             or c_details.get("side") 
#             or "").upper()
#     scenario_id = meta.get("scenario_id")
#     if scenario_id is None:
#         scenario_id = (c_details.get("details", {}) or {}).get("scenarioId")

#     # 构建资源
#     air_dict, ship_list = {}, []
#     if scenario_id is not None:
#         try:
#             resource_choice = meta.get("resource_choice", "auto")
#             air_dict, ship_list = _build_resources_from_db(db, int(scenario_id), side, resource_choice)
#         except Exception as e:
#             # 兜底：没有资源也可以，仅靠合同生成任务
#             print(f"[bridge] build resources failed: {e}")

#     # 落地
#     base = Path(tempfile.mkdtemp(prefix=f"rl_job_{job_id}_"))
#     task_dir = base / "Task"
#     res_dir  = base / "Resource"
#     task_dir.mkdir(parents=True, exist_ok=True)
#     res_dir.mkdir(parents=True, exist_ok=True)

#     with open(task_dir / f"task_{contract_id}.json", "w", encoding="utf-8") as f:
#         json.dump(task_json, f, ensure_ascii=False, indent=2)

#     # 根据 choice 写资源
#     ch = (meta.get("resource_choice") or "auto").lower()
#     write_air  = ch in ("auto", "both", "air_only")
#     write_ship = ch in ("auto", "both", "ship_only")

#     if write_air:
#         with open(res_dir / "air.json", "w", encoding="utf-8") as f:
#             json.dump(air_dict, f, ensure_ascii=False, indent=2)
#     if write_ship:
#         with open(res_dir / "ship.json", "w", encoding="utf-8") as f:
#             json.dump(ship_list, f, ensure_ascii=False, indent=2)

#     return str(task_dir), str(res_dir)


# ========== PCCS API 接口 (资源虚拟化标准) ==========

from models import PCCSResource, global_resource_pool
from pccs_adapter import PCCSAdapter

# 初始化 PCCS 适配器
pccs_adapter = PCCSAdapter()

@app.route('/api/pccs/resources', methods=['GET'])
def get_pccs_resources():
    """
    获取所有 PCCS 资源列表
    Query 参数:
        - type: 资源类型 (platform/equipment)
        - category: 资源类别
        - mission_type: 任务类型 (patrol/strike/air_defense/recon)
        - availability: 可用状态 (available/busy/reserved)
    """
    try:
        resource_type = request.args.get('type')
        category = request.args.get('category')
        mission_type = request.args.get('mission_type')
        availability = request.args.get('availability')

        # 构建过滤器
        filters = {}
        if category:
            filters['category'] = category
        if mission_type:
            filters['mission_type'] = mission_type
        if availability:
            filters['availability'] = availability

        resources = global_resource_pool.list_resources(
            resource_type=resource_type,
            filters=filters
        )

        return jsonify({
            'success': True,
            'count': len(resources),
            'resources': [r.to_dict() for r in resources]
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/pccs/resource/<resource_type>/<int:resource_id>', methods=['GET'])
def get_pccs_resource(resource_type, resource_id):
    """
    获取单个资源的 PCCS 完整信息
    """
    try:
        if resource_type not in ['platform', 'equipment']:
            return jsonify({
                'success': False,
                'error': 'Invalid resource_type. Must be platform or equipment'
            }), 400

        resource = global_resource_pool.get_resource(resource_type, resource_id)

        if resource is None:
            return jsonify({
                'success': False,
                'error': f'Resource {resource_type}:{resource_id} not found'
            }), 404

        return jsonify({
            'success': True,
            'resource': resource.to_dict()
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/pccs/resource/<resource_type>/<int:resource_id>/state', methods=['PUT'])
def update_pccs_resource_state(resource_type, resource_id):
    """
    更新资源的 State 维度
    Request Body 示例:
    {
        "operational_status": "online",
        "availability_status": "busy",
        "mission_status": "executing",
        "health_level": 0.95,
        "fuel_level": 0.7,
        "ammunition_level": 0.8
    }
    """
    try:
        resource = global_resource_pool.get_resource(resource_type, resource_id)

        if resource is None:
            return jsonify({
                'success': False,
                'error': f'Resource {resource_type}:{resource_id} not found'
            }), 404

        data = request.get_json()

        # 更新 State 字段
        if 'operational_status' in data:
            resource.state.operational_status = data['operational_status']
        if 'availability_status' in data:
            resource.state.availability_status = data['availability_status']
        if 'mission_status' in data:
            resource.state.mission_status = data['mission_status']
        if 'health_level' in data:
            resource.state.health_level = float(data['health_level'])
        if 'fuel_level' in data:
            resource.state.fuel_level = float(data['fuel_level'])
        if 'battery_level' in data:
            resource.state.battery_level = float(data['battery_level'])
        if 'ammunition_level' in data:
            resource.state.ammunition_level = float(data['ammunition_level'])
        if 'network_latency' in data:
            resource.state.network_latency = float(data['network_latency'])
        if 'packet_loss_rate' in data:
            resource.state.packet_loss_rate = float(data['packet_loss_rate'])
        if 'connection_strength' in data:
            resource.state.connection_strength = float(data['connection_strength'])

        # 更新最后修改时间
        from datetime import datetime
        resource.last_modified_time = datetime.now().isoformat()
        resource.state.last_update_time = datetime.now().isoformat()

        return jsonify({
            'success': True,
            'message': 'Resource state updated successfully',
            'resource': resource.to_dict()
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/pccs/search', methods=['GET'])
def search_pccs_by_capability():
    """
    根据 Capability 维度搜索资源 (用于任务匹配)
    Query 参数:
        - mission_type: 任务类型 (必需) patrol/strike/air_defense/recon
        - min_effectiveness: 最小效能评分 (0-1, 默认 0.5)
    """
    try:
        mission_type = request.args.get('mission_type')
        min_effectiveness = float(request.args.get('min_effectiveness', 0.5))

        if not mission_type:
            return jsonify({
                'success': False,
                'error': 'mission_type is required'
            }), 400

        if mission_type not in ['patrol', 'strike', 'air_defense', 'recon']:
            return jsonify({
                'success': False,
                'error': 'Invalid mission_type. Must be one of: patrol, strike, air_defense, recon'
            }), 400

        resources = global_resource_pool.search_by_capability(
            mission_type=mission_type,
            min_effectiveness=min_effectiveness
        )

        # 添加评分信息到返回结果
        results = []
        for r in resources:
            resource_dict = r.to_dict()
            resource_dict['match_effectiveness'] = r.capability.effectiveness_scores.get(mission_type, 0.0)
            results.append(resource_dict)

        return jsonify({
            'success': True,
            'mission_type': mission_type,
            'min_effectiveness': min_effectiveness,
            'count': len(results),
            'resources': results
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/pccs/statistics', methods=['GET'])
def get_pccs_statistics():
    """
    获取 PCCS 资源池统计信息
    """
    try:
        stats = global_resource_pool.get_statistics()

        # 添加更详细的统计信息
        all_resources = global_resource_pool.list_resources()

        # 按任务类型统计
        mission_type_counts = {}
        for mission_type in ['patrol', 'strike', 'air_defense', 'recon']:
            mission_type_counts[mission_type] = len([
                r for r in all_resources
                if mission_type in r.capability.mission_types
            ])

        # 按健康状态统计
        health_distribution = {
            'healthy': len([r for r in all_resources if r.state.health_level >= 0.8]),
            'degraded': len([r for r in all_resources if 0.5 <= r.state.health_level < 0.8]),
            'critical': len([r for r in all_resources if r.state.health_level < 0.5])
        }

        stats.update({
            'mission_type_counts': mission_type_counts,
            'health_distribution': health_distribution
        })

        return jsonify({
            'success': True,
            'statistics': stats
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/pccs/reload', methods=['POST'])
def reload_pccs_resources():
    """
    重新加载资源池 - 从数据库重新生成 PCCS 资源
    """
    try:
        db = get_db()

        # 清空现有资源池
        global_resource_pool.resources.clear()

        # 重新加载平台资源
        platforms = db.execute('SELECT * FROM platforms').fetchall()
        platform_count = 0

        for platform_row in platforms:
            platform_data = dict(platform_row)

            # 获取平台关联的装备
            equipments_rows = db.execute('''
                SELECT e.* FROM equipments e
                JOIN platform_equipment_link pe ON e.id = pe.equipment_id
                WHERE pe.platform_id = ?
            ''', (platform_data['id'],)).fetchall()

            equipments = [dict(r) for r in equipments_rows]

            # 转换为 PCCS 资源
            pccs_resource = pccs_adapter.convert_platform_to_pccs(platform_data, equipments)

            # 注册到资源池
            global_resource_pool.register_resource(pccs_resource)
            platform_count += 1

        # 重新加载装备资源 (可选：仅作为独立资源)
        equipments = db.execute('SELECT * FROM equipments').fetchall()
        equipment_count = 0

        for equipment_row in equipments:
            equipment_data = dict(equipment_row)

            # 转换为 PCCS 资源
            pccs_resource = pccs_adapter.convert_equipment_to_pccs(equipment_data)

            # 注册到资源池
            global_resource_pool.register_resource(pccs_resource)
            equipment_count += 1

        return jsonify({
            'success': True,
            'message': 'PCCS resource pool reloaded successfully',
            'platforms_loaded': platform_count,
            'equipments_loaded': equipment_count,
            'total': platform_count + equipment_count
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== Socket.IO handlers（集成 server.py 功能） ==========

@socketio.on('connect')
def on_connect():
    print(f"[socket] connect sid={request.sid}")

@socketio.on('disconnect')
def on_disconnect():
    print(f"[socket] disconnect sid={request.sid}")

@socketio.on('join_job')
def on_join_job(data):
    job_id = str((data or {}).get("job_id") or "")
    if job_id:
        room = f"job:{job_id}"
        join_room(room)
        emit("job/joined", {"job_id": job_id})
        print(f"[join_job] sid={request.sid} join {room}")

@socketio.on('cancel_job')
def on_cancel_job(data):
    job_id = str((data or {}).get("job_id") or "")
    if not job_id or job_id not in JOBS:
        emit("job/error", {"job_id": job_id, "error": "job_not_found"})
        return
    JOBS[job_id]["stop"].set()
    _emit_job(job_id, "job/stopped", {"job_id": job_id})

@socketio.on('submit_job')
def on_submit_job(data):
    """
    统一的训练/评估任务入口（磁盘目录名使用 ASCII 安全化）：
    - 训练：ckpt 保存到 jobs/<fs_job_id>/dqn.pt（除非显式给了带文件名的路径）
    - 自动评估（默认开）：仅 DQN 查 ckpt；找不到自动降级为 greedy
    - 仅评估：支持 from_train_job 或 *_eval 复用训练目录
    """
    sid = request.sid
    print(f"[submit_job] from {sid}: {data}")

    # -------- 基本参数 --------
    job_id   = (data.get("job_id") or f"job_{int(time.time())}").strip()
    job_type = (data.get("job_type") or "train").strip().lower()
    meta     = data.get("meta") or {}

    # -------- 磁盘目录一律用 ASCII 安全化名 --------
    fsid = _fs_job_id(job_id)
    base_dir = (Path("jobs") / fsid).resolve()
    (base_dir / "Task").mkdir(parents=True, exist_ok=True)
    (base_dir / "Resource").mkdir(parents=True, exist_ok=True)

    # WebSocket 房间仍使用原始 job_id（可含中文）
    join_room(f"job:{job_id}")

    # -------- 落地 Task/Resource 到 jobs/<fsid>/... --------
    try:
        task_dir, resource_dir = _materialize_job_dirs_from_db(job_id, meta)  # 函数内部已改为用 _fs_job_id
        task_dir = str(Path(task_dir).resolve())
        resource_dir = str(Path(resource_dir).resolve())
        socketio.emit("job/accepted", {
            "job_id": job_id,
            "job_type": job_type,
            "resolved_task_dir": task_dir,
            "resolved_resource_dir": resource_dir
        }, to=sid)
    except Exception as e:
        socketio.emit("job/error", {"job_id": job_id, "error": f"准备任务文件失败: {e}"}, to=sid)
        return

    if not job_id:
        emit("job/error", {"error": "missing job_id"}); return
    if job_id in JOBS:
        emit("job/error", {"job_id": job_id, "error": "job_id already exists"}); return

    stop_event = threading.Event()
    JOBS[job_id] = {"stop": stop_event, "task": None}

    # -------- 训练后台任务 --------
    def _run_train():
        try:
            p = data.get("train_params") or {}
            episodes      = int(p.get("episodes", 50))
            steps_per_ep  = int(p.get("steps_per_ep", p.get("stepsPerEp", 128)))
            epsilon       = float(p.get("epsilon", 0.3))
            epsilon_decay = float(p.get("epsilon_decay", p.get("epsilonDecay", 0.995)))
            trace_mode    = str(p.get("trace_mode", "episode"))

            # === checkpoint 规范化：目录/空 -> jobs/<fsid>/dqn.pt；相对 -> 基于 base_dir ===
            req_cp = str(p.get("checkpoint", "")).strip()
            if not req_cp:
                cp_path = base_dir / "dqn.pt"
            else:
                cp_path = Path(req_cp)
                # “像目录”的情况（无后缀或以分隔符结尾）→ 追加文件名
                if cp_path.suffix == "" or str(req_cp).endswith(("/", "\\")):
                    cp_path = cp_path / "dqn.pt"
                if not cp_path.is_absolute():
                    cp_path = (base_dir / cp_path).resolve()
            cp_path.parent.mkdir(parents=True, exist_ok=True)
            checkpoint = str(cp_path)

            def cb(rec: dict):
                event = "train/step" if rec.get("step") is not None else "train/episode"
                _emit_job(job_id, event, {"job_id": job_id, **rec})

            stats = train_stream(
                task_dir=task_dir, resource_dir=resource_dir,
                episodes=episodes, steps_per_ep=steps_per_ep,
                epsilon=epsilon, epsilon_decay=epsilon_decay,
                checkpoint=checkpoint, trace_out=None, trace_mode=trace_mode,
                callback=cb, stop_event=stop_event
            )

            # 回传真实 checkpoint（绝对路径）
            stats.setdefault("checkpoint", checkpoint)
            _emit_job(job_id, "train/done", {"job_id": job_id, **stats})

            # ===== 自动评估（默认 True）或前端显式带了 eval_params =====
            auto_eval = _as_bool(meta.get("auto_eval_after_train"), True) or bool(data.get("eval_params"))
            if auto_eval:
                pe = data.get("eval_params") or {}
                policy  = str(pe.get("policy", data.get("policy", "dqn"))).lower()
                ckpt_in = pe.get("checkpoint") or data.get("checkpoint") or checkpoint

                # 仅 DQN 查找 ckpt；找不到自动降级 greedy
                ckpt_path = None
                if policy == "dqn":
                    candidates = []
                    if ckpt_in: candidates.append(Path(ckpt_in))
                    candidates.append(base_dir / "dqn.pt")
                    candidates.append(Path("outputs") / "dqn.pt")
                    tried = []
                    for c in candidates:
                        if not c: continue
                        tried.append(str(c))
                        if Path(c).exists():
                            ckpt_path = Path(c).resolve()
                            break
                    if ckpt_path is None:
                        policy = "greedy"
                        print(f"[eval] checkpoint not found, fallback to greedy. tried: {', '.join(tried)}")
                else:
                    if ckpt_in: ckpt_path = Path(ckpt_in).resolve()

                out_dir = base_dir
                out_dir.mkdir(parents=True, exist_ok=True)
                if ckpt_path: ckpt_path.parent.mkdir(parents=True, exist_ok=True)

                _emit_job(job_id, "eval/starting", {"job_id": job_id, "policy": policy})
                out = eval_run(
                    task_dir=task_dir,
                    resource_dir=resource_dir,
                    policy=policy,
                    checkpoint=(str(ckpt_path) if ckpt_path else ""),
                    out_path=str(out_dir / "eval_result.json")
                )
                out.setdefault("meta", {})["from_train_job"] = job_id
                _emit_job(job_id, "eval/result", {"job_id": job_id, **out})

        except Exception as e:
            err = f"{e.__class__.__name__}: {e}"
            print("[train] error:", err); traceback.print_exc()
            _emit_job(job_id, "job/error", {"job_id": job_id, "error": err})
        finally:
            JOBS.pop(job_id, None)

    # -------- 仅评估后台任务 --------
    def _run_eval():
        try:
            pe = data.get("eval_params") or {}
            base_train_id = (meta.get("from_train_job") or (job_id[:-5] if job_id.endswith("_eval") else job_id))
            base_train_fsid = _fs_job_id(base_train_id)

            policy  = str(pe.get("policy", data.get("policy", "dqn"))).lower()
            ckpt_in = pe.get("checkpoint") or data.get("checkpoint")

            ckpt_path = None
            if policy == "dqn":
                candidates = []
                if ckpt_in: candidates.append(Path(ckpt_in))
                candidates.append(Path("jobs") / base_train_fsid / "dqn.pt")  # ★ 安全化目录名
                candidates.append(Path("outputs") / "dqn.pt")
                tried = []
                for c in candidates:
                    if not c: continue
                    tried.append(str(c))
                    if Path(c).exists():
                        ckpt_path = Path(c).resolve()
                        break
                if ckpt_path is None:
                    policy = "greedy"
                    print(f"[eval] checkpoint not found, fallback to greedy. tried: {', '.join(tried)}")
            else:
                if ckpt_in: ckpt_path = Path(ckpt_in).resolve()

            out_dir = (Path("jobs") / _fs_job_id(job_id)).resolve()
            out_dir.mkdir(parents=True, exist_ok=True)
            if ckpt_path: ckpt_path.parent.mkdir(parents=True, exist_ok=True)

            _emit_job(job_id, "eval/starting", {"job_id": job_id, "policy": policy})
            out = eval_run(
                task_dir=task_dir,
                resource_dir=resource_dir,
                policy=policy,
                checkpoint=(str(ckpt_path) if ckpt_path else ""),
                out_path=str(out_dir / "eval_result.json")
            )
            out.setdefault("meta", {})["from_train_job"] = base_train_id
            _emit_job(job_id, "eval/result", {"job_id": job_id, **out})
        except Exception as e:
            err = f"{e.__class__.__name__}: {e}"
            print("[eval] error:", err); traceback.print_exc()
            _emit_job(job_id, "job/error", {"job_id": job_id, "error": err})
        finally:
            JOBS.pop(job_id, None)

    # -------- 启动后台任务 --------
    task = socketio.start_background_task(_run_train if job_type == "train" else _run_eval)
    JOBS[job_id]["task"] = task


if __name__ == '__main__':
    # *** 核心修改：在启动服务器前，打印自定义的启动信息 ***

    # 使用 ANSI 转义码为输出添加一些颜色，使其更醒目
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'

    print(f"\n{BLUE}====================================================={RESET}")
    print(f"  🚀 {GREEN}对海作战仿真平台 - 后端服务正在启动...{RESET}")
    print(f"{BLUE}====================================================={RESET}")

    # *** 初始化 PCCS 资源池 ***
    try:
        from init_pccs_pool import init_pccs_resource_pool
        platform_count, equipment_count = init_pccs_resource_pool()
    except Exception as e:
        print(f"\n{YELLOW}⚠ PCCS 资源池初始化失败: {e}{RESET}")
        print(f"{YELLOW}  服务将继续启动，但 PCCS 功能可能不可用{RESET}\n")

    print(f"{BLUE}====================================================={RESET}")
    print(f"  {YELLOW}▶︎ 可访问地址:{RESET}")
    print(f"    - 本机访问:   {GREEN}http://127.0.0.1:5000{RESET} (推荐)")
    print(f"    - 本机访问:   {GREEN}http://localhost:5000{RESET}")
    # 你可以动态获取局域网IP并打印，但为了简单，这里只提供通用说明
    print(f"    - 局域网访问: {GREEN}http://<您的局域网IP>:5000{RESET}")
    print(f"\n  {YELLOW}▶︎ API 文档入口:{RESET}")
    print(f"    - {GREEN}http://127.0.0.1:5000/api/doc{RESET}")
    print(f"\n  {YELLOW}▶︎ 实时通信 (WebSocket):{RESET}")
    print(f"    - 路径: {GREEN}/socket.io/{RESET}")
    print(f"\n  {YELLOW}▶︎ PCCS 资源池:{RESET}")
    print(f"    - 资源池 API: {GREEN}/api/pccs/*{RESET}")
    print(f"{BLUE}====================================================={RESET}\n")
    
    # 使用 eventlet 时，Flask 的原生 debug 模式可能不完全兼容，
    # socketio.run 自带了重载功能，所以可以关闭 Flask 的 debug=True
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
