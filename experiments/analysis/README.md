# experiments/analysis/ — offline analysis of the LIBERO traces

Inputs: `data/libero_runs/` (the unzipped `bb_traces_export.zip` from `experiments/colab/`; `data/` is git-ignored).
Outputs: per-episode tables in `data/analysis/` (git-ignored) and summary tables in `results/` (committed).
Results and their interpretation: `docs/08-libero-results.md`.

Run in this order (Python ≥ 3.10 and numpy; about 30 s in total on two cores):

```
python experiments/analysis/libero_features.py   # data/analysis/features.csv: one row per episode, failure category
python experiments/analysis/reproduction.py      # results/reproduction.md: pi0.5 vs published success rates
python experiments/analysis/failures.py          # results/failures.md: failure categories, LIBERO-90 wrong-object check
python experiments/analysis/monitor_eval.py      # results/monitor.md: the bounded-brain monitor on every episode
python experiments/analysis/lean_conformance.py export          # data/analysis/lean_cases.jsonl
python experiments/analysis/lean_conformance.py check [BBMON]   # results/lean_conformance.md (needs `lake build bbmon`)
```

## Files

* `libero_aps.py` — atomic propositions per snapshot, from privileged simulator state: `touch`, `grasp_any`,
  `grasp_mover` (an object the task moves), `grasp_wrong` (any other object), `progress` (a goal predicate that was
  false at the start holds), `done` (all goal predicates hold), `fell`, `tipped`, `disturbed` (an object the task
  does not move fell more than 0.30 m, tilted more than 60° while not held, or moved more than 0.10 m).
* `libero_features.py` — per-episode features (first time of each proposition, gripper toggles, idle time, …) and a
  failure category: `never_touched`, `touched_no_grasp`, `wrong_object`, `mover_not_placed`, `partial_goal`
  (object tasks); `no_progress`, `partial_goal` (open/close/turn-on tasks).
* `reproduction.py`, `failures.py`, `monitor_eval.py` — the three analyses above.

## Choices that affect the numbers

* Object roles come from the BDDL goal in each episode's JSON: *movers* are the first argument of `on`/`in`;
  *targets* are other objects the goal names (`plate_1`, or `basket_1` via `basket_1_contain_region`).
* `fell`, `tipped` and `disturbed` are measured from snapshot 15 (0.75 s), not from the reset: some scenes start
  objects in mid-air (the ketchup bottle in LIVING_ROOM_SCENE1/2 drops about 0.5 m in the first 3 steps, before the
  arm can reach anything). Measured from the reset, 90 of 1169 successful reproduction episodes were flagged `fell`;
  from snapshot 15, none.
* The thresholds were checked on successful in-distribution episodes (pi05_s1000) before the monitor was run.
* Monitor bounds (`engage`, `deadline`) are calibrated on pi05_s1000 and pi05_ood90_s1000 only; those units are left
  out of the reported detection and false-alarm rates.
* All propositions use the simulator's true state (assumption A1 in `docs/04-architecture.md`); perception noise is
  not modelled here (P5-6).
