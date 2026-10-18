"""bounded-brain trace logger for LeRobot LIBERO evaluations.

Importing this module monkeypatches ``lerobot.envs.libero.LiberoEnv`` so that every
episode run by ``lerobot-eval`` is also saved with privileged simulator information,
which the bounded-brain monitor needs as ground-truth labels:

* the MuJoCo simulator state at every step (enough to replay the episode exactly
  and recompute any predicate offline),
* end-effector pose and gripper joint positions,
* positions and orientations of every object and fixture,
* truth values of the task's BDDL goal predicates,
* per-object "grasped" and "gripper in contact" flags.

One ``<episode_id>.npz`` (arrays) and one ``<episode_id>.json`` (metadata) are written
per episode under ``$BB_TRACE_DIR/<suite>/task_<id>/``. Logging failures never stop
the evaluation; they are counted and reported in the metadata.

Written against lerobot==0.6.1 and hf-libero==0.1.4 (their source was read on
2026-10-17). Other versions may rename the internals used here; a warning is printed.
"""

from __future__ import annotations

import atexit
import gzip
import json
import os
import time
import uuid
import weakref
from importlib import metadata

import numpy as np

from lerobot.envs import libero as _libero

TESTED_VERSIONS = {"lerobot": "0.6.1", "hf-libero": "0.1.4"}
TRACE_DIR = os.environ.get("BB_TRACE_DIR", os.path.abspath("bb_traces"))
RUN_TAG = os.environ.get("BB_RUN_TAG", "run")
POLICY = os.environ.get("BB_POLICY", "unknown")
FORMAT_VERSION = 1


def _version(pkg: str) -> str:
    try:
        return metadata.version(pkg)
    except metadata.PackageNotFoundError:
        return "missing"


VERSIONS = {pkg: _version(pkg) for pkg in TESTED_VERSIONS}
for _pkg, _tested in TESTED_VERSIONS.items():
    if VERSIONS[_pkg] != _tested:
        print(f"[bb_trace] WARNING: {_pkg}=={VERSIONS[_pkg]} (tested with {_tested}); internals may differ.")

_LiberoEnv = _libero.LiberoEnv
_orig_ensure_env = _LiberoEnv._ensure_env
_orig_reset = _LiberoEnv.reset
_orig_step = _LiberoEnv.step
_orig_close = _LiberoEnv.close
_live = weakref.WeakSet()


def _suite_name(env) -> str:
    # The BDDL file lives in .../bddl_files/<suite>/<task>.bddl
    return os.path.basename(os.path.dirname(env._task_bddl_file))


def _wrap_capture(env, control_env) -> None:
    """Remember the last raw observation dict returned by the LIBERO control env."""

    def capture(fn):
        def wrapped(*args, **kwargs):
            out = fn(*args, **kwargs)
            raw = out[0] if isinstance(out, tuple) else out
            if isinstance(raw, dict):
                env._bb_raw = raw
            return out

        return wrapped

    for name in ("step", "reset", "set_init_state"):
        if hasattr(control_env, name):
            setattr(control_env, name, capture(getattr(control_env, name)))


def _ensure_env(self) -> None:
    fresh = self._env is None
    _orig_ensure_env(self)
    if fresh and self._env is not None:
        _wrap_capture(self, self._env)
        inner = self._env.env
        self._bb_objects = list(inner.objects_dict.keys())
        self._bb_fixtures = list(inner.fixtures_dict.keys())
        self._bb_goal = [list(map(str, g)) for g in inner.parsed_problem.get("goal_state", [])]
        _live.add(self)


def _note_error(self, where: str, exc: Exception) -> None:
    errs = self._bb_buf.setdefault("errors", {})
    if where not in errs:
        errs[where] = f"{type(exc).__name__}: {exc}"
    self._bb_buf["n_errors"] = self._bb_buf.get("n_errors", 0) + 1


def _vec(raw, key: str, n: int) -> np.ndarray:
    val = raw.get(key) if isinstance(raw, dict) else None
    return np.asarray(val, dtype=np.float32).reshape(n) if val is not None else np.full(n, np.nan, np.float32)


def _snapshot(self) -> dict:
    snap: dict = {}
    control = self._env
    inner = control.env
    try:
        snap["sim_state"] = np.asarray(control.get_sim_state(), dtype=np.float64).copy()
    except Exception as exc:  # noqa: BLE001
        _note_error(self, "sim_state", exc)
        snap["sim_state"] = None
    raw = getattr(self, "_bb_raw", None)
    snap["eef_pos"] = _vec(raw, "robot0_eef_pos", 3)
    snap["eef_quat"] = _vec(raw, "robot0_eef_quat", 4)
    snap["gripper_qpos"] = _vec(raw, "robot0_gripper_qpos", 2)
    names = self._bb_objects + self._bb_fixtures
    try:
        ids = [inner.obj_body_id[n] for n in names]
        snap["obj_pos"] = np.array(inner.sim.data.body_xpos[ids], dtype=np.float32)
        snap["obj_quat_wxyz"] = np.array(inner.sim.data.body_xquat[ids], dtype=np.float32)
    except Exception as exc:  # noqa: BLE001
        _note_error(self, "obj_pose", exc)
        snap["obj_pos"] = np.full((len(names), 3), np.nan, np.float32)
        snap["obj_quat_wxyz"] = np.full((len(names), 4), np.nan, np.float32)
    goal = []
    for g in self._bb_goal:
        try:
            goal.append(bool(inner._eval_predicate(g)))
        except Exception as exc:  # noqa: BLE001
            _note_error(self, "goal_predicate", exc)
            goal.append(False)
    snap["goal"] = np.array(goal, dtype=bool)
    grasp, contact = [], []
    try:
        gripper = inner.robots[0].gripper
    except Exception as exc:  # noqa: BLE001
        _note_error(self, "gripper", exc)
        gripper = None
    for n in self._bb_objects:
        g = c = False
        if gripper is not None:
            try:
                g = bool(inner._check_grasp(gripper=gripper, object_geoms=inner.objects_dict[n]))
            except Exception as exc:  # noqa: BLE001
                _note_error(self, "grasp", exc)
            try:
                c = bool(inner.check_contact(gripper, inner.objects_dict[n]))
            except Exception as exc:  # noqa: BLE001
                _note_error(self, "contact", exc)
        grasp.append(g)
        contact.append(c)
    snap["grasp"] = np.array(grasp, dtype=bool)
    snap["contact"] = np.array(contact, dtype=bool)
    return snap


def _start(self, seed, init_id) -> None:
    self._bb_buf = {
        "t0": time.time(),
        "seed": None if seed is None else int(seed),
        "init_state_id": init_id,
        "actions": [],
        "rewards": [],
        "success": [],
        "snaps": [],
        "model_xml_gz": None,
    }
    try:
        # Exact offline replay needs more than the sim state: the episode's model XML,
        # and the fixture placements that LIBERO writes into model.body_pos/body_quat
        # at reset time (bddl_base_domain.py), which the XML does not contain.
        inner = self._env.env
        self._bb_buf["model_xml_gz"] = gzip.compress(inner.model.get_xml().encode("utf-8"))
        self._bb_buf["model_body_pos"] = np.array(inner.sim.model.body_pos, dtype=np.float64)
        self._bb_buf["model_body_quat"] = np.array(inner.sim.model.body_quat, dtype=np.float64)
    except Exception as exc:  # noqa: BLE001
        _note_error(self, "model", exc)
    try:
        self._bb_buf["snaps"].append(_snapshot(self))
    except Exception as exc:  # noqa: BLE001
        _note_error(self, "snapshot", exc)


def _flush(self, reason: str) -> None:
    buf = getattr(self, "_bb_buf", None)
    self._bb_buf = None
    if not buf or not buf["actions"]:
        return
    try:
        suite = _suite_name(self)
        n = len(buf["actions"])
        succ = np.array(buf["success"], dtype=bool)
        init_id = buf["init_state_id"]
        ep_id = (
            f"{RUN_TAG}-{suite}-t{self.task_id:02d}-i{-1 if init_id is None else init_id:03d}"
            f"-s{buf['seed']}-{uuid.uuid4().hex[:8]}"
        )
        out_dir = os.path.join(TRACE_DIR, suite, f"task_{self.task_id:02d}")
        os.makedirs(out_dir, exist_ok=True)
        snaps = buf["snaps"]
        arrays = {
            "actions": np.asarray(buf["actions"], dtype=np.float32),
            "rewards": np.asarray(buf["rewards"], dtype=np.float32),
            "success": succ,
        }
        for key in ("eef_pos", "eef_quat", "gripper_qpos", "obj_pos", "obj_quat_wxyz", "goal", "grasp", "contact"):
            arrays[key] = np.stack([s[key] for s in snaps])
        if all(s.get("sim_state") is not None for s in snaps):
            arrays["sim_state"] = np.stack([s["sim_state"] for s in snaps])
        if buf.get("model_xml_gz") is not None:
            arrays["model_xml_gz"] = np.frombuffer(buf["model_xml_gz"], dtype=np.uint8)
        for key in ("model_body_pos", "model_body_quat"):
            if buf.get(key) is not None:
                arrays[key] = buf[key]
        np.savez_compressed(os.path.join(out_dir, ep_id + ".npz"), **arrays)
        meta = {
            "format_version": FORMAT_VERSION,
            "episode_id": ep_id,
            "run_tag": RUN_TAG,
            "policy": POLICY,
            "suite": suite,
            "task_id": int(self.task_id),
            "task_name": self.task,
            "language": self.task_description,
            "init_state_id": init_id,
            "seed": buf["seed"],
            "n_steps": n,
            "n_snapshots": len(snaps),
            "success": bool(succ.any()),
            "success_step": int(np.argmax(succ)) if succ.any() else None,
            "end_reason": reason,
            "max_episode_steps": int(self._max_episode_steps),
            "control_freq_hz": int(self.control_freq),
            "objects": self._bb_objects,
            "fixtures": self._bb_fixtures,
            "goal_state": self._bb_goal,
            "array_shapes": {k: list(v.shape) for k, v in arrays.items()},
            "wall_time_s": round(time.time() - buf["t0"], 2),
            "versions": VERSIONS,
            "logger_errors": buf.get("errors", {}),
            "n_logger_errors": buf.get("n_errors", 0),
        }
        with open(os.path.join(out_dir, ep_id + ".json"), "w") as f:
            json.dump(meta, f, indent=1)
    except Exception as exc:  # noqa: BLE001
        print(f"[bb_trace] WARNING: could not save an episode ({type(exc).__name__}: {exc})")


def reset(self, seed=None, **kwargs):
    _flush(self, "reset")
    init_id = None
    if self.init_states and self._init_states is not None:
        init_id = int(self.init_state_id % len(self._init_states))
    self._bb_raw = None
    out = _orig_reset(self, seed=seed, **kwargs)
    _start(self, seed, init_id)
    return out


def step(self, action):
    out = _orig_step(self, action)
    _obs, reward, terminated, truncated, info = out
    buf = getattr(self, "_bb_buf", None)
    if buf is not None:
        try:
            buf["actions"].append(np.asarray(action, dtype=np.float32).reshape(-1))
            buf["rewards"].append(float(reward))
            buf["success"].append(bool(info.get("is_success", False)))
            buf["snaps"].append(_snapshot(self))
        except Exception as exc:  # noqa: BLE001
            _note_error(self, "step", exc)
        if terminated or truncated:
            _flush(self, "success" if info.get("is_success", False) else "terminated")
        elif len(buf["actions"]) >= self._max_episode_steps:
            _flush(self, "max_steps")
    return out


def close(self):
    _flush(self, "close")
    return _orig_close(self)


@atexit.register
def _flush_all() -> None:
    for env in list(_live):
        _flush(env, "exit")


_LiberoEnv._ensure_env = _ensure_env
_LiberoEnv.reset = reset
_LiberoEnv.step = step
_LiberoEnv.close = close
print(f"[bb_trace] logging LIBERO episodes to {TRACE_DIR} (run={RUN_TAG}, policy={POLICY})")
