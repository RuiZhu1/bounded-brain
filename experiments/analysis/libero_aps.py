"""Atomic propositions over LIBERO episode traces, from privileged simulator state.

A trace (experiments/colab/README.md, "Trace format") has T policy steps and T+1 snapshots: after reset and
after every step. `aps()` turns one episode into boolean arrays of length T+1, one per atomic proposition; the
monitor reads one label (the set of true propositions) per snapshot.

Object roles come from the task's BDDL goal (`goal_state` in the episode JSON):
  * movers  - objects the task moves: the first argument of an `on`/`in` predicate;
  * targets - objects the goal refers to otherwise (e.g. `plate_1`, or `basket_1` via `basket_1_contain_region`);
  * others  - every other object in the scene.

Thresholds are physical, and were checked against successful in-distribution episodes (pi05_s1000) before use
(see experiments/analysis/README.md). Positions and orientations for `fell`, `tipped` and `disturbed` are measured
from snapshot SETTLE, not from the reset: some scenes start objects in mid-air (e.g. the ketchup bottle in
LIVING_ROOM_SCENE1/2 drops about 0.5 m in the first 3 steps, before the arm can reach anything), and these
propositions are false before SETTLE.
"""

from __future__ import annotations

import json
import os
from typing import Dict, List, Tuple

import numpy as np

SETTLE = 15  # snapshots (0.75 s at 20 Hz): objects some LIBERO scenes place in mid-air drop during the first steps
FALL_DZ_M = -0.30  # an object this far below its start, while not held, fell off its support
TIP_DEG = 60.0  # a non-mover this far from its start orientation, while not held, was knocked over
DISTURB_M = 0.10  # a non-mover displaced this far from its start was disturbed

PROPS = ("touch", "grasp_any", "grasp_mover", "grasp_wrong", "grasp_other", "progress", "done",
         "fell", "tipped", "disturbed")


def load(json_path: str) -> Tuple[dict, Dict[str, np.ndarray]]:
    with open(json_path) as f:
        meta = json.load(f)
    with np.load(json_path[:-5] + ".npz") as z:
        arrays = {k: z[k] for k in z.files if k not in ("model_xml_gz", "sim_state")}
    return meta, arrays


def roles(meta: dict) -> Tuple[List[str], List[str], List[str]]:
    objs = list(meta["objects"])
    preds = [p for p in meta["goal_state"]]
    movers = [o for o in objs if any(p[0] in ("on", "in") and p[1] == o for p in preds)]
    args = {a for p in preds for a in p[1:]}
    targets = [o for o in objs if o not in movers and (o in args or any(a.startswith(o + "_") for a in args))]
    others = [o for o in objs if o not in movers and o not in targets]
    return movers, targets, others


def tilt_deg(q: np.ndarray, q0: np.ndarray) -> np.ndarray:
    """Angle between the body z-axes of orientations q (..., 4, wxyz) and q0."""

    def zaxis(qq: np.ndarray) -> np.ndarray:
        w, x, y, z = qq[..., 0], qq[..., 1], qq[..., 2], qq[..., 3]
        return np.stack([2 * (x * z + w * y), 2 * (y * z - w * x), 1 - 2 * (x * x + y * y)], -1)

    a, b = zaxis(q), zaxis(q0)
    cos = (a * b).sum(-1) / (np.linalg.norm(a, axis=-1) * np.linalg.norm(b, axis=-1) + 1e-9)
    return np.degrees(np.arccos(np.clip(cos, -1.0, 1.0)))


def aps(meta: dict, z: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
    """Boolean array (length T+1) per atomic proposition."""
    objs = list(meta["objects"])
    ix = {o: i for i, o in enumerate(objs)}
    movers, targets, others = roles(meta)
    mi = [ix[o] for o in movers]
    wi = [ix[o] for o in targets + others]  # not to be grasped
    oi = [ix[o] for o in others]
    ni = [ix[o] for o in targets + others]  # non-movers: should stay where they are
    goal = z["goal"].astype(bool)
    grasp = z["grasp"].astype(bool)
    contact = z["contact"].astype(bool)
    pos, quat = z["obj_pos"][:, : len(objs)], z["obj_quat_wxyz"][:, : len(objs)]
    s = goal.shape[0]
    none = np.zeros(s, bool)

    def any_of(arr: np.ndarray, cols: List[int]) -> np.ndarray:
        return arr[:, cols].any(1) if cols else none.copy()

    out = {
        "touch": contact.any(1),
        "grasp_any": grasp.any(1),
        "grasp_mover": any_of(grasp, mi),
        "grasp_wrong": any_of(grasp, wi),
        "grasp_other": any_of(grasp, oi),
        "progress": (goal & ~goal[:1]).any(1),  # a goal predicate that was false at the start holds now
        "done": goal.all(1),
    }
    held = grasp
    ref = min(SETTLE, s - 1)
    dz = pos[:, :, 2] - pos[ref : ref + 1, :, 2]
    out["fell"] = ((dz < FALL_DZ_M) & ~held).any(1)
    if ni:
        disp = np.linalg.norm(pos[:, ni] - pos[ref : ref + 1, ni], axis=2)
        tilt = tilt_deg(quat[:, ni], quat[ref : ref + 1, ni])
        out["disturbed"] = (disp > DISTURB_M).any(1)
        out["tipped"] = ((tilt > TIP_DEG) & ~held[:, ni]).any(1)
    else:
        out["disturbed"], out["tipped"] = none.copy(), none.copy()
    for name in ("fell", "disturbed", "tipped"):
        out[name][:ref] = False
    return out


def episode_paths(root: str) -> List[str]:
    """All trace JSON files under <root>/traces, sorted."""
    paths = []
    for dirpath, _, files in os.walk(os.path.join(root, "traces")):
        paths += [os.path.join(dirpath, f) for f in files if f.endswith(".json")]
    return sorted(paths)


def first_true(a: np.ndarray) -> int:
    """Index of the first True, or -1."""
    return int(np.argmax(a)) if a.any() else -1
