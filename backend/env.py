from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Tuple, Any, Optional
import numpy as np
import math

from adapters import CanonTask, CanonResource

CAPS = ["sense", "comm", "act"]

# ---------- geo helpers ----------

def _haversine_km(p1: Tuple[float,float], p2: Tuple[float,float]) -> float:
    if not p1 or not p2: return 0.0
    lon1, lat1 = float(p1[0]), float(p1[1])
    lon2, lat2 = float(p2[0]), float(p2[1])
    R = 6371.0
    phi1 = math.radians(lat1); phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl   = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dl/2)**2
    c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R*c

# ---------- type whitelist helper (宽匹配) ----------

def _type_ok_with_whitelist(rtype: str, rdomain: str, whitelist: List[str]) -> bool:
    if not whitelist:
        return True
    wset = set(whitelist)
    if rtype in wset:
        return True
    umbrella_air = {"飞行器","航空器","aircraft"}
    umbrella_sea = {"舰艇","舰船","ship","vessel"}
    umbrella_car = {"航母","航空母舰","carrier","cvn"}
    if wset & umbrella_air and rdomain == "air":
        return True
    if wset & umbrella_sea and rdomain == "sea":
        return True
    if wset & umbrella_car and rtype in ("航空母舰","两栖攻击舰"):
        return True
    return False

@dataclass
class EnvConfig:
    # 基础权重
    w_cover: float = 1.0
    w_scarcity: float = 0.1
    w_submatch: float = 0.2
    w_over: float = -0.5
    w_cost: float = -0.01
    # 时效按“剩余占比”衰减
    k_timeliness: float = 0.02  # 每步惩罚系数（乘以剩余占比）
    # 硬约束 & 塑形
    enforce_type_whitelist: bool = True
    enforce_speed_threshold: bool = False   # 软/硬约束开关；软时仅塑形
    enforce_reachability: bool = True
    # 类型/速度塑形
    w_type_match: float = 0.5
    w_type_mismatch: float = -5.0
    k_speed_shortfall: float = 3.0   # 速度不足线性系数（越大扣得越多）
    k_speed_excess: float = 0.5      # 速度满足时的小额奖励（上限1.0）
    # 子能力
    use_sub_demands: bool = True
    w_sub_mismatch: float = -0.3     # act 子能力未命中时的小额惩罚
    require_strike_subcap: bool = True  # 打击/反导任务要求 act_strike 子能力

class ResourceTaskEnv:
    def __init__(self, tasks: List[CanonTask], resources: List[CanonResource], cfg: EnvConfig = EnvConfig(), seed: int = 0):
        self.tasks = tasks
        self.resources = resources
        self.cfg = cfg
        self.rng = np.random.default_rng(seed)
        # vocab
        self.rtype_vocab = sorted({r.rtype for r in resources})
        self.kind_vocab = ["patrol","recon","strike","air_defense","generic"]
        self.domain_vocab = ["sea","air","mixed"]
        self.reset(seed)

    # ------------- public API -------------

    def reset(self, seed: Optional[int]=None):
        if seed is not None:
            self.rng = np.random.default_rng(seed)
        self.steps = 0
        # task state
        self.task_state: List[Dict[str,Any]] = []
        for t in self.tasks:
            self.task_state.append({
                "task": t,
                "done": False,
                "rem": dict(t.demand),
                "sub_rem": dict(t.sub_demand),
            })
        # resource state
        self.res_state: List[Dict[str,Any]] = []
        for r in self.resources:
            self.res_state.append({
                "res": r,
                "available": 1,
                "remaining_min": float(r.endurance_min),
                "uses_left": int(r.max_uses),
                "cooldown_remaining": 0.0,
            })
        # 记录初始总需求（用于时效惩罚的占比计算）
        self.initial_demand_sum = 0.0
        for ts in self.task_state:
            self.initial_demand_sum += sum(max(0.0, v) for v in ts["rem"].values())
        if self.initial_demand_sum <= 0:
            self.initial_demand_sum = 1.0
        self._rebuild_legal()
        return self.observe()

    def observe(self) -> np.ndarray:
        rems = []
        for ts in self.task_state:
            rems.extend([ts["rem"].get("sense",0.0), ts["rem"].get("comm",0.0), ts["rem"].get("act",0.0)])
        vec = np.array(rems + [0.0]*max(0, 16 - len(rems)), dtype=np.float32)
        return vec

    def action_space_n(self) -> int:
        return len(self.legal_actions)

    # ---------- 合法性判定（集中管理） ----------
    def _action_allowed(self, r: CanonResource, t: CanonTask, cap: str) -> bool:
        # 域路由
        if t.domain == "sea" and r.domain not in ("sea","air"):
            return False
        if t.domain == "air" and r.domain != "air":
            return False
        # 类型白名单（硬）
        type_ok  = _type_ok_with_whitelist(r.rtype, r.domain, t.type_whitelist)
        if self.cfg.enforce_type_whitelist and not type_ok:
            return False
        # 速度阈值（可选择硬/软）
        if self.cfg.enforce_speed_threshold and t.speed_min_kph > 0.0:
            if (r.speed_mps*3.6) < t.speed_min_kph:
                return False
        # 打击/反导任务：act 必须具备 strike 子能力
        if cap == "act" and self.cfg.require_strike_subcap and t.kind in ("strike","air_defense"):
            if float(r.sub_caps.get("act_strike", 0.0)) <= 0.0:
                return False
        # reachability（有足够信息时判断）
        if self.cfg.enforce_reachability and (t.area_center is not None) and (r.start_pos is not None) and (r.speed_mps>0):
            dist_km = _haversine_km(r.start_pos, t.area_center)
            speed_kph = float(r.speed_mps)*3.6
            eta_min = 60.0 * dist_km / max(1.0, speed_kph)
            time_budget = float(self._time_budget_for_task(t))
            if eta_min > time_budget:
                return False
        # 自身能力
        if cap == "sense" and r.sensors <= 0: return False
        if cap == "comm"  and r.comms   <= 0: return False
        if cap == "act"   and not r.has_cap("act"): return False
        return True

    def _time_budget_for_task(self, t: CanonTask) -> float:
        # 若任务有截止时间则使用，否则取资源侧 remaining_min 时再最小化
        if isinstance(t.deadline_min, (int, float)) and t.deadline_min > 0:
            return float(t.deadline_min)
        # 回退：给一个大窗口
        return 1e9

    def step(self, a: int):
        if a < 0 or a >= len(self.legal_actions):
            a = len(self.legal_actions)-1  # noop
        (i, j, cap) = self.legal_actions[a]
        detail = {
            "cover":0.0,"scarcity":0.0,"submatch":0.0,"over":0.0,
            "cost":0.0,"timeliness":0.0
        }

        if cap == "noop":
            # 时效（按剩余占比）
            unmet = sum(sum(max(0.0, v) for v in ts2["rem"].values()) for ts2 in self.task_state if not ts2["done"])
            ratio = unmet / max(1.0, self.initial_demand_sum)
            detail["timeliness"] = - self.cfg.k_timeliness * ratio
            self.steps += 1
            self._rebuild_legal()
            return self.observe(), float(sum(detail.values())), self._check_done(), {"reward_detail": detail}

        rs = self.res_state[i]; r: CanonResource = rs["res"]
        ts = self.task_state[j]; t: CanonTask = ts["task"]

        # coverage
        took = 0.0
        if ts["rem"].get(cap,0.0) > 0.0 and r.has_cap(cap):
            ts["rem"][cap] = max(0.0, ts["rem"][cap] - 1.0)
            took = 1.0
            detail["cover"] += self.cfg.w_cover * t.priority

        # submatch / mismatch（仅 act）
        if cap == "act" and self.cfg.use_sub_demands:
            hit = False
            if ts["sub_rem"].get("act_strike",0.0) > 0.0 and r.sub_caps.get("act_strike",0.0) > 0.0:
                ts["sub_rem"]["act_strike"] = max(0.0, ts["sub_rem"]["act_strike"] - 1.0)
                detail["submatch"] += self.cfg.w_submatch
                hit = True
            if ts["sub_rem"].get("act_resupply",0.0) > 0.0 and r.sub_caps.get("act_resupply",0.0) > 0.0:
                ts["sub_rem"]["act_resupply"] = max(0.0, ts["sub_rem"]["act_resupply"] - 1.0)
                detail["submatch"] += self.cfg.w_submatch
                hit = True
            if not hit:
                detail["submatch"] += self.cfg.w_sub_mismatch

        # over-assign
        if took == 0.0:
            detail["over"] += self.cfg.w_over

        # cost
        detail["cost"] += self.cfg.w_cost * float(r.cost_per_hour)

        # scarcity（基于“合法供给”）
        scarcity = self._cap_scarcity(cap)
        detail["scarcity"] += self.cfg.w_scarcity * scarcity

        # 类型塑形
        type_ok = _type_ok_with_whitelist(r.rtype, r.domain, t.type_whitelist)
        detail["type_match"] = (self.cfg.w_type_match if type_ok else self.cfg.w_type_mismatch)

        # 速度塑形：按比例线性
        if t.speed_min_kph > 0.0:
            speed_kph = float(r.speed_mps) * 3.6
            ratio = speed_kph / max(1.0, t.speed_min_kph)
            if ratio >= 1.0:
                detail["speed_meet"] = self.cfg.k_speed_excess * min(1.0, ratio)
            else:
                detail["speed_meet"] = - self.cfg.k_speed_shortfall * (1.0 - ratio)
        else:
            detail["speed_meet"] = 0.0

        # 时效（按剩余占比）
        unmet = sum(sum(max(0.0, v) for v in ts2["rem"].values()) for ts2 in self.task_state if not ts2["done"])
        ratio = unmet / max(1.0, self.initial_demand_sum)
        detail["timeliness"] = - self.cfg.k_timeliness * ratio

        # resource bookkeeping
        rs["uses_left"] = max(0, rs["uses_left"]-1)
        rs["remaining_min"] = max(0.0, rs["remaining_min"]-30.0)
        self.steps += 1

        # task done?
        self._update_task_done(ts)
        self._rebuild_legal()

        total = float(sum(detail.values()))
        return self.observe(), total, self._check_done(), {"reward_detail": detail}

    def simulate_step_reward_detail(self, a: int) -> Tuple[float, Dict[str,float]]:
        if a < 0 or a >= len(self.legal_actions):
            return 0.0, {}
        (i,j,cap) = self.legal_actions[a]
        if cap == "noop":
            unmet = sum(sum(max(0.0, v) for v in ts2["rem"].values()) for ts2 in self.task_state if not ts2["done"])
            ratio = unmet / max(1.0, self.initial_demand_sum)
            return - self.cfg.k_timeliness * ratio, {"timeliness": - self.cfg.k_timeliness * ratio}

        r = self.res_state[i]["res"]
        ts = self.task_state[j]
        t  = ts["task"]

        detail = {
            "cover":0.0,
            "scarcity":self.cfg.w_scarcity*self._cap_scarcity(cap),
            "submatch":0.0,"over":0.0,"cost":self.cfg.w_cost*r.cost_per_hour,
            "timeliness":0.0
        }
        if ts["rem"].get(cap,0.0) > 0.0 and r.has_cap(cap):
            detail["cover"] += self.cfg.w_cover * t.priority
            if cap == "act" and self.cfg.use_sub_demands:
                hit = False
                if ts["sub_rem"].get("act_strike",0.0)>0 and r.sub_caps.get("act_strike",0.0)>0:
                    detail["submatch"] += self.cfg.w_submatch; hit = True
                if ts["sub_rem"].get("act_resupply",0.0)>0 and r.sub_caps.get("act_resupply",0.0)>0:
                    detail["submatch"] += self.cfg.w_submatch; hit = True
                if not hit:
                    detail["submatch"] += self.cfg.w_sub_mismatch
        else:
            detail["over"] += self.cfg.w_over

        type_ok = _type_ok_with_whitelist(r.rtype, r.domain, t.type_whitelist)
        detail["type_match"] = (self.cfg.w_type_match if type_ok else self.cfg.w_type_mismatch)

        if t.speed_min_kph>0.0:
            ratio = (float(r.speed_mps)*3.6) / max(1.0, t.speed_min_kph)
            detail["speed_meet"] = (self.cfg.k_speed_excess * min(1.0, ratio)) if ratio>=1.0 \
                                   else (- self.cfg.k_speed_shortfall * (1.0 - ratio))
        else:
            detail["speed_meet"] = 0.0

        unmet = sum(sum(max(0.0, v) for v in ts2["rem"].values()) for ts2 in self.task_state if not ts2["done"])
        ratio = unmet / max(1.0, self.initial_demand_sum)
        detail["timeliness"] = - self.cfg.k_timeliness * ratio

        return float(sum(detail.values())), detail

    # ------------- helpers -------------

    def _check_done(self) -> bool:
        return all(ts["done"] for ts in self.task_state) or all(rs["uses_left"]<=0 for rs in self.res_state)

    def _update_task_done(self, ts: Dict[str,Any]):
        rem = ts["rem"]; sub = ts["sub_rem"]
        done_main = all(v<=0.0 for v in rem.values())
        done_sub  = True
        if self.cfg.use_sub_demands and rem.get("act",0.0)<=0.0:
            done_sub = all(v<=0.0 for v in sub.values())
        ts["done"] = (done_main and done_sub)

    def _cap_scarcity(self, cap: str) -> float:
        need = sum(max(0.0, ts["rem"].get(cap,0.0)) for ts in self.task_state if not ts["done"])
        if need <= 0: return 0.0
        # 仅统计“对任何未完成任务构成合法动作”的资源数量
        supply = 0.0
        for rs in self.res_state:
            if rs["uses_left"]<=0 or rs["remaining_min"]<=0: 
                continue
            r: CanonResource = rs["res"]
            ok_any = False
            for ts in self.task_state:
                if ts["done"]: 
                    continue
                if ts["rem"].get(cap,0.0) <= 0.0: 
                    continue
                if self._action_allowed(r, ts["task"], cap):
                    ok_any = True
                    break
            if ok_any:
                supply += 1.0
        return float(need) / max(1.0, float(supply))

    def _rebuild_legal(self):
        actions = []
        for i, rs in enumerate(self.res_state):
            if rs["uses_left"]<=0 or rs["remaining_min"]<=0:
                continue
            r: CanonResource = rs["res"]
            for j, ts in enumerate(self.task_state):
                if ts["done"]:
                    continue
                t: CanonTask = ts["task"]
                for cap in CAPS:
                    if ts["rem"].get(cap,0.0) <= 0.0:
                        continue
                    if not self._action_allowed(r, t, cap):
                        continue
                    actions.append((i,j,cap))
        actions.append( (-1, -1, "noop") )
        self.legal_actions: List[Tuple[int,int,str]] = actions

    # ---------- action features for DQN ----------

    def action_features(self, actions: List[Tuple[int,int,str]]) -> np.ndarray:
        feats = []

        # 动态确定 noop 的特征长度
        feat_len = None
        for (ii,jj,cc) in actions:
            if cc != "noop":
                r: CanonResource = self.res_state[ii]["res"]
                t: CanonTask     = self.task_state[jj]["task"]
                dom_vec = self._one_hot(self.domain_vocab.index(r.domain), len(self.domain_vocab))
                rtype_vec = self._one_hot(self.rtype_vocab.index(r.rtype), len(self.rtype_vocab)) if r.rtype in self.rtype_vocab else [0.0]*len(self.rtype_vocab)
                r_vec = dom_vec + rtype_vec + [
                    float(r.speed_mps)*3.6/1000.0,
                    float(r.endurance_min)/10000.0,
                    float(r.cost_per_hour)/10.0,
                    float(r.tags.get("strike_capable",0.0)),
                    float(r.tags.get("anti_ship",0.0)),
                    float(r.tags.get("bvr",0.0)),
                    float(r.sub_caps.get("act_strike",0.0)),
                    float(r.sub_caps.get("act_resupply",0.0)),
                ]
                t_dom_vec = self._one_hot(self.domain_vocab.index(t.domain), len(self.domain_vocab))
                t_kind_vec= self._one_hot(self.kind_vocab.index(t.kind) if t.kind in self.kind_vocab else self.kind_vocab.index("generic"), len(self.kind_vocab))
                whitelist_hit = 1.0 if _type_ok_with_whitelist(r.rtype, r.domain, t.type_whitelist) else 0.0
                ts = self.task_state[jj]
                t_vec = t_dom_vec + t_kind_vec + [
                    float(t.priority),
                    float(t.speed_min_kph)/1000.0,
                    float(t.radar_min_km)/1000.0,
                    float(t.min_units)/10.0,
                    float(ts["rem"].get("sense",0.0))/5.0,
                    float(ts["rem"].get("comm",0.0))/5.0,
                    float(ts["rem"].get("act",0.0))/5.0,
                    float(ts["sub_rem"].get("act_strike",0.0))/5.0,
                    float(ts["sub_rem"].get("act_resupply",0.0))/5.0,
                    whitelist_hit,
                ]
                cap_vec = self._one_hot(CAPS.index(cc), len(CAPS))
                feat_len = len(r_vec) + len(t_vec) + len(cap_vec)
                break
        if feat_len is None:
            feat_len = self._feat_dim()

        for (i,j,cap) in actions:
            if cap == "noop":
                feats.append([0.0]*feat_len)
                continue
            r: CanonResource = self.res_state[i]["res"]
            t: CanonTask     = self.task_state[j]["task"]
            dom_vec = self._one_hot(self.domain_vocab.index(r.domain), len(self.domain_vocab))
            rtype_vec = self._one_hot(self.rtype_vocab.index(r.rtype), len(self.rtype_vocab)) if r.rtype in self.rtype_vocab else [0.0]*len(self.rtype_vocab)
            r_vec = dom_vec + rtype_vec + [
                float(r.speed_mps)*3.6/1000.0,
                float(r.endurance_min)/10000.0,
                float(r.cost_per_hour)/10.0,
                float(r.tags.get("strike_capable",0.0)),
                float(r.tags.get("anti_ship",0.0)),
                float(r.tags.get("bvr",0.0)),
                float(r.sub_caps.get("act_strike",0.0)),
                float(r.sub_caps.get("act_resupply",0.0)),
            ]
            kind_idx = self.kind_vocab.index(t.kind) if t.kind in self.kind_vocab else self.kind_vocab.index("generic")
            t_dom_vec = self._one_hot(self.domain_vocab.index(t.domain), len(self.domain_vocab))
            t_kind_vec= self._one_hot(kind_idx, len(self.kind_vocab))
            whitelist_hit = 1.0 if _type_ok_with_whitelist(r.rtype, r.domain, t.type_whitelist) else 0.0
            ts = self.task_state[j]
            t_vec = t_dom_vec + t_kind_vec + [
                float(t.priority),
                float(t.speed_min_kph)/1000.0,
                float(t.radar_min_km)/1000.0,
                float(t.min_units)/10.0,
                float(ts["rem"].get("sense",0.0))/5.0,
                float(ts["rem"].get("comm",0.0))/5.0,
                float(ts["rem"].get("act",0.0))/5.0,
                float(ts["sub_rem"].get("act_strike",0.0))/5.0,
                float(ts["sub_rem"].get("act_resupply",0.0))/5.0,
                whitelist_hit,
            ]
            cap_vec = self._one_hot(CAPS.index(cap), len(CAPS))
            feats.append(r_vec + t_vec + cap_vec)
        return np.asarray(feats, dtype=np.float32)

    def _feat_dim(self) -> int:
        return (
            len(self.domain_vocab) + len(self.rtype_vocab) + 8 +
            len(self.domain_vocab) + len(self.kind_vocab) + 10 +
            len(CAPS)
        )

    @staticmethod
    def _one_hot(idx: int, n: int) -> List[float]:
        v = [0.0]*n
        if 0<=idx<n:
            v[idx]=1.0
        return v