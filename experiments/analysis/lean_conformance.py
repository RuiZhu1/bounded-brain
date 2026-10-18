"""The verified Lean monitor and the Python monitor on every LIBERO episode (TODO P3-7, contribution C2).

    python experiments/analysis/lean_conformance.py export        # needs data/libero_runs
    python experiments/analysis/lean_conformance.py check [EXE]   # needs the Lean binary (lean/: lake build bbmon)

`export` writes data/analysis/lean_cases.jsonl: one line per episode with its four specs (the ones of
monitor_eval.py, with the same calibrated bounds) and its labels, one per snapshot. `check` runs
`bbmon batch` on that file, runs the Python monitor on the same input, and compares, for every
(episode, spec), the verdict and residual size after every step, the final residual and the final
answer. The result goes to experiments/analysis/results/lean_conformance.md.
"""

from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
import time
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "monitor", "src"))
from bounded_brain import Monitor, accepts, from_dict, size, to_dict  # noqa: E402

CASES = os.path.join(REPO, "data", "analysis", "lean_cases.jsonl")


def export_one(job):
    import libero_aps as L
    import monitor_eval as M

    path, bounds = job
    meta, z = L.load(path)
    ap = L.aps(meta, z)
    n = len(ap["done"])
    labels = [sorted(p for p in L.PROPS if ap[p][t]) for t in range(n)]
    specs = [to_dict(phi) for phi in M.specs(bounds).values()]
    return json.dumps({"id": meta["episode_id"], "specs": specs, "trace": labels})


def export() -> None:
    import libero_aps as L
    import monitor_eval as M

    rows = list(csv.DictReader(open(os.path.join(REPO, "data", "analysis", "features.csv"))))
    bounds = M.calibrate(rows)
    jobs = []
    for p in L.episode_paths(os.path.join(REPO, "data", "libero_runs")):
        suite = p.split(os.sep + "traces" + os.sep, 1)[1].split(os.sep)[1].split("__partial_")[0]
        jobs.append((p, bounds[suite]))
    with Pool(max(1, os.cpu_count() or 2)) as pool, open(CASES, "w") as f:
        for line in pool.imap(export_one, jobs, chunksize=16):
            f.write(line + "\n")
    print(f"{len(jobs)} episodes -> {CASES}")


def python_results(line: str):
    case = json.loads(line)
    trace = [frozenset(label) for label in case["trace"]]
    out = []
    for spec in case["specs"]:
        phi = from_dict(spec)
        m = Monitor(phi)
        verdicts, sizes = [], []
        for label in trace:
            verdicts.append(m.step(label).value)
            sizes.append(size(m.residual))
        out.append({"verdicts": verdicts, "sizes": sizes, "residual": to_dict(m.residual),
                    "accepts": accepts(phi, trace)})
    return case["id"], out


def check(exe: str) -> None:
    t0 = time.time()
    proc = subprocess.run([exe, "batch", CASES], capture_output=True, text=True, check=True)
    t_lean = time.time() - t0
    lean = {}
    for line in proc.stdout.splitlines():
        row = json.loads(line)
        lean[row["id"]] = row["results"]
    with open(CASES) as f:
        lines = f.readlines()
    t0 = time.time()
    with Pool(max(1, os.cpu_count() or 2)) as pool:
        py = dict(pool.imap(python_results, lines, chunksize=16))
    t_py = time.time() - t0
    pairs = steps = 0
    mismatches = []
    for eid, results in py.items():
        for k, (a, b) in enumerate(zip(results, lean[eid])):
            pairs += 1
            steps += len(a["verdicts"])
            if a != b:
                mismatches.append((eid, k))
    assert len(lean) == len(py), (len(lean), len(py))
    text = [
        "## Lean monitor vs Python monitor on the LIBERO episodes", "",
        f"{len(py)} episodes, {pairs} (episode, spec) pairs, {steps} monitor steps. For every pair the verdict "
        "and the residual size after every step, the final residual and the final answer were compared.", "",
        f"Mismatches: {len(mismatches)}." + (f" First: {mismatches[:5]}" if mismatches else ""), "",
        f"Time: Lean binary {t_lean:.1f} s (including JSON parsing), Python {t_py:.1f} s on {os.cpu_count()} cores.",
    ]
    out = os.path.join(HERE, "results", "lean_conformance.md")
    with open(out, "w") as f:
        f.write("\n".join(text) + "\n")
    print("\n".join(text))
    sys.exit(1 if mismatches else 0)


if __name__ == "__main__":
    if sys.argv[1:2] == ["export"]:
        export()
    elif sys.argv[1:2] == ["check"]:
        check(sys.argv[2] if len(sys.argv) > 2 else os.path.join(REPO, "lean", ".lake", "build", "bin", "bbmon"))
    else:
        print(__doc__)
        sys.exit(2)
