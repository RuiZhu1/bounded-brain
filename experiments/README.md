# experiments/

This folder holds the protocol, configs and runbooks for Phase 5. `colab/` collected 4,062 LIBERO episodes of π0.5
with privileged traces (TODO P5-0); `analysis/` turns them into the results in `../docs/08-libero-results.md`.

## Protocol (draft)

* **Systems compared:** (1) raw VLA; (2) VLA + continuous filter (ATACOM/CBF-style); (3) (2) + monitor, detect-only;
  (4) (2) + monitor, enforcement.
* **Base model:** π0 open weights through LeRobot (`github.com/huggingface/lerobot`). Reproduce one published
  number before trusting the pipeline (TODO P5-1).
* **Benchmark:** decide in P1-7 (SafeLIBERO appeared in a search snippet only; LIBERO/LeRobot sim as fallback).
* **Specs:** the library from TODO P2-5 (each spec has a natural-language description and positive/negative traces).
* **Labels:** privileged simulator state first, perceived labels second; the gap between them is an ablation (P5-6).
* **Metrics:** task success; task-level violation rate per spec; geometric violation rate; intervention rate;
  monitor latency (µs/step); episode time.
* **Statistics:** fixed seeds, ≥ N episodes per condition (decide N with the owner's compute), report confidence
  intervals, publish all episodes (no cherry-picking).
* **Logging:** per-episode JSONL traces in the interchange format of `../docs/04-architecture.md`.

## Layout

```
configs/    one YAML per experiment condition (not created yet)
runbooks/   step-by-step setup notes, e.g. 00-env-setup.md
```

Large artifacts (weights, datasets, videos) are git-ignored; document how to fetch them instead.
