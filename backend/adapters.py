from __future__ import annotations
import json, os, re, math
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from pathlib import Path

# -------------------- small utils --------------------

_NUM_RE = re.compile(r"[-+]?\d+(?:\.\d+)?")

def _to_float(x, default=0.0) -> float:
    try:
        if isinstance(x, (int, float)):
            return float(x)
        if isinstance(x, str):
            m = _NUM_RE.search(x)
            return float(m.group(0)) if m else default
        return default
    except Exception:
        return default

def _parse_kph(s: Any) -> float:
    if not s: return 0.0
    if isinstance(s, (int, float)): return float(s)
    s = str(s).lower()
    v = _to_float(s, 0.0)
    if "km/h" in s or "公里/小时" in s: return v
    if "m/s" in s or "米/秒" in s: return v * 3.6
    if "kn" in s or "节" in s: return v * 1.852
    return v

# ——避免 "km" 被 "m" 命中：先匹配 km，再 nm，最后米——
def _parse_km(s: Any) -> float:
    if not s: return 0.0
    if isinstance(s, (int, float)): return float(s)
    s = str(s).lower()
    v = _to_float(s, 0.0)
    if "km" in s or "公里" in s or "千米" in s: return v
    if "nm" in s or "海里" in s: return v * 1.852
    if "米" in s or re.search(r'(^|\D)m($|\D)', s): return v / 1000.0
    return v

def _parse_time(s: Any) -> Optional[datetime]:
    if not s: return None
    if isinstance(s, (int, float)):
        try: return datetime.utcfromtimestamp(float(s))
        except: return None
    for fmt in ["%Y-%m-%d %H:%M:%S","%Y/%m/%d %H:%M:%S","%Y-%m-%dT%H:%M:%SZ","%Y-%m-%d","%Y/%m/%d"]:
        try: return datetime.strptime(str(s), fmt)
        except: pass
    return None

def _parse_count(v: Any) -> int:
    if v is None: return 0
    if isinstance(v, (int, float)): return max(0, int(v))
    if isinstance(v, str): return max(0, int(_to_float(v, 0.0)))
    if isinstance(v, list):
        nums=[]
        for x in v:
            n=_to_float(x, None)
            if n is not None: nums.append(int(n))
        return max(nums) if nums else 0
    return 0

# -------------------- canonical models --------------------

@dataclass
class CanonTask:
    tid: str
    name: str
    scene: str
    kind: str            # patrol | recon | strike | air_defense | generic
    domain: str          # sea | air | mixed
    # time
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    deadline_min: float = 0.0
    # area (optional) 采用 (lon, lat)
    area_center: Optional[Tuple[float,float]] = None
    area_km2: float = 0.0
    # hard requirements
    type_whitelist: List[str] = field(default_factory=list)
    speed_min_kph: float = 0.0
    radar_min_km: float = 0.0
    min_units: int = 0
    requires: Dict[str, Any] = field(default_factory=dict)
    # demands（统一 act 语义）
    demand: Dict[str, float] = field(default_factory=lambda: {"sense":0.0,"comm":0.0,"act":0.0})
    sub_demand: Dict[str, float] = field(default_factory=lambda: {"act_strike":0.0,"act_resupply":0.0})
    redundancy: float = 0.0
    priority: float = 1.0

@dataclass
class CanonResource:
    rid: str
    name: str
    domain: str           # sea | air | other
    rtype: str            # 驱逐舰/潜艇/巡逻舰/航空母舰/战斗机/运输机/预警机/无人机/轰炸机/攻击机/...
    speed_mps: float
    endurance_min: float
    sensors: float
    comms: float
    cargo: float
    cost_per_hour: float = 1.0
    start_pos: Optional[Tuple[float,float]] = None   # (lon, lat)
    tags: Dict[str, bool] = field(default_factory=dict)
    sub_caps: Dict[str, float] = field(default_factory=lambda: {"act_strike":0.0, "act_resupply":0.0})
    max_uses: int = 999
    cooldown_min: float = 0.0

    def has_cap(self, cap:str)->bool:
        if cap in ("cargo","act"):
            if self.cargo > 0: return True
            if self.sub_caps.get("act_strike",0.0) > 0: return True
            if self.sub_caps.get("act_resupply",0.0) > 0: return True
            # 兼容旧键名
            if self.sub_caps.get("cargo_strike",0.0) > 0: return True
            if self.sub_caps.get("cargo_resupply",0.0) > 0: return True
            return False
        if cap=="sense": return self.sensors>0
        if cap=="comm":  return self.comms>0
        return False

# -------------------- domain/kind inference --------------------

def _infer_kind(scene: str) -> str:
    s = scene or ""
    if "巡逻" in s: return "patrol"
    if "侦察" in s: return "recon"
    if any(k in s for k in ["反导","防空","制空"]): return "air_defense"
    if any(k in s for k in ["打击","攻击"]): return "strike"
    return "generic"

def _infer_domain_from_scene(scene: str) -> str:
    s = scene or ""
    if "对海" in s: return "sea"
    if "对空" in s: return "air"
    return "mixed"

# -------------------- parse Task --------------------

_REGION_KEYS = ["巡逻区域","侦察区域","巡逻区","侦察区","区域","area","AOI","aoi"]
_CORNER_KEYS = ["左上角","右上角","左下角","右下角","top_left","topRight","bottom_left","bottomRight"]

def _extract_rect_area(d: Dict[str,Any]) -> Tuple[Optional[Tuple[float,float]], float]:
    rect = None
    for k in _REGION_KEYS:
        if k in d and isinstance(d[k], dict):
            rect = d[k]; break
    if not rect: return None, 0.0
    pts=[]
    for ck in _CORNER_KEYS:
        v = rect.get(ck)
        if isinstance(v,(list,tuple)) and len(v)>=2:
            pts.append((float(_to_float(v[0])), float(_to_float(v[1]))))  # JSON 为 [lon, lat]
    if len(pts)<2: return None, 0.0
    lons=[p[0] for p in pts]; lats=[p[1] for p in pts]
    lon_span=(max(lons)-min(lons))*111.0*abs(math.cos(math.radians(sum(lats)/len(lats))))
    lat_span=(max(lats)-min(lats))*111.0
    return ((sum(lons)/len(lons), sum(lats)/len(lats))), max(0.0, lon_span*lat_span)

# ——去掉“巡逻舰”误并到“护卫舰”；中文精确 > 别名 > 中文子串——
TYPE_ALIASES: Dict[str, List[str]] = {
    # Surface/Undersea
    "巡逻舰": ["巡逻舰","巡逻","patrol boat","patrol"],
    "驱逐舰": ["驱逐","destroyer","ddg"],
    "护卫舰": ["护卫","frigate","ffg"],
    "潜艇":   ["潜艇","submarine","ssn","ssbn","ss"],
    "航空母舰": ["航母","航空母舰","carrier","cvn"],
    "两栖攻击舰": ["两栖","两栖攻击舰","lhd","lha","amphib"],
    "补给舰": ["补给","补给舰","supply","aoe","aor"],

    # Aircraft
    "战斗机": ["战斗机","fighter","f-","f "],
    "轰炸机": ["轰炸机","b-","b "],
    "攻击机": ["攻击机","a-10","a10"],
    "预警机": ["预警机","e-3","e3","awacs","sentry"],
    "运输机": ["运输机","c-130","c130","c-17","il-76","a400m"],
    "无人机": ["无人机","uav","mq-9","mq9","reaper"],
}

def _canonicalize_type(s: str) -> str:
    if not s: return ""
    for k in TYPE_ALIASES.keys():           # 中文精确
        if s == k: return k
    low = s.lower()
    for k, arr in TYPE_ALIASES.items():     # 别名
        if any(a in low for a in arr): return k
    for k in TYPE_ALIASES.keys():           # 中文子串兜底
        if k in s: return k
    return s

# ——“无偏好/不限”即 0；不再强制最小=1——
def _parse_min_units(block) -> int:
    if block is None: return 0
    if isinstance(block, (int, float)): return max(0, int(block))
    if isinstance(block, str):
        if ("无偏好" in block) or ("不限" in block): return 0
        return max(0, int(_to_float(block, 0.0)))
    if isinstance(block, list):
        txt = "".join(map(str, block))
        if ("无偏好" in txt) or ("不限" in txt): return 0
        nums=[]
        for x in block:
            m = _NUM_RE.search(str(x))
            if m: nums.append(int(float(m.group(0))))
        return (2 if 2 in nums else (max(0, min(nums)) if nums else 0))
    return 0

def _extract_task_demands_by_kind(kind:str) -> Tuple[Dict[str,float], Dict[str,float]]:
    demand={"sense":0.0,"comm":0.0,"act":0.0}
    sub={"act_strike":0.0,"act_resupply":0.0}
    if kind in ("patrol","recon"):
        demand["sense"]=1.0; demand["comm"]=1.0
    elif kind in ("strike","air_defense"):
        demand["sense"]=1.0; demand["comm"]=1.0; demand["act"]=1.0
        sub["act_strike"]=1.0
    return demand, sub

def _merge_req_block_into_task(block: Dict[str,Any], type_whitelist: List[str], task: CanonTask):
    if not isinstance(block, dict): return
    # 类型
    type_req = block.get("类型要求") or block.get("类型") or []
    if isinstance(type_req, list):
        for x in type_req:
            v=_canonicalize_type(str(x))
            if v and v not in type_whitelist:
                type_whitelist.append(v)
    elif isinstance(type_req, str):
        v=_canonicalize_type(type_req)
        if v and v not in type_whitelist:
            type_whitelist.append(v)
    # 能力阈值
    cap_req = block.get("能力要求") or {}
    if isinstance(cap_req, dict):
        for k in ("行驶速度","出航速度","速度"):
            if k in cap_req:
                task.speed_min_kph = max(task.speed_min_kph, _parse_kph(cap_req.get(k)))
        for k in ("雷达能力","感知范围"):
            if k in cap_req:
                task.radar_min_km = max(task.radar_min_km, _parse_km(cap_req.get(k)))
        mu = cap_req.get("启用任务所需的装备最低数量")
        if mu is not None:
            task.min_units = max(task.min_units, _parse_min_units(mu))
        # 打击半径 & 弹药量映射到 act 需求
        if "最小打击半径" in cap_req:
            task.requires["strike_r_min_km"] = max(float(task.requires.get("strike_r_min_km", 0.0)),
                                                   _parse_km(cap_req["最小打击半径"]))
        if "最大打击半径" in cap_req:
            task.requires["strike_r_max_km"] = max(float(task.requires.get("strike_r_max_km", 0.0)),
                                                   _parse_km(cap_req["最大打击半径"]))
        if "弹药最低数量" in cap_req:
            c = _parse_count(cap_req["弹药最低数量"])
            task.sub_demand["act_strike"] = max(task.sub_demand.get("act_strike",0.0), float(c))
            task.demand["act"] = max(task.demand.get("act",0.0), float(c))

def _apply_enemy_targets_and_damage(raw: Dict[str,Any], task: CanonTask):
    targets = raw.get("敌方目标", []) or []
    if targets:
        xs=[]; ys=[]
        for t in targets:
            pos = t.get("position") or t.get("坐标")
            if isinstance(pos,(list,tuple)) and len(pos)>=2:
                xs.append(float(_to_float(pos[0]))); ys.append(float(_to_float(pos[1])))
        if xs and ys:
            lon_mid = sum(xs)/len(xs); lat_mid = sum(ys)/len(ys)
            lon_span = (max(xs)-min(xs))*111.0*abs(math.cos(math.radians(lat_mid)))
            lat_span = (max(ys)-min(ys))*111.0
            task.area_center = (lon_mid, lat_mid) if task.area_center is None else task.area_center
            task.area_km2    = max(task.area_km2, lon_span*lat_span)

        n_tgt = len(xs)
        dmg_lv = (raw.get("期望毁伤率") or ["完全摧毁"])[0]
        if isinstance(dmg_lv, str) and any(k in dmg_lv for k in ["仅攻击一次","仅一次攻击","仅攻击1次"]):
            inc = 1
        else:
            alpha = {"完全摧毁":1.0, "重创":0.8, "部分摧毁":0.6, "轻创":0.4}.get(dmg_lv, 0.6)
            inc = max(1, int(math.ceil(alpha*n_tgt)))
        # ——将需求提升应用到任务（修复此前仅在 else 分支才应用的问题）——
        if n_tgt > 0 and task.kind in ("strike","air_defense","generic"):
            task.demand["act"] = max(task.demand.get("act",0.0), float(inc))
            task.sub_demand["act_strike"] = max(task.sub_demand.get("act_strike",0.0), float(inc))
            task.priority = min(5.0, task.priority * (1.0 + 0.2*n_tgt))

def _post_calibrate_task(t: CanonTask, clamp_sea_speed: bool = True):
    """
    任务规范化：在不改 env 的前提下，避免不合理阈值把奖励拉负。
    - 海域任务（可开关）：把速度阈值钳制到 60 km/h（≈32 kn）上限。
    - 巡逻/侦察：确保没有误引入 act 需求。
    """
    if clamp_sea_speed and (t.domain == "sea") and (t.speed_min_kph > 60.0):
        t.requires["orig_speed_min_kph"] = float(t.speed_min_kph)  # 记录原值以便追踪
        t.speed_min_kph = 60.0

    if t.kind in ("patrol","recon"):
        # 强保证：无 act 需求（有些表单项可能把数量/半径误写进来了）
        t.demand["act"] = 0.0
        t.sub_demand["act_strike"] = 0.0
        t.sub_demand["act_resupply"] = 0.0

def load_tasks(task_files: List[str], clamp_sea_speed: bool = True) -> List[CanonTask]:
    tasks: List[CanonTask] = []
    for i, p in enumerate(task_files):
        with open(p, "r", encoding="utf-8") as f:
            d = json.load(f)
        # 任务名兼容：优先“名称”→“合同名称”→文件名
        name = d.get("名称") or d.get("合同名称") or Path(p).name
        scene = d.get("作战场景") or ""
        kind  = _infer_kind(scene)
        domain= _infer_domain_from_scene(scene)

        # time
        tinfo = d.get("作战时间", {})
        st = _parse_time(tinfo.get("开始时间"))
        et = _parse_time(tinfo.get("结束时间"))
        deadline_min = float(((et-st).total_seconds()/60.0) if (st and et) else 0.0)

        # region
        area_center, area_km2 = _extract_rect_area(d)

        # default demands by kind
        demand, sub_demand = _extract_task_demands_by_kind(kind)

        canon = CanonTask(
            tid=str(i), name=name, scene=scene, kind=kind, domain=domain,
            start_time=st, end_time=et, deadline_min=deadline_min,
            area_center=area_center, area_km2=area_km2,
            type_whitelist=[], speed_min_kph=0.0, radar_min_km=0.0, min_units=0,
            requires={}, demand=demand, sub_demand=sub_demand,
            redundancy=0.0, priority=float(d.get("priority") or d.get("优先级") or 1.0)
        )

        # 兼容新/旧三块“装备要求”
        type_whitelist: List[str] = []
        _merge_req_block_into_task(d.get("巡逻作战装备要求") or {}, type_whitelist, canon)
        _merge_req_block_into_task(d.get("侦察作战装备要求") or {}, type_whitelist, canon)
        _merge_req_block_into_task(d.get("感知Sense作战装备要求") or {}, type_whitelist, canon)
        _merge_req_block_into_task(d.get("控制Command作战装备要求") or {}, type_whitelist, canon)
        _merge_req_block_into_task(d.get("执行Act作战装备要求") or {}, type_whitelist, canon)
        canon.type_whitelist = type_whitelist

        # 最低数量 -> 提升需求
        if canon.min_units>0:
            if kind in ("patrol","recon"):
                canon.demand["sense"] = max(canon.demand.get("sense",0.0), float(canon.min_units))
                canon.demand["comm"]  = max(canon.demand.get("comm",0.0),  float(canon.min_units))
            else:
                canon.demand["act"] = max(canon.demand.get("act",0.0), float(canon.min_units))
                canon.sub_demand["act_strike"] = max(canon.sub_demand.get("act_strike",0.0), float(canon.min_units))

        # 敌目标 + 毁伤等级 -> 目标驱动的 act 需求
        _apply_enemy_targets_and_damage(d, canon)

        # 任务后校准（关键修复）
        _post_calibrate_task(canon, clamp_sea_speed=clamp_sea_speed)

        # 兼容旧键名（如外部统计）
        canon.requires["compat_demand_cargo"] = float(canon.demand.get("act",0.0))
        canon.requires["compat_sub_cargo_strike"] = float(canon.sub_demand.get("act_strike",0.0))
        canon.requires["compat_sub_cargo_resupply"] = float(canon.sub_demand.get("act_resupply",0.0))

        tasks.append(canon)
    return tasks

# -------------------- parse Resources --------------------

def _aircraft_role_from_name(name: str) -> str:
    n = (name or "").lower()
    if any(k in n for k in ["e-3","awacs","sentry"]): return "预警机"
    if any(k in n for k in ["mq-9","reaper","uav","drone"]): return "无人机"
    if any(k in n for k in ["c-130","c130","c-17","il-76","a400m"]): return "运输机"
    if any(k in n for k in ["b-2","b2","b-1","b-52"]): return "轰炸机"
    if any(k in n for k in ["a-10","a10","su-25"]): return "攻击机"
    if any(k in n for k in ["f-22","f22","f-35","f35","f-16","f16","f-14","f14","su-","mig-"]): return "战斗机"
    return "战斗机"

def _extract_caps_from_air_item(item: Dict[str,Any], name: str) -> Tuple[float,float,float, Dict[str,bool], Dict[str,float], float]:
    n = (name or "").lower()
    sensors = 1.0
    comms = 1.0 if any(k in n for k in ["e-3","awacs","sentry","link-16","link16"]) else 0.5
    cargo = 1.0 if any(k in n for k in ["c-130","c-17","il-76","a400m"]) else 0.0
    sub = {"act_strike": 1.0 if any(k in n for k in ["f-","b-","a-10","mq-9"]) else 0.0,
           "act_resupply": 1.0 if cargo>0 else 0.0}
    tags = {
        "strike_capable": sub["act_strike"]>0.0,
        "anti_ship": any(k in n for k in ["harpoon","雄风","鹰击","exocet"]),
        "bvr": any(k in n for k in ["aim-120","meteor","pl-15"])
    }
    params = (item.get("vehicle") or {}).get("params", {})
    max_speed = params.get("maxSpeed") or params.get("cruiseSpeed") or 900  # km/h
    speed_kph = _parse_kph(max_speed) if isinstance(max_speed, (int,float,str)) else 900
    return sensors, comms, cargo, tags, sub, speed_kph/3.6

def _extract_start_pos_from_generic(obj: Dict[str,Any]) -> Optional[Tuple[float,float]]:
    # 尝试多个常见路径：顶层 start_pos/position/坐标；或 params 中 lon/lat、longitude/latitude、lng/lat
    sp = obj.get("start_pos") or obj.get("position") or obj.get("坐标")
    if not sp:
        params = obj.get("params") or (obj.get("vehicle") or {}).get("params") or {}
        candidates = [
            (params.get("lon"), params.get("lat")),
            (params.get("longitude"), params.get("latitude")),
            (params.get("lng"), params.get("lat")),
            (params.get("x"), params.get("y")),
        ]
        for c in candidates:
            if isinstance(c, (list, tuple)) and len(c) >= 2 and (c[0] is not None) and (c[1] is not None):
                sp = c; break
    if isinstance(sp, (list, tuple)) and len(sp) >= 2:
        try:
            return (float(_to_float(sp[0])), float(_to_float(sp[1])))
        except Exception:
            return None
    return None

def load_air_resources(files: List[str]) -> List[CanonResource]:
    out=[]
    for p in files:
        d=json.load(open(p,"r",encoding="utf-8"))
        if not isinstance(d, dict): continue
        for k, item in d.items():
            veh=(item.get("vehicle") or {})
            name=str(veh.get("name") or item.get("name") or f"air-{k}")
            rtype=_aircraft_role_from_name(name)
            sensors,comms,cargo,tags,sub_act,speed_mps=_extract_caps_from_air_item(item, name)
            sub_act = dict(sub_act)
            # 兼容旧键名
            sub_act["cargo_strike"]   = sub_act.get("act_strike",0.0)
            sub_act["cargo_resupply"] = sub_act.get("act_resupply",0.0)
            start_pos = _extract_start_pos_from_generic(item)
            out.append(CanonResource(
                rid=f"A-{k}", name=name, domain="air", rtype=rtype,
                speed_mps=float(speed_mps),
                endurance_min=180.0,
                sensors=float(sensors), comms=float(comms), cargo=float(cargo),
                cost_per_hour=1.0, start_pos=start_pos, tags=tags, sub_caps=sub_act,
                max_uses=3, cooldown_min=20.0
            ))
    return out

def load_sea_resources(files: List[str]) -> List[CanonResource]:
    out=[]
    for p in files:
        arr=json.load(open(p,"r",encoding="utf-8"))
        if not isinstance(arr, list): continue
        for i, item in enumerate(arr):
            name = str(item.get("name") or f"ship-{i}")
            rtype = _canonicalize_type(str(item.get("type") or "舰艇"))
            params = item.get("params",{})
            v = _to_float(params.get("最大航速") or params.get("maxSpeed") or params.get("航速") or "20")
            # v<80 视为节(knots) -> km/h
            speed_kph = v*1.852 if v<80 else v
            sensors = 1.0
            comms = 1.0
            cargo = 1.0 if rtype in ("航空母舰","两栖攻击舰","补给舰") else 0.2
            has_missile = any(
                str(e.get("type","")).lower().find("missile")>=0 or
                "反舰" in (e.get("name","")+e.get("type",""))
                for e in item.get("equipment",[])
            )
            sub_act = {
                "act_strike": 1.0 if has_missile else 0.0,
                "act_resupply": 1.0 if rtype in ("补给舰","两栖攻击舰","航空母舰") else 0.0
            }
            sub_act["cargo_strike"]   = sub_act["act_strike"]
            sub_act["cargo_resupply"] = sub_act["act_resupply"]
            tags={"strike_capable": sub_act["act_strike"]>0.0,
                  "anti_ship": any("反舰" in (e.get("name","")+e.get("type","")) for e in item.get("equipment",[])),
                  "bvr": False}
            start_pos = _extract_start_pos_from_generic(item)
            out.append(CanonResource(
                rid=f"S-{i}", name=name, domain="sea", rtype=rtype,
                speed_mps=float(speed_kph)/3.6, endurance_min=10080.0,
                sensors=float(sensors), comms=float(comms), cargo=float(cargo),
                cost_per_hour=2.0, start_pos=start_pos, tags=tags, sub_caps=sub_act,
                max_uses=999, cooldown_min=0.0
            ))
    return out

def load_resources(air_json: str, ship_json: str) -> List[CanonResource]:
    out=[]
    if air_json and os.path.exists(air_json): out.extend(load_air_resources([air_json]))
    if ship_json and os.path.exists(ship_json): out.extend(load_sea_resources([ship_json]))
    return out

# -------------------- directory scanners --------------------

def scan_task_files(task_dir: Path) -> List[str]:
    task_dir = Path(task_dir)
    return [str(p) for p in sorted(task_dir.glob("*.json")) if p.is_file()]

def scan_resource_files(resource_dir: Path) -> Tuple[Optional[str], Optional[str]]:
    air_json = None
    ship_json = None
    for p in sorted(Path(resource_dir).glob("*.json")):
        try:
            d = json.load(open(p, "r", encoding="utf-8"))
        except Exception:
            continue
        if isinstance(d, dict) and any(isinstance(v, dict) and "vehicle" in v for v in d.values()):
            if air_json is None:
                air_json = str(p)
        elif isinstance(d, list):
            if ship_json is None:
                ship_json = str(p)
    if air_json is None:
        for p in sorted(Path(resource_dir).glob("*.json")):
            try:
                if isinstance(json.load(open(p, "r", encoding="utf-8")), dict):
                    air_json = str(p); break
            except: pass
    if ship_json is None:
        for p in sorted(Path(resource_dir).glob("*.json")):
            try:
                if isinstance(json.load(open(p, "r", encoding="utf-8")), list):
                    ship_json = str(p); break
            except: pass
    return air_json, ship_json

# ----------- directory loaders -----------

def load_tasks_from_dir(task_dir: str | Path, clamp_sea_speed: bool = True) -> List[CanonTask]:
    task_dir = Path(task_dir)
    paths = [str(p) for p in sorted(task_dir.glob("*.json")) if p.is_file()]
    if not paths:
        raise FileNotFoundError(f"No task JSON found under: {task_dir}")
    return load_tasks(paths, clamp_sea_speed=clamp_sea_speed)

def load_resources_from_dir(resource_dir: str | Path) -> List[CanonResource]:
    resource_dir = Path(resource_dir)
    air_files: List[str] = []
    sea_files: List[str] = []

    for p in sorted(resource_dir.glob("*.json")):
        if not p.is_file():
            continue
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue
        if isinstance(data, dict) and any(isinstance(v, dict) and "vehicle" in v for v in data.values()):
            air_files.append(str(p))
        elif isinstance(data, list):
            sea_files.append(str(p))

    if not air_files and not sea_files:
        for p in sorted(resource_dir.glob("*.json")):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                continue
            if isinstance(data, dict):
                air_files.append(str(p))
            elif isinstance(data, list):
                sea_files.append(str(p))

    out: List[CanonResource] = []
    if air_files:
        out.extend(load_air_resources(air_files))
    if sea_files:
        out.extend(load_sea_resources(sea_files))

    if not out:
        raise FileNotFoundError(f"No valid resource JSON found under: {resource_dir}")
    return out