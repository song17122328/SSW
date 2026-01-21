# -*- coding: utf-8 -*-
"""
train.py
--------
训练 DQN；支持 episode 级别的 trace（默认）或 step 级别（可选），
并把每个 episode 的最终 per_task_named 与 reward 分项写入 JSONL。
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from collections import defaultdict

from adapters import scan_task_files, scan_resource_files, load_tasks, load_resources
from env import ResourceTaskEnv, EnvConfig
from dqn import DQNAgent, DQNConfig


def build_names(env: ResourceTaskEnv):
    task_names = [ts["task"].name for ts in env.task_state]
    res_names = [rs["res"].name for rs in env.res_state]
    return task_names, res_names


def train_stream(
    task_dir: str = "Task",
    resource_dir: str = "Resource",
    episodes: int = 50,
    steps_per_ep: int = 128,
    epsilon: float = 0.3,
    epsilon_decay: float = 0.995,
    checkpoint: str = "outputs/dqn.pt",
    trace_out: str | None = None,
    trace_mode: str = "episode",      # "episode" | "step"
    callback=None,                    # callable(dict)
    stop_event=None,                  # threading.Event
    # ----- P1 参数透传 -----
    clamp_sea_speed: bool = True,
    enforce_speed_threshold: bool | None = None,
    k_speed_shortfall: float | None = None,
    # ----- P2 超参覆写 -----
    dqn_overrides: dict | None = None,
):
    """
    与 main() 同步的训练过程，但将每条 trace 通过 callback(rec) 发出。
    返回：{"episodes": N, "last_epsilon": ..., "checkpoint": "..."} 作为简单统计。
    """
    # ---- data & env ----
    task_files = scan_task_files(Path(task_dir))
    air_json, ship_json = scan_resource_files(Path(resource_dir))
    tasks = load_tasks(task_files, clamp_sea_speed=clamp_sea_speed)
    resources = load_resources(air_json, ship_json)

    cfg = EnvConfig()
    if enforce_speed_threshold is not None:
        cfg.enforce_speed_threshold = bool(enforce_speed_threshold)
    if k_speed_shortfall is not None:
        cfg.k_speed_shortfall = float(k_speed_shortfall)
    env = ResourceTaskEnv(tasks, resources, cfg=cfg)

    obs_dim = env.observe().shape[0]
    af0 = env.action_features(list(env.legal_actions))
    dcfg = DQNConfig(obs_dim=obs_dim, act_feat_dim=af0.shape[-1])
    if dqn_overrides:
        for k, v in dqn_overrides.items():
            if hasattr(dcfg, k):
                setattr(dcfg, k, v)
    agent = DQNAgent(dcfg)

    _ = env.reset()
    task_names, res_names = build_names(env)

    fout = None
    if trace_out:
        Path(trace_out).parent.mkdir(parents=True, exist_ok=True)
        fout = open(Path(trace_out), "w", encoding="utf-8")

    eps = epsilon
    for ep in range(episodes):
        if stop_event is not None and stop_event.is_set():
            break

        obs = env.reset(seed=ep)
        ep_reward = 0.0
        per_task_named_final = {tn: [] for tn in task_names}
        from collections import defaultdict as _dd
        comp_sum = _dd(float)

        for step in range(steps_per_ep):
            if stop_event is not None and stop_event.is_set():
                break

            actions_now = list(env.legal_actions)
            if len(actions_now) == 0:
                break
            af_now = env.action_features(actions_now)
            a = agent.act(obs, actions_now, af_now, epsilon=eps)

            i, j, cap = actions_now[a]
            next_obs, r, done, info = env.step(a)
            ep_reward += r

            # 奖励分量累加
            rd = info.get("reward_detail", {})
            for k, v in rd.items():
                comp_sum[k] += float(v)

            # 训练一步
            actions_next = list(env.legal_actions)
            af_next = env.action_features(actions_next)
            agent.train_step(
                obs=obs, action_index=a, reward=r, next_obs=next_obs, done=done,
                actions_now=actions_now, actions_next=actions_next,
                action_feats_now=af_now, action_feats_next=af_next,
            )
            obs = next_obs

            # episode 末尾合并（保持与原 trace 一致）
            if cap != "noop":
                rname = res_names[i]
                tname = task_names[j]
                per_task_named_final.setdefault(tname, []).append({
                    "resource_name": rname, "capability": cap
                })

            # 若需要 step 级回传
            if trace_mode == "step":
                rec_step = {
                    "episode": ep,
                    "step": step,
                    "action_named": None if cap == "noop" else {
                        "resource_name": rname, "task_name": tname, "capability": cap
                    },
                    "reward_detail": rd,
                    "ep_reward_so_far": float(ep_reward),
                }
                if fout:
                    fout.write(json.dumps(rec_step, ensure_ascii=False) + "\n")
                if callback:
                    callback(rec_step)

            if done:
                break

        rec_ep = {
            "episode": ep,
            "steps": env.steps,
            "reward": {"total": float(ep_reward), "components": dict(comp_sum)},
            "per_task_named": per_task_named_final,
        }
        if fout:
            fout.write(json.dumps(rec_ep, ensure_ascii=False) + "\n")
        if callback:
            callback(rec_ep)

        eps = max(0.05, eps * epsilon_decay)

    if fout:
        fout.close()

    # ---- 规范化并创建最终 checkpoint 文件路径（目录或无扩展名 -> 目录/dqn.pt） ----
    ckpt_path = Path(checkpoint)
    is_dirish = (ckpt_path.suffix == "") or str(ckpt_path).endswith(("/", "\\")) or (ckpt_path.exists() and ckpt_path.is_dir())
    if is_dirish:
        ckpt_path.mkdir(parents=True, exist_ok=True)       # 创建目录本体（如 jobs\_-3_0295_d97bc1）
        ckpt_path = ckpt_path / "dqn.pt"
    else:
        ckpt_path.parent.mkdir(parents=True, exist_ok=True)

    agent.save(str(ckpt_path))

    return {
        "episodes": episodes,
        "last_epsilon": float(eps),
        "checkpoint": str(ckpt_path),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task-dir", type=str, default="Task")
    ap.add_argument("--resource-dir", type=str, default="Resource")
    ap.add_argument("--episodes", type=int, default=50)
    ap.add_argument("--steps-per-ep", type=int, default=128)
    ap.add_argument("--epsilon", type=float, default=0.3)
    ap.add_argument("--epsilon-decay", type=float, default=0.995)
    ap.add_argument("--checkpoint", type=str, default="outputs/dqn.pt")
    ap.add_argument("--trace-out", type=str, default="outputs/train_trace.jsonl")
    ap.add_argument("--trace-mode", type=str, choices=["episode", "step"], default="episode")
    # ---- P1 控制项 ----
    ap.add_argument("--clamp-sea-speed", type=int, default=1, help="1=钳制海域速度阈值至60km/h, 0=不钳制")
    ap.add_argument("--enforce-speed-threshold", type=int, default=-1, help="1=硬约束,0=软约束,-1=保持默认")
    ap.add_argument("--k-speed-shortfall", type=float, default=-1.0, help=">0 则覆盖速度不足惩罚系数")
    # ---- P2 覆写项 ----
    ap.add_argument("--buffer-size", type=int, default=-1)
    ap.add_argument("--batch-size", type=int, default=-1)
    ap.add_argument("--warmup-steps", type=int, default=-1)
    ap.add_argument("--updates-per-env-step", type=int, default=-1)
    ap.add_argument("--target-update-interval", type=int, default=-1)
    args = ap.parse_args()

    dqn_overrides = {}
    if args.buffer_size > 0:
        dqn_overrides["buffer_size"] = args.buffer_size
    if args.batch_size > 0:
        dqn_overrides["batch_size"] = args.batch_size
    if args.warmup_steps > 0:
        dqn_overrides["warmup_steps"] = args.warmup_steps
    if args.updates_per_env_step > 0:
        dqn_overrides["updates_per_env_step"] = args.updates_per_env_step
    if args.target_update_interval > 0:
        dqn_overrides["target_update_interval"] = args.target_update_interval

    enforce_speed_threshold = None
    if args.enforce_speed_threshold in (0, 1):
        enforce_speed_threshold = bool(args.enforce_speed_threshold)
    k_speed_shortfall = None
    if args.k_speed_shortfall > 0:
        k_speed_shortfall = float(args.k_speed_shortfall)

    stats = train_stream(
        task_dir=args.task_dir,
        resource_dir=args.resource_dir,
        episodes=args.episodes,
        steps_per_ep=args.steps_per_ep,
        epsilon=args.epsilon,
        epsilon_decay=args.epsilon_decay,
        checkpoint=args.checkpoint,
        trace_out=args.trace_out,
        trace_mode=args.trace_mode,
        callback=None,
        stop_event=None,
        clamp_sea_speed=bool(args.clamp_sea_speed),
        enforce_speed_threshold=enforce_speed_threshold,
        k_speed_shortfall=k_speed_shortfall,
        dqn_overrides=(dqn_overrides or None),
    )
    print(f"[train] saved checkpoint to {stats['checkpoint']}")
    if args.trace_out:
        print(f"[train] wrote trace to {args.trace_out}")


if __name__ == "__main__":
    main()
