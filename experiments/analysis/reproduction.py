"""Reproduction of pi0.5's published LIBERO success rates (fixed initial states, 10 episodes per task).

    python experiments/analysis/reproduction.py

Reads data/analysis/features.csv (from libero_features.py) and writes
experiments/analysis/results/reproduction.csv and reproduction.md.

Published numbers (docs/02-facts-register.md F25): LeRobot 97.0 / 99.0 / 98.0 / 96.0 (Spatial / Object / Goal /
10, average 97.5); OpenPI 98.8 / 98.2 / 98.0 / 92.4 (average 96.85).
"""

from __future__ import annotations

import csv
import math
import os
import statistics
from collections import defaultdict

SUITES = ["libero_spatial", "libero_object", "libero_goal", "libero_10"]
LEROBOT = {"libero_spatial": 97.0, "libero_object": 99.0, "libero_goal": 98.0, "libero_10": 96.0}
OPENPI = {"libero_spatial": 98.8, "libero_object": 98.2, "libero_goal": 98.0, "libero_10": 92.4}
SEEDS = ["pi05_s1000", "pi05_s2000", "pi05_s3000"]


def wilson(k: int, n: int, z: float = 1.96) -> tuple:
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return 100 * (c - h), 100 * (c + h)


def main() -> None:
    repo = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    rows = list(csv.DictReader(open(os.path.join(repo, "data", "analysis", "features.csv"))))
    rows = [r for r in rows if r["run_tag"] in SEEDS and r["partial_attempt"] == "False"]
    k = defaultdict(int)
    n = defaultdict(int)
    for r in rows:
        n[(r["run_tag"], r["suite"])] += 1
        k[(r["run_tag"], r["suite"])] += r["success"] == "True"
    out_dir = os.path.join(repo, "experiments", "analysis", "results")
    os.makedirs(out_dir, exist_ok=True)
    table = []
    for s in SUITES + ["average"]:
        suites = SUITES if s == "average" else [s]
        per_seed = [100 * sum(k[(t, x)] for x in suites) / sum(n[(t, x)] for x in suites) for t in SEEDS]
        kk = sum(k[(t, x)] for t in SEEDS for x in suites)
        nn = sum(n[(t, x)] for t in SEEDS for x in suites)
        lo, hi = wilson(kk, nn)
        lerobot = statistics.mean(LEROBOT.values()) if s == "average" else LEROBOT[s]
        openpi = statistics.mean(OPENPI.values()) if s == "average" else OPENPI[s]
        table.append({
            "suite": s, **{t: f"{v:.1f}" for t, v in zip(SEEDS, per_seed)},
            "mean": f"{statistics.mean(per_seed):.2f}", "sd_over_seeds": f"{statistics.stdev(per_seed):.2f}",
            "successes": kk, "episodes": nn, "pooled": f"{100 * kk / nn:.2f}", "wilson95_lo": f"{lo:.1f}",
            "wilson95_hi": f"{hi:.1f}", "lerobot": f"{lerobot:.2f}", "openpi": f"{openpi:.2f}",
            "lerobot_in_ci": lo <= lerobot <= hi, "openpi_in_ci": lo <= openpi <= hi,
        })
    with open(os.path.join(out_dir, "reproduction.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(table[0].keys()))
        w.writeheader()
        w.writerows(table)
    # failed tasks
    fails = defaultdict(lambda: [0, 0])
    for r in rows:
        key = (r["suite"], int(r["task_id"]), r["language"])
        fails[key][1] += 1
        fails[key][0] += r["success"] != "True"
    lines = ["| Suite | s1000 | s2000 | s3000 | Mean ± sd (seeds) | Pooled (k/n) | 95% CI (Wilson) | LeRobot | OpenPI |",
             "|---|---|---|---|---|---|---|---|---|"]
    for t in table:
        lines.append(f"| {t['suite']} | {t['pi05_s1000']} | {t['pi05_s2000']} | {t['pi05_s3000']} | "
                     f"{t['mean']} ± {t['sd_over_seeds']} | {t['pooled']} ({t['successes']}/{t['episodes']}) | "
                     f"{t['wilson95_lo']}–{t['wilson95_hi']} | {t['lerobot']} | {t['openpi']} |")
    lines += ["", "Tasks with failures (all three seeds pooled, 30 episodes per task):", "",
              "| Suite | Task | Instruction | Failures |", "|---|---|---|---|"]
    for (s, tid, lang), (f_, n_) in sorted(fails.items(), key=lambda kv: (-kv[1][0], kv[0])):
        if f_:
            lines.append(f"| {s} | {tid} | {lang} | {f_}/{n_} |")
    with open(os.path.join(out_dir, "reproduction.md"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
