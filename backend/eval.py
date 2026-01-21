# -*- coding: utf-8 -*-
"""
eval.py
-------
评估期可以用 DQN（默认）或贪心；只输出 per_task_named + reward（含分项 components）。
"""

from __future__ import annotations
import argparse, json
from pathlib import Path
from adapters import scan_task_files, scan_resource_files, load_tasks, load_resources
from env import ResourceTaskEnv, EnvConfig
from dqn import DQNAgent, DQNConfig

def build_names(env: ResourceTaskEnv):
    task_names = [ts["task"].name for ts in env.task_state]
    res_names  = [rs["res"].name  for rs in env.res_state]
    return task_names, res_names

def choose_action_greedy(env: ResourceTaskEnv) -> int:
    n = env.action_space_n()
    if n <= 1:  # only noop
        return 0
    scores = []
    for a in range(n):
        total, _ = env.simulate_step_reward_detail(a)
        scores.append(total)
    return int(max(range(n), key=lambda i: scores[i]))

def eval_run(
    task_dir: str = "Task",
    resource_dir: str = "Resource",
    policy: str = "dqn",
    checkpoint: str = "outputs/dqn.pt",
    out_path: str | None = None,
    # ---- P1 评估期同样可透传 ----
    clamp_sea_speed: bool = True,
    enforce_speed_threshold: bool | None = None,
    k_speed_shortfall: float | None = None,
) -> dict:
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

    _ = env.reset()
    task_names, res_names = build_names(env)

    agent = None
    local_policy = policy
    if local_policy == "dqn":
        obs_dim = env.observe().shape[0]
        actions_now = list(env.legal_actions)
        af_now = env.action_features(actions_now)
        agent = DQNAgent(DQNConfig(obs_dim=obs_dim, act_feat_dim=af_now.shape[-1]))
        if Path(checkpoint).exists():
            agent.load(checkpoint)
        else:
            print(f"[warn] checkpoint not found: {checkpoint}, fallback to greedy")
            local_policy = "greedy"

    per_task_named = {tn: [] for tn in task_names}
    components_sum = {}
    total_reward = 0.0

    obs = env.reset()
    while True:
        n = env.action_space_n()
        if n <= 1:
            break

        if local_policy == "dqn":
            actions_now = list(env.legal_actions)
            af_now = env.action_features(actions_now)
            a = agent.act(obs, actions_now, af_now, epsilon=0.0)
        else:
            a = choose_action_greedy(env)

        i, j, cap = env.legal_actions[a]
        next_obs, r, done, info = env.step(a)
        total_reward += r

        if cap != "noop":
            rname = res_names[i]; tname = task_names[j]
            per_task_named.setdefault(tname, []).append({"resource_name": rname, "capability": cap})

        detail = info.get("reward_detail", {}) or {}
        for k, v in detail.items():
            components_sum[k] = float(components_sum.get(k, 0.0) + float(v))

        obs = next_obs
        if done:
            break

    out = {
        "per_task_named": per_task_named,
        "reward": {
            "total": float(total_reward),
            "components": {k: float(v) for k, v in components_sum.items()}
        }
    }
    if out_path:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print(json.dumps(out, ensure_ascii=False, indent=2))
        print(f"\n[eval] wrote: {out_path}")
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task-dir", type=str, default="Task")
    ap.add_argument("--resource-dir", type=str, default="Resource")
    ap.add_argument("--policy", type=str, default="dqn", choices=["dqn","greedy"])
    ap.add_argument("--checkpoint", type=str, default="outputs/dqn.pt")
    ap.add_argument("--out", type=str, default="outputs/result_eval.json")
    # ---- P1 控制项 ----
    ap.add_argument("--clamp-sea-speed", type=int, default=1)
    ap.add_argument("--enforce-speed-threshold", type=int, default=-1)
    ap.add_argument("--k-speed-shortfall", type=float, default=-1.0)
    args = ap.parse_args()

    enforce_speed_threshold = None
    if args.enforce_speed_threshold in (0,1):
        enforce_speed_threshold = bool(args.enforce_speed_threshold)
    k_speed_shortfall = None
    if args.k_speed_shortfall > 0:
        k_speed_shortfall = float(args.k_speed_shortfall)

    eval_run(
        task_dir=args.task_dir,
        resource_dir=args.resource_dir,
        policy=args.policy,
        checkpoint=args.checkpoint,
        out_path=args.out,
        clamp_sea_speed=bool(args.clamp_sea_speed),
        enforce_speed_threshold=enforce_speed_threshold,
        k_speed_shortfall=k_speed_shortfall,
    )

if __name__ == "__main__":
    main()

