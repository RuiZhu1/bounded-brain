"""Helpers for the bounded-brain Colab notebook.

Runs in Colab's own Python. Each evaluation "unit" (one policy x one LIBERO suite x one
seed) is a separate `lerobot-eval` process inside the /content/bbenv virtualenv, with the
trace logger switched on. Units are resumable: a unit whose eval_info.json exists on
Google Drive is skipped, so after a disconnect you just run the notebook again.
"""

from __future__ import annotations

import glob
import json
import os
import re
import shutil
import signal
import subprocess
import threading
import time

VENV_PY = "/content/bbenv/bin/python"
KIT = "/content/bbkit"
SUITE_TASKS = {"libero_spatial": 10, "libero_object": 10, "libero_goal": 10, "libero_10": 10, "libero_90": 90}
ECHO_KEYS = ("pc_success", "Traceback", "Error", "error:", "bb_trace", "Killed", "CUDA out of memory",
             "Could not load state dict", "Missing keys", "Unexpected keys")


def _ledger_path(out_root: str) -> str:
    return os.path.join(out_root, "ledger.json")


def load_ledger(out_root: str) -> dict:
    try:
        with open(_ledger_path(out_root)) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"units": {}, "gpu_seconds": 0.0}


def save_ledger(out_root: str, ledger: dict) -> None:
    os.makedirs(out_root, exist_ok=True)
    tmp = _ledger_path(out_root) + ".tmp"
    with open(tmp, "w") as f:
        json.dump(ledger, f, indent=1)
    os.replace(tmp, _ledger_path(out_root))


def count_traces(trace_dir: str) -> int:
    return len(glob.glob(os.path.join(trace_dir, "**", "*.json"), recursive=True))


# lerobot 0.6.1's pi0/pi05 `from_pretrained` catches a failed `load_state_dict`, prints one of these
# lines and carries on with partly random weights. Such a unit must not count as valid data.
WEIGHT_WARNINGS = ("Could not load state dict", "Missing keys when loading state dict",
                   "Unexpected keys when loading state dict", "Returning model without loading pretrained weights")


def weight_warning(log_path: str) -> str | None:
    """First weight-loading warning in a unit's log, or None."""
    try:
        with open(log_path, errors="replace") as f:
            for line in f:
                if any(w in line for w in WEIGHT_WARNINGS):
                    return line.strip()[:300]
    except OSError:
        pass
    return None


def _summary_from_disk(unit: str, eval_dir: str, unit_trace_dir: str, log_path: str, previous: dict) -> dict:
    """Rebuild a finished unit's summary from its files (the ledger entry may be stale)."""
    summary = dict(previous or {})
    summary.update({"unit": unit, "status": "done", "episodes_logged": count_traces(unit_trace_dir), "log": log_path})
    try:
        with open(os.path.join(eval_dir, "eval_info.json")) as f:
            overall = json.load(f).get("overall", {})
        summary["pc_success"] = overall.get("pc_success")
        summary["n_episodes"] = overall.get("n_episodes")
    except (OSError, json.JSONDecodeError):
        pass
    warn = weight_warning(log_path)
    if warn:
        summary["status"] = "failed"
        summary["weights_warning"] = warn
    return summary


def run_unit(
    out_root: str,
    tag: str,
    policy: str,
    suite: str,
    n_episodes: int,
    seed: int,
    batch_size: int,
    use_async: bool,
    extra: tuple = (),
    task_ids: list | None = None,
    episode_length: int | None = None,
    max_videos: int = 1,
    mujoco_gl: str = "egl",
    heartbeat_s: int = 300,
    timeout_s: float | None = None,
) -> dict:
    """Run one lerobot-eval process; return a summary dict (also stored in the ledger).

    timeout_s: kill the whole process group (including parallel env workers) after this
    many seconds and mark the unit as failed, so a hung run cannot block the notebook.
    Default: 20 min + 30 s per episode (60 s without parallel envs), at least 30 min.
    """
    if timeout_s is None:
        n_tasks = len(task_ids) if task_ids is not None else SUITE_TASKS.get(suite, 10)
        timeout_s = max(1800.0, 1200.0 + 30.0 * n_tasks * n_episodes * (1 if use_async else 2))
    unit = f"{tag}/{suite}"
    eval_dir = os.path.join(out_root, "evals", tag, suite)
    trace_dir = os.path.join(out_root, "traces", tag)
    unit_trace_dir = os.path.join(trace_dir, suite)  # bb_trace writes <trace_dir>/<suite>/task_XX/
    log_dir = os.path.join(out_root, "logs")
    os.makedirs(log_dir, exist_ok=True)
    info_path = os.path.join(eval_dir, "eval_info.json")
    log_path = os.path.join(log_dir, f"{tag}__{suite}.log")
    ledger = load_ledger(out_root)
    if os.path.exists(info_path):
        summary = _summary_from_disk(unit, eval_dir, unit_trace_dir, log_path, ledger["units"].get(unit))
        if ledger["units"].get(unit) != summary:
            ledger["units"][unit] = summary
            save_ledger(out_root, ledger)
        note = f" (weights did not load: {summary['weights_warning']})" if summary.get("weights_warning") else ""
        print(f"[skip] {unit}: already run{note}")
        return summary
    # An earlier attempt was cut off (runtime lost, timeout, error). Keep its data, but apart from
    # the new attempt, so finished units never contain duplicate episodes.
    stamp = int(time.time())
    for d in (eval_dir, unit_trace_dir):
        if os.path.exists(d):
            shutil.move(d, f"{d}__partial_{stamp}")
            print(f"[keep] earlier partial attempt kept at {d}__partial_{stamp}")

    cmd = [
        VENV_PY, os.path.join(KIT, "bb_eval.py"),
        f"--policy.path={policy}",
        "--env.type=libero",
        f"--env.task={suite}",
        f"--eval.n_episodes={n_episodes}",
        f"--eval.batch_size={batch_size}",
        f"--eval.use_async_envs={'true' if use_async else 'false'}",
        f"--seed={seed}",
        f"--output_dir={eval_dir}",
        *extra,
    ]
    if task_ids is not None:
        cmd.append("--env.task_ids=" + json.dumps(list(task_ids)).replace(" ", ""))
    if episode_length is not None:
        cmd.append(f"--env.episode_length={episode_length}")
    # The eval runs in a separate Python 3.12 venv; do not leak Colab kernel settings into it.
    # Colab sets MPLBACKEND to its inline backend, which the venv lacks (matplotlib then fails on import),
    # and PYTHONPATH to its own 3.13 packages.
    env = dict(
        os.environ,
        MPLBACKEND="Agg",
        MUJOCO_GL=mujoco_gl,
        PYOPENGL_PLATFORM=mujoco_gl,
        BB_TRACE_DIR=trace_dir,
        BB_RUN_TAG=tag,
        BB_POLICY=policy,
        BB_MAX_VIDEOS=str(max_videos),
        PYTHONPATH=KIT,
        TQDM_DISABLE="1",
        TOKENIZERS_PARALLELISM="false",
    )
    print(f"[run ] {unit}: {policy} | {n_episodes} ep/task | batch {batch_size} | "
          f"{'async' if use_async else 'sync'} | seed {seed}")
    t0 = time.time()
    stop = threading.Event()
    lock = threading.Lock()
    credited = [0.0]

    def credit(seconds: float, final: dict | None = None) -> None:
        # GPU time is booked every heartbeat, so it is not lost if the runtime dies mid-unit.
        with lock:
            led = load_ledger(out_root)
            led["gpu_seconds"] = led.get("gpu_seconds", 0.0) + seconds
            led["units"][unit] = final or {"unit": unit, "status": "running",
                                           "minutes": round((time.time() - t0) / 60, 2),
                                           "episodes_logged": count_traces(unit_trace_dir)}
            save_ledger(out_root, led)
            credited[0] += seconds

    def heartbeat():
        while not stop.wait(heartbeat_s):
            credit(heartbeat_s)
            print(f"       ... {unit}: {count_traces(unit_trace_dir)} episodes logged, "
                  f"{(time.time() - t0) / 60:.1f} min")

    # An eval left over from an interrupted cell would still hold the GPU: stop it first. The anchored
    # pattern only matches command lines that start with the venv's python running our bb_eval.py.
    subprocess.run(["pkill", "-f", "^" + re.escape(VENV_PY) + " " + re.escape(os.path.join(KIT, "bb_eval.py"))],
                   check=False)
    hb = threading.Thread(target=heartbeat, daemon=True)
    hb.start()
    timed_out = threading.Event()

    def kill_group(proc):
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass

    with open(log_path, "w") as log:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env,
                                start_new_session=True)

        def watchdog():
            if not stop.wait(timeout_s) and proc.poll() is None:
                timed_out.set()
                print(f"       !!! {unit}: no result after {timeout_s / 60:.0f} min, stopping it")
                kill_group(proc)

        threading.Thread(target=watchdog, daemon=True).start()
        banner_shown = False
        try:
            for line in proc.stdout:
                log.write(line)
                if "[bb_trace] logging LIBERO episodes" in line:   # printed by every parallel env worker
                    if banner_shown:
                        continue
                    banner_shown = True
                if any(k in line for k in ECHO_KEYS):
                    print("       " + line.rstrip()[:220])
            rc = proc.wait()
        except BaseException:
            # The cell was interrupted: the eval runs in its own process group, so stop it explicitly.
            stop.set()
            kill_group(proc)
            raise
    stop.set()
    hb.join(timeout=60)
    if timed_out.is_set():
        rc = rc if rc not in (0, None) else -9
    elapsed = time.time() - t0
    n_eps = count_traces(unit_trace_dir)
    summary = {
        "unit": unit, "policy": policy, "suite": suite, "seed": seed, "batch_size": batch_size,
        "async": use_async, "returncode": rc, "minutes": round(elapsed / 60, 2),
        "episodes_logged": n_eps, "status": "done" if (rc == 0 and os.path.exists(info_path)) else "failed",
        "timed_out": timed_out.is_set(), "log": log_path,
    }
    if summary["status"] == "done":
        with open(info_path) as f:
            info = json.load(f)
        overall = info.get("overall", {})
        summary["pc_success"] = overall.get("pc_success")
        summary["n_episodes"] = overall.get("n_episodes")
        summary["sec_per_episode"] = round(elapsed / max(1, n_eps), 2)
    warn = weight_warning(log_path)
    if warn:  # the policy ran with partly random weights: its episodes are not valid data
        summary["status"] = "failed"
        summary["weights_warning"] = warn
    credit(max(0.0, elapsed - credited[0]), final=summary)
    status = summary["status"].upper()
    print(f"[{status}] {unit}: {summary.get('pc_success')}% success, {n_eps} episodes, "
          f"{summary['minutes']} min (log: {log_path})" + (f"\n       WEIGHTS DID NOT LOAD: {warn}" if warn else ""))
    return summary


def episode_index(out_root: str, run_tag: str = "") -> list[dict]:
    """One row per logged episode (all runs, or only `run_tag`'s, which reads far fewer files)."""
    rows = []
    for j in glob.glob(os.path.join(out_root, "traces", run_tag, "**", "*.json"), recursive=True):
        try:
            with open(j) as f:
                m = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        row = {k: m.get(k) for k in (
            "episode_id", "run_tag", "policy", "suite", "task_id", "language", "init_state_id", "seed",
            "n_steps", "success", "success_step", "end_reason", "n_logger_errors")}
        row["partial_attempt"] = "__partial_" in j  # from a unit attempt that was cut off
        row["path"] = os.path.relpath(j, out_root)
        rows.append(row)
    return rows


def export_zip(out_root: str, dest_name: str = "bb_traces_export.zip") -> str:
    """Pack traces, eval summaries, logs, ledger and index into one zip on Drive (no videos)."""
    import zipfile

    local = os.path.join("/content", dest_name) if os.path.isdir("/content") else os.path.join(out_root, "_" + dest_name)
    patterns = ["traces/**/*.npz", "traces/**/*.json", "evals/**/eval_info.json", "logs/*.log",
                "ledger.json", "episodes.csv"]
    n = 0
    with zipfile.ZipFile(local, "w", compression=zipfile.ZIP_STORED) as z:  # .npz is already compressed
        for pat in patterns:
            for path in glob.glob(os.path.join(out_root, pat), recursive=True):
                if os.path.isfile(path):
                    z.write(path, os.path.relpath(path, out_root))
                    n += 1
    dest = os.path.join(out_root, dest_name)
    if os.path.abspath(local) != os.path.abspath(dest):
        shutil.copy(local, dest)
    print(f"{n} files, {os.path.getsize(dest) / 1e6:.0f} MB -> {dest}")
    return dest
