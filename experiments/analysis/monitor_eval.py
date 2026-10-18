"""Run the bounded-brain monitor (monitor/src/bounded_brain) over every LIBERO episode.

    python experiments/analysis/monitor_eval.py

Reads data/analysis/features.csv and the traces in data/libero_runs; writes
data/analysis/monitor_verdicts.csv (one row per episode and spec) and experiments/analysis/results/monitor.md.

Specs (bounded LTLf, atomic propositions from libero_aps.py, one label per snapshot at 20 Hz):
  wrong_object  G !grasp_wrong                            never grasp an object the task does not move
  collateral    G (!tipped & !fell & !disturbed)          other objects stay upright, on their support, in place
  engage        F[0,K_e] (grasp_mover | progress)          grasp an object to move, or change a goal predicate, in time
  deadline      F[0,K_d] done                              finish in time

K_e and K_d are set per suite to 1.1 x the latest time seen in the *calibration* units (successful episodes of
pi05_s1000 for the four fine-tuning suites, of pi05_ood90_s1000 for LIBERO-90), capped at the step limit. Those
units are excluded from the evaluation below. A spec violated during a failed episode is a detection; the lead
time is the time between the verdict and the end of the episode (the step limit). A violation during a successful
episode is reported separately: for wrong_object and collateral it is a real event in a successful episode, for
engage and deadline it is a false alarm.

Every final verdict is also checked against the reference semantics `spec.holds` on the full trace.
"""

from __future__ import annotations

import csv
import math
import os
import statistics
import sys
from collections import defaultdict
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "monitor", "src"))
import libero_aps as L  # noqa: E402
from bounded_brain import (And, Always, EventuallyWithin, Monitor, Or, Verdict, atom, holds,  # noqa: E402
                           not_atom, size)

HZ = 20
CALIBRATION = {"pi05_s1000", "pi05_ood90_s1000"}
SPECS = ("wrong_object", "collateral", "engage", "deadline")
COMBOS = {"early (all but deadline)": ("wrong_object", "collateral", "engage"), "any": SPECS}


def calibrate(rows):
    """Per-suite bounds from the calibration units' successful episodes."""
    late = defaultdict(lambda: {"engage": 0, "deadline": 0})
    cap = {}
    for r in rows:
        if r["run_tag"] not in CALIBRATION or r["success"] != "True":
            continue
        s = r["suite"]
        firsts = [int(r[k]) for k in ("first_grasp_mover", "first_progress") if int(r[k]) >= 0]
        late[s]["engage"] = max(late[s]["engage"], min(firsts))
        late[s]["deadline"] = max(late[s]["deadline"], int(r["first_done"]))
        cap[s] = int(r["max_steps"])
    return {s: {k: min(cap[s], math.ceil(1.1 * v)) for k, v in d.items()} for s, d in late.items()}


def specs(bounds):
    return {
        "wrong_object": Always(not_atom("grasp_wrong")),
        "collateral": Always(And(not_atom("tipped"), And(not_atom("fell"), not_atom("disturbed")))),
        "engage": EventuallyWithin(bounds["engage"], Or(atom("grasp_mover"), atom("progress"))),
        "deadline": EventuallyWithin(bounds["deadline"], atom("done")),
    }


def evaluate(job):
    path, bounds = job
    meta, z = L.load(path)
    ap = L.aps(meta, z)
    n = len(ap["done"])
    trace = [frozenset(p for p in L.PROPS if ap[p][t]) for t in range(n)]
    out = []
    for name, phi in specs(bounds).items():
        mon = Monitor(phi)
        t_viol, peak = -1, size(phi)
        for t, label in enumerate(trace):
            v = mon.step(label)
            peak = max(peak, size(mon.residual))
            if v is Verdict.VIOLATED:
                t_viol = t
                break
        final = mon.finish() if t_viol < 0 else False
        out.append({"episode_id": meta["episode_id"], "spec": name, "violated_at": t_viol,
                    "snapshots": n, "final_ok": final, "oracle_ok": holds(trace, 0, phi), "peak_size": peak})
    return out


def med(v):
    """Median of snapshot counts, in seconds."""
    return f"{statistics.median(v) / HZ:.1f} s" if v else "—"


def main() -> None:
    rows = list(csv.DictReader(open(os.path.join(REPO, "data", "analysis", "features.csv"))))
    by_id = {r["episode_id"]: r for r in rows}
    bounds = calibrate(rows)
    paths = L.episode_paths(os.path.join(REPO, "data", "libero_runs"))
    jobs = []
    for p in paths:
        suite = p.split(os.sep + "traces" + os.sep, 1)[1].split(os.sep)[1].split("__partial_")[0]
        jobs.append((p, bounds[suite]))
    with Pool(max(1, (os.cpu_count() or 2))) as pool:
        results = [r for chunk in pool.imap_unordered(evaluate, jobs, chunksize=8) for r in chunk]
    with open(os.path.join(REPO, "data", "analysis", "monitor_verdicts.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        w.writeheader()
        w.writerows(results)

    agree = sum(r["final_ok"] == r["oracle_ok"] for r in results)
    peak = defaultdict(int)
    for r in results:
        peak[r["spec"]] = max(peak[r["spec"]], r["peak_size"])
    out = ["## Specs and bounds", "",
           "| Suite | K_e (engage) | K_d (deadline) | Step limit |", "|---|---|---|---|"]
    for s in sorted(bounds):
        cap = next(int(r["max_steps"]) for r in rows if r["suite"] == s)
        out.append(f"| {s} | {bounds[s]['engage']} ({bounds[s]['engage'] / HZ:.1f} s) | "
                   f"{bounds[s]['deadline']} ({bounds[s]['deadline'] / HZ:.1f} s) | {cap} ({cap / HZ:.0f} s) |")
    out += ["", f"Monitor verdict = reference semantics on {agree}/{len(results)} (episode, spec) pairs. "
            "Largest monitor state (formula nodes): " + ", ".join(f"{k} {v}" for k, v in peak.items()) + ".", ""]

    groups = ["reproduction", "randinit", "ood90"]
    out += ["## Held-out episodes (calibration units excluded)", "",
            "Failed episodes: share with a violation, median time of the verdict and median lead time before the step "
            "limit. Successful episodes: share with a violation before success.", "",
            "| Spec | Group | Failures flagged | Verdict at (median) | Lead (median) | Episode left (median) | Successes flagged |",
            "|---|---|---|---|---|---|---|"]
    per_ep = defaultdict(dict)
    for r in results:
        per_ep[r["episode_id"]][r["spec"]] = r
    for spec in SPECS + tuple(COMBOS):
        for g in groups:
            fail_t, lead, left, n_fail, n_succ, succ_flag = [], [], [], 0, 0, 0
            for eid, d in per_ep.items():
                row = by_id[eid]
                if row["group"] != g or row["run_tag"] in CALIBRATION:
                    continue
                specs_here = COMBOS.get(spec, (spec,))
                ts = [d[s]["violated_at"] for s in specs_here if d[s]["violated_at"] >= 0]
                t = min(ts) if ts else -1
                if row["success"] == "True":
                    n_succ += 1
                    succ_flag += t >= 0
                else:
                    n_fail += 1
                    if t >= 0:
                        last = d[SPECS[0]]["snapshots"] - 1
                        fail_t.append(t)
                        lead.append(last - t)
                        left.append(100 * (last - t) / last)
            left_s = f"{statistics.median(left):.0f}%" if left else "—"
            out.append(f"| {spec} | {g} | {len(fail_t)}/{n_fail} ({100 * len(fail_t) / max(1, n_fail):.0f}%) | "
                       f"{med(fail_t)} | {med(lead)} | {left_s} | {succ_flag}/{n_succ} "
                       f"({100 * succ_flag / max(1, n_succ):.1f}%) |")
    res = os.path.join(REPO, "experiments", "analysis", "results")
    os.makedirs(res, exist_ok=True)
    with open(os.path.join(res, "monitor.md"), "w") as f:
        f.write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
