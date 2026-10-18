"""Build libero_traces.ipynb from the kit files in this folder (keeps them in sync).

    python build_notebook.py
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
KIT_FILES = ["bb_trace.py", "bb_eval.py", "bb_replay.py", "bb_colab.py"]


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip("\n").splitlines(keepends=True)}


def code(text):
    return {
        "cell_type": "code",
        "metadata": {},
        "execution_count": None,
        "outputs": [],
        "source": text.strip("\n").splitlines(keepends=True),
    }


cells = [
    md(r"""
# bounded-brain · LIBERO rollouts with privileged traces (π0.5)

This notebook spends spare Colab compute on data the project needs:

* It evaluates the open π0.5 LIBERO checkpoint with `lerobot-eval` (LeRobot 0.6.1), following the published
  protocol (10 episodes per task), so we can compare against reported success rates. The π0 checkpoint is
  probed too, but its weights do not load in LeRobot 0.6.1, so its runs are left out automatically.
* For **every** episode it also saves the simulator state at every step, object poses, gripper
  contacts and the task's goal predicates (`bb_trace.py`). These are the ground-truth labels the
  bounded-brain monitor will be evaluated on. Episodes can be replayed exactly offline (`bb_replay.py`).
* It adds out-of-distribution runs (LIBERO-90 tasks the checkpoints were not fine-tuned on), which
  produce failures, the interesting cases for a monitor.

**Before you start (about 5 minutes)**

1. *Runtime → Change runtime type → A100 GPU.* The A100 40 GB variant is cheaper than 80 GB; we do not need 80 GB.
2. π0 and π0.5 use the PaliGemma tokenizer, which is a **gated** Hugging Face repo. Log in to Hugging Face,
   open https://huggingface.co/google/paligemma-3b-pt-224 and accept the license (access is granted immediately).
   Then create a *read* token at https://huggingface.co/settings/tokens.
3. In Colab, open the key icon (**Secrets**) on the left, add `HF_TOKEN` with that token, and allow notebook access.
4. Run the cells in order. Keep this browser tab open while it runs.

**Two stages.** *Runtime → Run all* installs everything and runs the smoke tests (cell 6, about 20–30 min),
then stops at cell 7 on purpose. If cell 6 looks good, set `START_MAIN_RUNS = True` in cell 1 and fill in the two
numbers from Colab's Resources panel there, run cell 1, then run cells 7 and 8.

**When it stops.** The main runs stop by themselves before the compute budget or Colab's 12-hour session limit
runs out. Cell 8 then waits until every file has reached Google Drive (uploads lag behind the writes, and files
not yet uploaded are lost when the machine is released) and releases the GPU. If it stopped for the 12-hour
limit, open the notebook later and *Run all* again.

**Keep the browser connected.** Keep this tab open and the computer awake (no sleep), with a stable connection.
On 2026-10-17/18 a session ended after about 8 of its 12 hours; the cause is not known, and a lost browser
connection (sleep, network) is the most likely one.

**Disconnects.** Everything is written to Google Drive (`MyDrive/bounded-brain/libero_runs/`) as soon as each
episode ends. A short network drop does not stop the computation, which runs on Google's machine. If the runtime
itself is lost (idle timeout, a crash), run all cells again: finished units are skipped and only the interrupted
unit restarts; its partial episodes are kept separately and flagged. Before deleting a runtime by hand, run
`from google.colab import drive; drive.flush_and_unmount()` so the newest files are not lost.
"""),
    code(r"""
# @title 1 · Settings and GPU check
START_MAIN_RUNS = False      # set True once the smoke tests in cell 6 look good
# Budget for the main runs: two numbers from Colab's Resources panel (click the RAM/Disk bars at the top right,
# with this notebook connected to its A100). Changing either number later re-bases the budget; keeping them keeps it.
CU_AVAILABLE_NOW = None      # "Available: ... compute units"
CU_PER_HOUR_NOW = None       # "Usage rate: approximately ... per hour" (None = guess from the GPU type)
OUT_ROOT = "/content/drive/MyDrive/bounded-brain/libero_runs"
AUTO_DISCONNECT = True       # when the runs stop: wait for the upload to Drive, then release the GPU

import subprocess
gpu = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
                     capture_output=True, text=True).stdout.strip()
print("GPU:", gpu or "none! (Runtime -> Change runtime type -> A100)")
# Third-party observation (March 2026): A100 40GB ~5.40 CU/h, A100 80GB ~7.52 CU/h, L4 ~1.71 CU/h.
CU_RATE = CU_PER_HOUR_NOW or (7.52 if "80GB" in gpu.replace(" ", "") else 5.40 if "A100" in gpu
                              else 1.71 if "L4" in gpu else 5.40)
print(f"Compute units: {CU_AVAILABLE_NOW} available, {CU_RATE} per hour"
      + ("" if CU_PER_HOUR_NOW else " (guessed from the GPU; the Resources panel shows the real rate)"))
"""),
    code(r"""
# @title 2 · Mount Google Drive
from google.colab import drive
drive.mount("/content/drive")
import os
os.makedirs(OUT_ROOT, exist_ok=True)
print("Output folder:", OUT_ROOT)
"""),
    code(r"""
# @title 3 · Hugging Face token and gated-model access
import os
from google.colab import userdata
from huggingface_hub import hf_hub_download

class SetupNeeded(Exception):
    pass

try:
    token = userdata.get("HF_TOKEN")
except Exception as exc:  # SecretNotFoundError, or NotebookAccessError if "Notebook access" is off
    raise SetupNeeded(
        f"{type(exc).__name__}: click the key icon on the left (Secrets) -> Add new secret, name HF_TOKEN, "
        "value = your Hugging Face *read* token (starts with hf_), and switch on 'Notebook access'. "
        "Then run this cell again.") from None
os.environ["HF_TOKEN"] = token
try:
    hf_hub_download("google/paligemma-3b-pt-224", "tokenizer_config.json", token=token)
    print("PaliGemma tokenizer access: OK")
except Exception as exc:
    raise SetupNeeded(
        f"{type(exc).__name__}: no access to google/paligemma-3b-pt-224. Open that model page on Hugging Face "
        "with the same account as the token, accept the license, then run this cell again.") from None
"""),
    md(r"""
**4 · Install** LeRobot 0.6.1 and LIBERO in a separate Python 3.12 environment (about 5 minutes).
"""),
    code(r"""
%%bash
set -e
pip -q install uv
# Re-running this cell in the same runtime is fine: the environment is created only once.
[ -x /content/bbenv/bin/python ] || uv venv -q -p 3.12 /content/bbenv
# --torch-backend=auto picks the PyTorch CUDA build that matches this machine's driver.
uv pip install -q --python /content/bbenv/bin/python --torch-backend=auto "lerobot[libero,pi]==0.6.1"
/content/bbenv/bin/python -c "import torch, lerobot; print('torch', torch.__version__, '| CUDA available:', torch.cuda.is_available(), '| lerobot', lerobot.__version__)"
"""),
    code(r"""
# @title 5 · Rendering (EGL) and LIBERO configuration
import os, subprocess, textwrap
icd = "/usr/share/glvnd/egl_vendor.d/10_nvidia.json"   # lets MuJoCo find NVIDIA's EGL driver
if not os.path.exists(icd):
    os.makedirs(os.path.dirname(icd), exist_ok=True)
    with open(icd, "w") as f:
        f.write('{"file_format_version": "1.0.0", "ICD": {"library_path": "libEGL_nvidia.so.0"}}')
setup = textwrap.dedent('''
    import os, yaml, importlib.util
    root = os.path.join(os.path.dirname(importlib.util.find_spec("libero").origin), "libero")
    paths = {"benchmark_root": "", "bddl_files": "bddl_files", "init_states": "init_files",
             "datasets": "../datasets", "assets": "assets"}
    cfg = {k: os.path.join(root, v) for k, v in paths.items()}
    os.makedirs(os.path.expanduser("~/.libero"), exist_ok=True)   # avoids LIBERO's interactive prompt
    with open(os.path.expanduser("~/.libero/config.yaml"), "w") as f:
        yaml.safe_dump(cfg, f)
    from libero.libero import get_assets_path
    print("LIBERO assets:", get_assets_path())      # downloads them once, before any parallel worker starts
    import mujoco
    ctx = mujoco.GLContext(64, 64); ctx.make_current(); ctx.free()
    print("MuJoCo rendering OK with", os.environ["MUJOCO_GL"])
''')

def try_backend(backend):
    env = dict(os.environ, MUJOCO_GL=backend, PYOPENGL_PLATFORM=backend, MPLBACKEND="Agg", PYTHONPATH="")
    r = subprocess.run(["/content/bbenv/bin/python", "-c", setup], env=env, capture_output=True, text=True)
    print(r.stdout[-1500:] or r.stderr[-1500:])
    return r.returncode == 0

MUJOCO_GL = "egl"
if not try_backend("egl"):
    print("EGL failed; falling back to OSMesa (CPU rendering, slower).")
    subprocess.run("apt-get -qq update && apt-get -qq install -y libosmesa6", shell=True, check=False)
    MUJOCO_GL = "osmesa"
    assert try_backend("osmesa"), "No working MuJoCo renderer; send me the output above."
"""),
    md(r"""
The next cells write the trace-logging kit to `/content/bbkit` (the same files are in the
project repository under `experiments/colab/`).
"""),
]

# %%writefile must be the first line of its cell, so the folder is created in its own cell.
cells.append(code("!mkdir -p /content/bbkit"))
for name in KIT_FILES:
    with open(os.path.join(HERE, name)) as f:
        body = f.read()
    cells.append(code(f"%%writefile /content/bbkit/{name}\n" + body))

cells += [
    code(r"""
# @title 6 · Smoke tests (about 10–20 min): π0.5 sync, π0.5 parallel envs, π0
import sys, importlib, json
sys.path.insert(0, "/content/bbkit")
import bb_colab; importlib.reload(bb_colab)

# n_action_steps=10 follows LeRobot's LIBERO docs. The checkpoints switch on torch.compile in max-autotune mode,
# which spends many minutes autotuning in every new process; inference is a small share of an episode, so turn it off.
PI05, PI05_ARGS = "lerobot/pi05_libero_finetuned", ("--policy.n_action_steps=10", "--policy.compile_model=false")
PI0, PI0_ARGS = "lerobot/pi0_libero", ("--policy.compile_model=false",)

def probe(tag, skip_if_failed=False, **kw):
    # Only the optional parallel-env probe is not retried; the required smoke tests always run again.
    prev = bb_colab.load_ledger(OUT_ROOT)["units"].get(f"{tag}/{kw['suite']}")
    if skip_if_failed and prev and prev.get("status") == "failed":
        print(f"[skip] {tag}: failed in an earlier session"); return prev
    return bb_colab.run_unit(OUT_ROOT, tag, mujoco_gl=MUJOCO_GL, heartbeat_s=120, **kw)

s1 = probe("smoke_pi05_sync", policy=PI05, suite="libero_spatial", n_episodes=1, seed=0,   # includes the model download
           batch_size=1, use_async=False, extra=PI05_ARGS, task_ids=[0], timeout_s=2400)
assert s1.get("status") == "done", "The basic smoke test failed. Send me the last 40 lines of the log file printed above."
for r in bb_colab.episode_index(OUT_ROOT, run_tag="smoke_pi05_sync"):
    print("trace:", r)

s2 = probe("smoke_pi05_async", skip_if_failed=True, policy=PI05, suite="libero_object", n_episodes=2, seed=0,
           batch_size=2, use_async=True, extra=PI05_ARGS, task_ids=[0], timeout_s=900)
ASYNC_OK = s2.get("status") == "done" and s2.get("episodes_logged", 0) >= 2
s3 = probe("smoke_pi0_sync", policy=PI0, suite="libero_spatial", n_episodes=1, seed=0,     # includes the model download
           batch_size=1, use_async=False, extra=PI0_ARGS, task_ids=[0], timeout_s=2400)
PI0_OK = s3.get("status") == "done"     # "failed" also when its weights did not load (then the runs are skipped)
print(f"\nparallel envs work: {ASYNC_OK} | pi0 checkpoint usable: {PI0_OK} | "
      f"pi0.5 seconds per episode (single env, incl. loading): {s1.get('sec_per_episode')}")
if s3.get("weights_warning"):
    print("pi0: the checkpoint's weights do not load in LeRobot 0.6.1, so pi0 runs are left out of the plan.")
print("\nSMOKE TESTS DONE. Copy this cell's output to Claude. To start the main runs: in cell 1 set "
      "START_MAIN_RUNS = True and fill in CU_AVAILABLE_NOW / CU_PER_HOUR_NOW, run cell 1, then run cells 7 and 8.")
"""),
    code(r"""
# @title 7 · Main runs (they stop by themselves before the budget or Colab's 12-hour limit runs out)
SESSION_LIMIT_H = 12.0    # Colab Pro / pay-as-you-go sessions end after at most 12 hours (Colab FAQ)
END_RESERVE_H = 0.5       # kept free at the end of a session for the summary and the upload to Drive
FINAL_RESERVE_H = 0.75    # kept out of the budget: the final summary and the setup of one more session
STALL_MIN = 25            # no new episode for this long (45 min before a unit's first one): the run is hung, stop it
FIRST_EPISODE_MIN = 45

import glob, os, re, shutil, signal, subprocess, threading, time, traceback

class MainRunsNotStarted(Exception):
    pass

if not START_MAIN_RUNS:
    raise MainRunsNotStarted("Stopped before the main runs on purpose. If the smoke tests look good: in cell 1 set "
                             "START_MAIN_RUNS = True and fill in CU_AVAILABLE_NOW / CU_PER_HOUR_NOW, run cell 1, "
                             "then run this cell and cell 8.")

# Session clock: the kernel's start time, kept in a file on this machine so re-running cells does not reset it.
_mark = "/content/.bb_session_start"
if not os.path.exists(_mark):
    try:
        import psutil
        _t0 = psutil.Process(os.getpid()).create_time()
    except Exception:
        _t0 = time.time()
    with open(_mark, "w") as f:
        f.write(str(_t0))
with open(_mark) as f:
    SESSION_START = float(f.read())

def session_hours():
    return (time.time() - SESSION_START) / 3600

# Budget in hours of runs, from cell 1's numbers. It is re-based only when those numbers change, so a restart that
# keeps them continues the same budget.
ledger = bb_colab.load_ledger(OUT_ROOT)
panel = [CU_AVAILABLE_NOW, CU_PER_HOUR_NOW]
if CU_AVAILABLE_NOW is not None and ledger.get("budget_from_panel") != panel:
    ledger["budget_hours"] = max(0.0, CU_AVAILABLE_NOW / CU_RATE - FINAL_RESERVE_H)
    ledger["gpu_seconds_at_budget_start"] = ledger.get("gpu_seconds", 0.0)
    ledger["budget_from_panel"] = panel
    bb_colab.save_ledger(OUT_ROOT, ledger)
    print(f"Budget set from cell 1: {CU_AVAILABLE_NOW} CU at {CU_RATE} CU/h.")
elif "budget_hours" not in ledger:
    raise MainRunsNotStarted("Fill in CU_AVAILABLE_NOW in cell 1 (Colab's Resources panel), run cell 1, "
                             "then run this cell and cell 8.")
budget_h = ledger["budget_hours"]
start_s = ledger.get("gpu_seconds_at_budget_start", 0.0)

def used_hours():
    return (bb_colab.load_ledger(OUT_ROOT)["gpu_seconds"] - start_s) / 3600

MAX_STEPS = {"libero_spatial": 280, "libero_object": 280, "libero_goal": 300, "libero_10": 520, "libero_90": 400}

def unit_hours(suite):
    # Expected duration of a unit, scaled from the main units finished so far (same suite if there is one).
    done = [s for u, s in bb_colab.load_ledger(OUT_ROOT)["units"].items()
            if not u.startswith("smoke_") and s.get("status") == "done" and s.get("minutes") and s.get("suite") in MAX_STEPS]
    same = [s for s in done if s["suite"] == suite]
    pool, factor = (same, 1.15) if same else (done, 1.5)
    work = bb_colab.SUITE_TASKS[suite] * MAX_STEPS[suite]          # tasks x step limit
    if not pool:
        return work * 0.25 / 3600                                   # before any unit has finished
    per_work = (sum(s["minutes"] * 60 for s in pool)
                / sum(bb_colab.SUITE_TASKS[s["suite"]] * MAX_STEPS[s["suite"]] for s in pool))
    return factor * work * per_work / 3600

def timeout_for(suite, n_ep, need_h, use_async):
    # Hung runs are caught by the progress watch below, so the hard limit is generous: 3x the expected time.
    default = max(1800.0, 1200.0 + 30.0 * bb_colab.SUITE_TASKS[suite] * n_ep * (1 if use_async else 2))
    return max(default, 3 * need_h * 3600)

def kill_evals():
    # Same anchored pattern as bb_colab: only our own lerobot-eval processes; their whole process group.
    pattern = "^" + re.escape(bb_colab.VENV_PY) + " " + re.escape(os.path.join(bb_colab.KIT, "bb_eval.py"))
    for pid in subprocess.run(["pgrep", "-f", pattern], capture_output=True, text=True).stdout.split():
        try:
            os.killpg(os.getpgid(int(pid)), signal.SIGKILL)
        except (ProcessLookupError, PermissionError, ValueError):
            pass

def watch_progress(unit_trace_dir, done, poll_s=60):
    last_n, last_t = None, time.time()
    while not done.wait(poll_s):
        n = bb_colab.count_traces(unit_trace_dir)
        if n != last_n:
            last_n, last_t = n, time.time()
        elif time.time() - last_t > (STALL_MIN if n else FIRST_EPISODE_MIN) * 60:
            print(f"       !!! no new episode for {(time.time() - last_t) / 60:.0f} min: stopping this unit as hung")
            kill_evals()
            return

def run_watched(tag, use_async, need_h, **kw):
    done = threading.Event()
    threading.Thread(target=watch_progress, args=(os.path.join(OUT_ROOT, "traces", tag, kw["suite"]), done),
                     daemon=True).start()
    try:
        return bb_colab.run_unit(OUT_ROOT, tag, use_async=use_async,
                                 timeout_s=timeout_for(kw["suite"], kw["n_episodes"], need_h, use_async), **kw)
    finally:
        done.set()

def blocker(need_h):
    if used_hours() + need_h > budget_h:
        return "budget"
    if session_hours() + need_h + END_RESERVE_H > SESSION_LIMIT_H:
        return "session_limit"
    return None

print(f"Budget {budget_h:.1f} h for the main runs, used so far {used_hours():.1f} h. "
      f"This session has run {session_hours():.1f} h of at most {SESSION_LIMIT_H:.0f} h.")

STD = ["libero_spatial", "libero_object", "libero_goal", "libero_10"]
RANDOM_INIT = ("--env.init_states=false",)   # random object layouts instead of LIBERO's 50 fixed ones
plan  = [("pi05_s1000", PI05, s, 10, 1000, PI05_ARGS) for s in STD]                        # 1 reproduce the published protocol
plan += [("pi05_ood90_s1000", PI05, "libero_90", 3, 1000, PI05_ARGS)]                      # 2 unseen tasks -> failures
if PI0_OK:
    plan += [("pi0_s1000", PI0, s, 10, 1000, PI0_ARGS) for s in STD]                        # 3 a second, weaker policy
    plan += [("pi0_ood90_s1000", PI0, "libero_90", 3, 1000, PI0_ARGS)]                      # 4
plan += [("pi05_randinit_s1000", PI05, s, 5, 1000, PI05_ARGS + RANDOM_INIT) for s in STD]    # 5 new layouts
plan += [("pi05_ood90_randinit_s2000", PI05, "libero_90", 3, 2000, PI05_ARGS + RANDOM_INIT)] # 6 more, different failures
if PI0_OK:
    plan += [("pi0_randinit_s1000", PI0, s, 5, 1000, PI0_ARGS + RANDOM_INIT) for s in STD]  # 7
plan += [("pi05_s2000", PI05, s, 10, 2000, PI05_ARGS) for s in STD]                        # 8 extra seeds (for mean ± sd
plan += [("pi05_s3000", PI05, s, 10, 3000, PI05_ARGS) for s in STD]                        #   of the reproduction)
for seed in range(4000, 40000, 1000):                                                     # 9 then new layouts until the
    plan += [(f"pi05_ood90_randinit_s{seed}", PI05, "libero_90", 3, seed, PI05_ARGS + RANDOM_INIT)]   # budget is used
    plan += [(f"pi05_randinit_s{seed}", PI05, s, 5, seed, PI05_ARGS + RANDOM_INIT) for s in STD]

def finished(tag, suite):
    return os.path.exists(os.path.join(OUT_ROOT, "evals", tag, suite, "eval_info.json"))

# Units that are valued for their individual episodes rather than as a complete set (random layouts, unseen tasks).
# If such a unit was cut off after logging at least half of its episodes, it is not run again: the same seed gives
# the same layouts, so a re-run would mostly repeat those episodes. They are kept, flagged `partial_attempt`.
EXPLORATORY = ("randinit", "ood90")

def set_aside(tag, suite):
    # Move a cut-off attempt's folders aside (as run_unit would) and count the episodes all such attempts logged.
    stamp = int(time.time())
    for d in (os.path.join(OUT_ROOT, "evals", tag, suite), os.path.join(OUT_ROOT, "traces", tag, suite)):
        if os.path.exists(d):
            shutil.move(d, f"{d}__partial_{stamp}")
            print(f"[keep] earlier partial attempt kept at {d}__partial_{stamp}")
    return sum(bb_colab.count_traces(d)
               for d in glob.glob(os.path.join(OUT_ROOT, "traces", tag, glob.escape(suite) + "__partial_*")))

RUN_STATE = "finished"     # read by cell 8: finished | budget | session_limit | error
skipped_for_budget, failures_in_a_row = [], 0
try:
    for tag, policy, suite, n_ep, seed, extra in plan:
        kw = dict(policy=policy, suite=suite, n_episodes=n_ep, seed=seed, batch_size=n_ep, extra=extra, mujoco_gl=MUJOCO_GL)
        if not finished(tag, suite) and any(k in tag for k in EXPLORATORY):
            n_all, n_cut = n_ep * bb_colab.SUITE_TASKS[suite], set_aside(tag, suite)
            if n_cut >= n_all / 2:
                print(f"[skip] {tag}/{suite}: a cut-off attempt already logged {n_cut} of {n_all} episodes "
                      "(kept, flagged partial)")
                continue
        need_h = unit_hours(suite)
        why = None if finished(tag, suite) else blocker(need_h)
        if why == "budget":
            skipped_for_budget.append(f"{tag}/{suite}")
            continue                     # a smaller unit further down may still fit
        if why == "session_limit":       # it fits the budget, but not the rest of this session
            RUN_STATE = "session_limit"
            print(f"[stop] {tag}/{suite} needs about {need_h:.1f} h and would not finish before Colab's "
                  f"{SESSION_LIMIT_H:.0f}-hour limit (this session has run {session_hours():.1f} h).")
            break
        s = run_watched(tag, ASYNC_OK, need_h, **kw)    # units finished earlier are only re-checked
        if s.get("status") == "failed" and ASYNC_OK and blocker(2 * need_h) is None:
            print("Retrying this unit with a single process.")
            s = run_watched(tag, False, 2 * need_h, **kw)
        failures_in_a_row = failures_in_a_row + 1 if s.get("status") == "failed" else 0
        if failures_in_a_row >= 3:
            RUN_STATE = "error"
            print("[stop] three units in a row failed, so the runs stop here instead of using up the budget. "
                  "Send Claude this cell's output.")
            break
except Exception:  # not KeyboardInterrupt: the stop button still just stops
    RUN_STATE = "error"
    traceback.print_exc()
    print("[stop] unexpected error (above). Cell 8 still uploads everything and releases the GPU.")
if skipped_for_budget:
    RUN_STATE = "budget" if RUN_STATE == "finished" else RUN_STATE
    print(f"[budget] {len(skipped_for_budget)} planned units did not fit in the remaining budget "
          f"(first: {skipped_for_budget[0]}).")
print(f"Main runs stopped: {RUN_STATE}. Budget used {used_hours():.1f} of {budget_h:.1f} h; "
      f"session at {session_hours():.1f} h.")
"""),
    code(r"""
# @title 8 · Summary, wait for the upload to Drive, release the GPU
import csv, collections, os, traceback
from google.colab import drive
RUN_STATE = globals().get("RUN_STATE", "finished")
try:
    ledger = bb_colab.load_ledger(OUT_ROOT)
    print(f"GPU time used by evaluations: {ledger['gpu_seconds'] / 3600:.2f} h\n")
    print(f"{'unit':40s} {'status':7s} {'success %':>9s} {'episodes':>8s} {'min':>6s}")
    for unit, s in sorted(ledger["units"].items()):
        print(f"{unit:40s} {s.get('status', '?'):7s} {str(s.get('pc_success')):>9s} "
              f"{s.get('episodes_logged') or 0:8d} {s.get('minutes') or 0:6.1f}")
    if RUN_STATE != "session_limit":   # the episode index and the zip are made once, at the very end
        rows = bb_colab.episode_index(OUT_ROOT)
        with open(os.path.join(OUT_ROOT, "episodes.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["episode_id"])
            w.writeheader(); w.writerows(rows)
        complete = [r for r in rows if not r["partial_attempt"]]
        by = collections.Counter((r["run_tag"], r["success"]) for r in complete)
        print(f"\n{len(complete)} episodes with traces ({len(rows) - len(complete)} more from cut-off attempts); "
              "failures per run:", {tag: n for (tag, ok), n in sorted(by.items()) if not ok})
        print("Packing traces for download (no videos) ...")
        bb_colab.export_zip(OUT_ROOT)      # download this one file from Drive and put it in bounded-brain/data/
except Exception:
    traceback.print_exc()
    print("The summary failed (above); the data already on Drive is not affected.")

# Drive uploads lag behind the writes. Releasing the machine before they finish loses the newest files,
# so wait for them explicitly.
print("\nWaiting until every file has reached Google Drive (usually a few minutes) ...")
try:
    drive.flush_and_unmount(timeout_ms=40 * 60 * 1000)
    print("All files are on Google Drive.")
except Exception as exc:
    print(f"The upload check did not finish ({type(exc).__name__}: {exc}); the newest files may be missing.")

if RUN_STATE == "session_limit":
    print("\nColab's 12-hour session limit is close, so this session ends here. Later: open this notebook, "
          "Runtime -> Run all. Finished units are skipped; the budget is kept.")
elif RUN_STATE == "error":
    print("\nThe main runs stopped because of errors. Send Claude the output of cell 7.")
else:
    print("\nAll done. Download bb_traces_export.zip from MyDrive/bounded-brain/libero_runs/.")
if AUTO_DISCONNECT:
    from google.colab import runtime
    print("Releasing the GPU so no more compute units are used.")
    runtime.unassign()
"""),
]

nb = {
    "cells": cells,
    "metadata": {
        "accelerator": "GPU",
        "colab": {"provenance": [], "gpuType": "A100"},
        "kernelspec": {"display_name": "Python 3", "name": "python3"},
        "language_info": {"name": "python"},
    },
    "nbformat": 4,
    "nbformat_minor": 0,
}
out = os.path.join(HERE, "libero_traces.ipynb")
with open(out, "w") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
print("wrote", out, "with", len(cells), "cells")
