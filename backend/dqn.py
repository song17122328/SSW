# -*- coding: utf-8 -*-
"""
dqn.py
- Action-conditional Q network: Q(s, a_feat) via (obs MLP ⊕ action MLP).
- GPU if available. Robust save()/load() with dir-or-file path handling and atomic replace.
- 增强：Replay Buffer + 固定步长目标网络硬更新（P2-6）
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from collections import deque
import random

Action = Tuple[int, int, str]  # (resource_idx, task_idx, cap)


@dataclass
class DQNConfig:
    obs_dim: int
    act_feat_dim: int = 64  # will be set dynamically at first call if 0
    hidden: int = 256
    lr: float = 1e-3
    gamma: float = 0.99
    # ---- Replay & Target ----
    buffer_size: int = 50000
    batch_size: int = 1                 # 由于动作集合 A 变长，这里默认逐条样本更新
    warmup_steps: int = 1000
    updates_per_env_step: int = 1
    target_update_interval: int = 1000  # 每多少个梯度更新同步目标网络


class QNet(nn.Module):
    def __init__(self, obs_dim: int, act_dim: int, hidden: int):
        super().__init__()
        self.obs_mlp = nn.Sequential(
            nn.Linear(obs_dim, hidden),
            nn.ReLU(),
            nn.Linear(hidden, hidden),
            nn.ReLU(),
        )
        self.act_mlp = nn.Sequential(
            nn.Linear(act_dim, hidden // 2),
            nn.ReLU(),
            nn.Linear(hidden // 2, hidden // 2),
            nn.ReLU(),
        )
        self.head = nn.Sequential(
            nn.Linear(hidden + hidden // 2, hidden),
            nn.ReLU(),
            nn.Linear(hidden, 1),
        )

    def forward(self, obs: torch.Tensor, action_feats: torch.Tensor) -> torch.Tensor:
        """
        obs: (B, obs_dim)
        action_feats: (B, A, act_dim)
        return: (B, A)
        """
        B, A, F = action_feats.shape
        h_obs = self.obs_mlp(obs)                        # (B,H)
        h_act = self.act_mlp(action_feats.view(B * A, F))  # (B*A, H/2)
        h_obs_tiled = h_obs.unsqueeze(1).repeat(1, A, 1).view(B * A, -1)  # (B*A, H)
        q = self.head(torch.cat([h_obs_tiled, h_act], dim=1))             # (B*A,1)
        return q.view(B, A)


class ReplayBuffer:
    def __init__(self, capacity: int):
        self.buf = deque(maxlen=capacity)

    def push(self, tr: Dict[str, Any]):
        self.buf.append(tr)

    def __len__(self):
        return len(self.buf)

    def sample(self, batch_size: int) -> List[Dict[str, Any]]:
        k = min(batch_size, len(self.buf))
        return random.sample(self.buf, k=k)


class DQNAgent:
    def __init__(self, cfg: DQNConfig):
        self.cfg = cfg
        self.obs_dim = cfg.obs_dim
        self.act_dim = cfg.act_feat_dim if cfg.act_feat_dim > 0 else 64  # placeholder; will be reset on first call
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # lazy init when we know act_dim
        self.q: Optional[QNet] = None
        self.tgt: Optional[QNet] = None
        self.optim: Optional[optim.Optimizer] = None

        # replay & step counters
        self.replay = ReplayBuffer(cfg.buffer_size)
        self.total_updates = 0

    def _ensure_net(self, act_dim: int):
        if (self.q is None) or (self.act_dim != act_dim):
            self.act_dim = act_dim
            self.q = QNet(self.obs_dim, self.act_dim, self.cfg.hidden).to(self.device)
            self.tgt = QNet(self.obs_dim, self.act_dim, self.cfg.hidden).to(self.device)
            self.tgt.load_state_dict(self.q.state_dict())
            self.optim = optim.Adam(self.q.parameters(), lr=self.cfg.lr)

    @torch.no_grad()
    def act(self, obs: np.ndarray, actions_now: List[Action], action_feats_now: np.ndarray, epsilon: float = 0.1) -> int:
        A = len(actions_now)
        if A == 0:
            return 0
        self._ensure_net(action_feats_now.shape[-1])
        if np.random.rand() < epsilon:
            return int(np.random.randint(0, A))
        x = torch.from_numpy(obs).float().unsqueeze(0).to(self.device)                # (1,D)
        af = torch.from_numpy(action_feats_now).float().unsqueeze(0).to(self.device)  # (1,A,F)
        q = self.q(x, af)  # (1,A)
        a = int(torch.argmax(q, dim=1).item())
        return a

    def _td_update_once(self, tr: Dict[str, Any]) -> float:
        """对单个 transition 计算 TD 目标并反向。"""
        obs = tr["obs"]
        next_obs = tr["next_obs"]
        done = bool(tr["done"])
        aidx = int(tr["action_index"])
        r = float(tr["reward"])
        af_now = tr["af_now"]
        af_next = tr["af_next"]

        x = torch.from_numpy(obs).float().unsqueeze(0).to(self.device)
        afn = torch.from_numpy(af_now).float().unsqueeze(0).to(self.device)
        q_now = self.q(x, afn)  # (1,A_now)

        # 更严谨的索引兜底（防止负数或超界）
        A_now = q_now.shape[1]
        aidx = max(0, min(aidx, A_now - 1))
        q_sa = q_now[0, aidx].unsqueeze(0)  # (1,)

        with torch.no_grad():
            x2 = torch.from_numpy(next_obs).float().unsqueeze(0).to(self.device)  # (1,D)
            if af_next is not None and len(af_next) > 0:
                af2 = torch.from_numpy(af_next).float().unsqueeze(0).to(self.device)  # (1,A2,F)
                q_next_online = self.q(x2, af2)  # (1,A2)
                a_star = torch.argmax(q_next_online, dim=1)  # (1,)
                q_next_tgt = self.tgt(x2, af2)  # (1,A2)
                q_next = q_next_tgt.gather(1, a_star.unsqueeze(1)).squeeze(1)  # (1,)
            else:
                q_next = torch.zeros(1, dtype=torch.float32, device=self.device)  # (1,)
            target = torch.tensor([r], dtype=torch.float32, device=self.device)
            if not done:
                target = target + self.cfg.gamma * q_next

        loss = torch.nn.functional.smooth_l1_loss(q_sa, target)
        assert self.optim is not None
        self.optim.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.q.parameters(), 5.0)
        self.optim.step()
        return float(loss.item())

    def train_step(
        self,
        obs: np.ndarray,
        action_index: int,
        reward: float,
        next_obs: np.ndarray,
        done: bool,
        actions_now: List[Action],
        actions_next: List[Action],
        action_feats_now: np.ndarray,
        action_feats_next: np.ndarray,
    ) -> float:
        self._ensure_net(action_feats_now.shape[-1])

        # 存入回放
        tr = {
            "obs": obs,
            "action_index": int(action_index),
            "reward": float(reward),
            "next_obs": next_obs,
            "done": bool(done),
            "af_now": action_feats_now,
            "af_next": action_feats_next,
        }
        self.replay.push(tr)

        last_loss = 0.0
        # warmup 后进行学习；否则可做一次 on-policy 更新
        if len(self.replay) >= self.cfg.warmup_steps:
            updates = max(1, int(self.cfg.updates_per_env_step))
            for _ in range(updates):
                batch = self.replay.sample(self.cfg.batch_size)
                # 由于动作集合维度 A 变长，逐条处理更稳妥
                for b in batch:
                    last_loss = self._td_update_once(b)
                    self.total_updates += 1
                    if (self.total_updates % self.cfg.target_update_interval) == 0:
                        # 硬同步目标网络
                        self.tgt.load_state_dict(self.q.state_dict())
        else:
            last_loss = self._td_update_once(tr)

        return last_loss

    # ---------- IO ----------
    def save(self, path: str):
        """
        支持传入“目录路径”或“文件路径”；若是目录或无扩展名，则落到 <path>/dqn.pt。
        使用临时文件 + 原子替换，提升并发/清理场景鲁棒性。
        """
        if self.q is None:
            return

        p = Path(path)
        # 将“目录或无扩展名或显式以分隔符结尾”的情况统一当作目录处理
        is_dirish = (p.suffix == "") or str(p).endswith(("/", "\\")) or (p.exists() and p.is_dir())
        if is_dirish:
            p = p / "dqn.pt"

        # 确保最终“文件路径”的父目录存在
        p.parent.mkdir(parents=True, exist_ok=True)

        ckpt = {
            "obs_dim": self.obs_dim,
            "act_dim": self.act_dim,
            "state_dict": self.q.state_dict(),
            "tgt_state_dict": self.tgt.state_dict() if self.tgt is not None else None,
            "cfg": self.cfg.__dict__,
        }

        # 原子写入：先写临时文件，再替换
        tmp = p.with_suffix(p.suffix + ".tmp")  # e.g., dqn.pt.tmp
        torch.save(ckpt, str(tmp))
        tmp.replace(p)

    def load(self, path: str):
        """
        支持目录或文件路径；若给的是目录则尝试 <dir>/dqn.pt。
        兼容旧 ckpt 没有 tgt_state_dict 的情况。
        """
        p = Path(path)
        is_dirish = (p.suffix == "") or str(p).endswith(("/", "\\")) or (p.exists() and p.is_dir())
        if is_dirish:
            p = p / "dqn.pt"

        ckpt = torch.load(str(p), map_location=self.device)
        self.obs_dim = int(ckpt.get("obs_dim", self.obs_dim))
        act_dim = int(ckpt.get("act_dim", self.act_dim))
        self._ensure_net(act_dim)
        self.q.load_state_dict(ckpt["state_dict"])

        tgt_sd = ckpt.get("tgt_state_dict", None)
        if tgt_sd is None:
            # 兼容老模型：若无目标网络权重，则拷贝在线网络
            self.tgt.load_state_dict(self.q.state_dict())
        else:
            self.tgt.load_state_dict(tgt_sd)
