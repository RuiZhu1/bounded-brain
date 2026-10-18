"""Replay a logged LIBERO episode exactly (offline, CPU is enough).

    from bb_replay import Replayer
    rep = Replayer("path/to/<episode_id>.npz")   # reads the matching .json too
    for k in range(rep.n_snapshots):
        inner = rep.goto(k)                       # robosuite/LIBERO env at snapshot k
        on = inner._eval_predicate(["on", "akita_black_bowl_1", "plate_1"])

Any predicate, contact or distance can be recomputed this way, so labels for new
specifications do not require re-running the policy.
"""

from __future__ import annotations

import gzip
import json
import os

import numpy as np


class Replayer:
    def __init__(self, npz_path: str):
        from libero.libero import benchmark
        from lerobot.envs.libero import LiberoEnv

        self.data = np.load(npz_path)
        with open(os.path.splitext(npz_path)[0] + ".json") as f:
            self.meta = json.load(f)
        if "sim_state" not in self.data.files or "model_xml_gz" not in self.data.files:
            raise ValueError("this trace has no sim_state/model_xml_gz; exact replay is impossible")
        suite = benchmark.get_benchmark_dict()[self.meta["suite"]]()
        self.env = LiberoEnv(
            task_suite=suite,
            task_id=self.meta["task_id"],
            task_suite_name=self.meta["suite"],
            obs_type="pixels_agent_pos",
        )
        self.env._ensure_env()
        xml = gzip.decompress(self.data["model_xml_gz"].tobytes()).decode("utf-8")
        self.env._env.reset_from_xml_string(xml)
        model = self.env._env.env.sim.model
        # LIBERO places fixtures by writing model.body_pos/body_quat at reset time.
        if "model_body_pos" in self.data.files:
            model.body_pos[:] = self.data["model_body_pos"]
            model.body_quat[:] = self.data["model_body_quat"]
        self.n_snapshots = int(self.data["sim_state"].shape[0])

    def goto(self, k: int):
        control = self.env._env
        control.set_state(self.data["sim_state"][k])
        control.env.sim.forward()
        return control.env

    def close(self) -> None:
        self.env.close()
