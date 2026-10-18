# experiments/colab/ — LIBERO rollouts with privileged traces

Status (2026-10-18): done. Two Colab sessions (the first ended after about 8 hours, F42) produced 4,062 episodes
with traces, 0 logger errors; analysis in `experiments/analysis/` and `docs/08-libero-results.md`. The π0
checkpoint does not load in LeRobot 0.6.1, so π0 was left out (`docs/02` F38, `docs/07` D-019). The logging and
runner code was also tested end-to-end on CPU with a random-weight ACT policy, and the stop logic of cells 7 and 8
with a simulated clock (D-020, D-021).

## What it produces

`libero_traces.ipynb` runs `lerobot-eval` on the LIBERO suites with the open checkpoint
`lerobot/pi05_libero_finetuned` (and `lerobot/pi0_libero` if its weights load), and logs every episode with
privileged simulator information. Plan, in priority order (it stops when the compute budget is used):

| # | Unit tag | Policy | Suites | Episodes | Why |
|---|---|---|---|---|---|
| 1 | `pi05_s1000` | π0.5 | spatial, object, goal, 10 | 10 / task (400) | reproduce the published protocol (P5-1) |
| 2 | `pi05_ood90_s1000` | π0.5 | libero_90 | 3 / task (270) | tasks outside its fine-tuning data → failures |
| 3 | `pi0_s1000` | π0 | spatial, object, goal, 10 | 10 / task (400) | a second, weaker policy (skipped: checkpoint does not load) |
| 4 | `pi0_ood90_s1000` | π0 | libero_90 | 3 / task (270) | failures (skipped, as 3) |
| 5 | `pi05_randinit_s1000` | π0.5 | spatial, object, goal, 10 | 5 / task (200) | random object layouts (`--env.init_states=false`) |
| 6 | `pi05_ood90_randinit_s2000` | π0.5 | libero_90 | 3 / task (270) | different layouts → different failures |
| 7 | `pi0_randinit_s1000` | π0 | spatial, object, goal, 10 | 5 / task (200) | as 5, second policy (skipped, as 3) |
| 8 | `pi05_s2000`, `pi05_s3000` | π0.5 | spatial, object, goal, 10 | 10 / task each | extra seeds; least new information, so last |
| 9 | `pi05_ood90_randinit_s<seed>`, `pi05_randinit_s<seed>` | π0.5 | libero_90; spatial, object, goal, 10 | 3 / task; 5 / task | new seeds 4000, 5000, … until the budget is used |

Priorities follow information per compute unit: the monitor needs failures and varied behaviour, and the
reproduction run (1) makes every later number credible.

## Running it

*Runtime → Run all* installs everything, runs the smoke tests (cell 6) and then stops at cell 7 on purpose.
After checking cell 6, set `START_MAIN_RUNS = True` in cell 1 and fill in two numbers from Colab's Resources panel
(with the notebook connected to its A100): `CU_AVAILABLE_NOW` (`Available … compute units`) and `CU_PER_HOUR_NOW`
(`Usage rate … per hour`; `None` guesses it from the GPU type). Then run cell 1, 7 and 8. The budget is set from these
numbers; changing them later re-bases it, keeping them (for example on a restart) keeps it.

How the main runs end (cell 7 decides before each unit, from the durations of the units already finished):

* **Budget.** A unit that would not fit in the remaining budget is skipped; smaller units further down may still
  run. The budget keeps 0.75 h in reserve for the final summary and one more session's setup.
* **Colab's 12-hour session limit** (Pro and pay-as-you-go, F36). Before a unit that would not finish with 0.5 h to
  spare, the session ends cleanly; *Run all* in a new session continues where it stopped.
* **Hung runs.** A unit with no new episode for 25 min (45 min before its first) is stopped and retried once in a
  single process; three failed units in a row stop the runs.
* **Cut-off units.** After a lost runtime, a cut-off unit restarts from scratch, except a random-layout or LIBERO-90
  unit that already logged at least half of its episodes: it is skipped, because the same seed gives the same layouts
  and a re-run would mostly repeat them. Its episodes stay, flagged `partial_attempt`; for the monitor they are valid
  episodes (only the reproduction units need complete sets).

Cell 8 then writes the summary, `episodes.csv` and `bb_traces_export.zip` (traces, eval summaries, logs; no videos;
skipped when only the session limit was reached), **waits until every file has reached Google Drive**
(`drive.flush_and_unmount`) and releases the GPU. Drive uploads lag behind the writes: files not yet uploaded are lost
when the machine is released (F40). Before deleting a runtime by hand, run
`from google.colab import drive; drive.flush_and_unmount()`.

Keep the browser connected (tab open, no sleep, stable network): on 2026-10-18 a session ended after about 8 of its
12 hours, cause unknown (F42).

Robustness: every episode is written to Drive when it ends; a unit's GPU time is booked in `ledger.json` every
5 minutes; after a lost runtime, *Run all* skips finished units and handles the interrupted one as above, moving
its partial data to `…__partial_<time>` (flagged `partial_attempt` in `episodes.csv`, never mixed into a
finished unit).

Reference success rates for π0.5 on LIBERO (from LeRobot's docs, read 2026-10-17): LeRobot 97.5% average,
OpenPI 96.85% (`docs/02` F25). Our run uses `lerobot/pi05_libero_finetuned` with `--policy.n_action_steps=10`,
as in those docs.

## Output layout (Google Drive: `MyDrive/bounded-brain/libero_runs/`)

```
evals/<tag>/<suite>/eval_info.json   lerobot-eval results (+ 1 video per task)
traces/<tag>/<suite>/task_XX/<episode_id>.npz / .json
logs/<tag>__<suite>.log               full process logs
ledger.json                           per-unit status, minutes, success rate (resumability)
episodes.csv                          one row per logged episode
```

## Trace format (`format_version` 1)

Per episode, `T` = number of policy steps; snapshots are taken after reset and after every step (`T+1`).

| Array | Shape | Meaning |
|---|---|---|
| `actions` | T × 7 | action sent to the env (6-D end-effector delta + gripper) |
| `rewards`, `success` | T | env reward; LIBERO success flag after each step |
| `sim_state` | (T+1) × D | flattened MuJoCo state (`get_sim_state()`) — exact replay |
| `model_xml_gz`, `model_body_pos`, `model_body_quat` | — | the episode's model XML (gzip) and body placements; LIBERO writes fixture placements into `model.body_pos/quat` at reset, so replay needs them |
| `eef_pos`, `eef_quat`, `gripper_qpos` | (T+1) × 3/4/2 | robot state **as the policy observed it** (robosuite observables; can lag the physics by one 2 ms substep) |
| `obj_pos`, `obj_quat_wxyz` | (T+1) × N × 3/4 | object then fixture body poses (names in the JSON: `objects` + `fixtures`) |
| `goal` | (T+1) × G | truth value of each BDDL goal predicate (`goal_state` in the JSON) |
| `grasp`, `contact` | (T+1) × M | per object: robosuite `_check_grasp` (both finger pads) / any gripper contact |

The JSON holds task, language instruction, init-state id, seed, success, success step, end reason, versions
and logger error counts. `bb_replay.Replayer` restores any snapshot exactly (checked: replayed object and
fixture positions match the logged ones to 3e-8 m), so labels for new specs never require re-running the policy.

## Files

* `bb_trace.py` — monkeypatches `lerobot.envs.libero.LiberoEnv` (pinned to lerobot 0.6.1 / hf-libero 0.1.4)
* `bb_eval.py` — `lerobot-eval` with the logger on; caps videos to 1 per task (`BB_MAX_VIDEOS`)
* `bb_replay.py` — exact offline replay of a logged episode
* `bb_colab.py` — resumable units, ledger, watchdog timeout, episode index (all runs or one run tag)
* `build_notebook.py` — regenerates `libero_traces.ipynb` from the files above (edit the .py files, then rebuild)

## Known limits

* Parallel environments (`AsyncVectorEnv`) could not be tested here: they fail even without our logger in the
  agent's CPU-only sandbox. The notebook probes them on Colab and falls back to a single process.
* Rates in compute units per hour are a third-party observation (March 2026); Colab's Resources panel is authoritative,
  hence the two numbers in cell 7.
* Unit durations for the stop decisions are estimates scaled from finished units (by suite, then by tasks × step
  limit, with a safety factor); before the first LIBERO-90 unit finishes, its estimate is deliberately high.
* The session clock is the notebook kernel's start time; restarting the kernel by hand makes it start later than
  Colab's own 12-hour clock.
* The PaliGemma tokenizer repo is gated: the user must accept its license and provide `HF_TOKEN`.
