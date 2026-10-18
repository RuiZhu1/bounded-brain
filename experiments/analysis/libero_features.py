"""Per-episode features and failure categories for the LIBERO traces.

    python experiments/analysis/libero_features.py [DATA_ROOT]

DATA_ROOT defaults to data/libero_runs (the unzipped bb_traces_export.zip). Writes
data/analysis/features.csv (one row per episode; data/ is git-ignored) and prints the category counts.

Failure categories (failed episodes only; first match wins):
  object tasks (the goal moves at least one object)
    never_touched     - the gripper never touched any object
    touched_no_grasp  - touched, never grasped anything
    wrong_object      - grasped only objects the task does not move
    mover_not_placed  - grasped an object to move, no goal predicate ever newly true
    partial_goal      - some goal predicate became true, never all at once
  fixture-only tasks (open/close/turn on/turn off)
    no_progress       - no goal predicate ever newly true
    partial_goal      - as above
  any task
    done_not_counted  - all goal predicates held at some snapshot, yet the episode failed (should not occur)
"""

from __future__ import annotations

import csv
import os
import sys
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import libero_aps as L  # noqa: E402

FIELDS = ["episode_id", "group", "run_tag", "suite", "task_id", "task_name", "language", "init", "seed",
          "partial_attempt", "success", "n_steps", "success_step", "max_steps", "task_kind", "n_goal",
          "n_movers", "n_targets", "n_others", "first_touch", "first_grasp_any", "first_grasp_mover",
          "first_grasp_wrong", "first_grasp_other", "first_progress", "first_done", "first_fell",
          "first_tipped", "first_disturbed", "goal_max_frac", "goal_final_frac", "grasp_events",
          "mover_grasp_events", "gripper_toggles", "eef_path_m", "idle_max_steps", "category"]


def group_of(tag: str) -> str:
    if tag.startswith("smoke_"):
        return "smoke"
    if "ood90" in tag:
        return "ood90"
    if "randinit" in tag:
        return "randinit"
    return "reproduction"


def rising(a: np.ndarray) -> int:
    return int((a[1:] & ~a[:-1]).sum() + a[0])


def category(row: dict, ap: dict) -> str:
    if row["success"]:
        return "success"
    if ap["done"].any():
        return "done_not_counted"
    if row["task_kind"] == "object":
        if not ap["touch"].any():
            return "never_touched"
        if not ap["grasp_any"].any():
            return "touched_no_grasp"
        if not ap["grasp_mover"].any():
            return "wrong_object"
        if not ap["progress"].any():
            return "mover_not_placed"
        return "partial_goal"
    return "partial_goal" if ap["progress"].any() else "no_progress"


def features(path: str) -> dict:
    meta, z = L.load(path)
    ap = L.aps(meta, z)
    movers, targets, others = L.roles(meta)
    goal = z["goal"].astype(bool)
    eef = z["eef_pos"]
    step = np.linalg.norm(np.diff(eef, axis=0), axis=1)
    idle = step < 1e-3
    longest = run = 0
    for v in idle:
        run = run + 1 if v else 0
        longest = max(longest, run)
    grip = np.sign(z["actions"][:, 6])
    rel = path.split(os.sep + "traces" + os.sep, 1)[1]
    row = {
        "episode_id": meta["episode_id"],
        "group": group_of(meta["run_tag"]),
        "run_tag": meta["run_tag"],
        "suite": meta["suite"],
        "task_id": meta["task_id"],
        "task_name": meta["task_name"],
        "language": meta["language"],
        "init": "random" if meta["init_state_id"] in (None, -1) or "randinit" in meta["run_tag"] else "fixed",
        "seed": meta["seed"],
        "partial_attempt": "__partial_" in rel,
        "success": bool(meta["success"]),
        "n_steps": meta["n_steps"],
        "success_step": meta["success_step"] if meta["success_step"] is not None else -1,
        "max_steps": meta["max_episode_steps"],
        "task_kind": "object" if movers else "fixture",
        "n_goal": goal.shape[1],
        "n_movers": len(movers),
        "n_targets": len(targets),
        "n_others": len(others),
        "goal_max_frac": round(float(goal.sum(1).max()) / goal.shape[1], 3),
        "goal_final_frac": round(float(goal[-1].sum()) / goal.shape[1], 3),
        "grasp_events": rising(ap["grasp_any"]),
        "mover_grasp_events": rising(ap["grasp_mover"]),
        "gripper_toggles": int((grip[1:] != grip[:-1]).sum()),
        "eef_path_m": round(float(step.sum()), 3),
        "idle_max_steps": longest,
    }
    for name in ("touch", "grasp_any", "grasp_mover", "grasp_wrong", "grasp_other", "progress", "done",
                 "fell", "tipped", "disturbed"):
        row["first_" + name] = L.first_true(ap[name])
    row["category"] = category(row, ap)
    return row


def main() -> None:
    repo = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.join(repo, "data", "libero_runs")
    out_dir = os.path.join(repo, "data", "analysis")
    os.makedirs(out_dir, exist_ok=True)
    paths = L.episode_paths(root)
    with Pool(max(1, (os.cpu_count() or 2) - 1)) as pool:
        rows = pool.map(features, paths, chunksize=16)
    with open(os.path.join(out_dir, "features.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} episodes -> {os.path.join(out_dir, 'features.csv')}")
    groups = ["reproduction", "randinit", "ood90"]
    cats = sorted({r["category"] for r in rows if r["group"] in groups})
    print(f"{'category':18s}" + "".join(f"{g:>14s}" for g in groups))
    for c in cats:
        print(f"{c:18s}" + "".join(f"{sum(r['category'] == c and r['group'] == g for r in rows):14d}" for g in groups))


if __name__ == "__main__":
    main()
