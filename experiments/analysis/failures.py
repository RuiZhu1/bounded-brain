"""Failure taxonomy for the LIBERO runs, and a check of the "wrong object" failures on unseen LIBERO-90 tasks.

    python experiments/analysis/failures.py

Reads data/analysis/features.csv (libero_features.py) and the traces in data/libero_runs; writes
experiments/analysis/results/failures.md.

The check: LIBERO-90 shares scenes with LIBERO-10, on which the checkpoint was fine-tuned. For an unseen task
whose episode grasped an object the task does not move, we ask whether every grasped object is one that a
LIBERO-10 task *in the same scene* moves, i.e. whether the policy behaved as in its training task for that scene.
"""

from __future__ import annotations

import csv
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import libero_aps as L  # noqa: E402

GROUPS = ["reproduction", "randinit", "ood90"]
CATS = ["never_touched", "touched_no_grasp", "wrong_object", "mover_not_placed", "no_progress", "partial_goal"]
SCENE = re.compile(r"^([A-Z_]+_SCENE\d+)_")


def main() -> None:
    repo = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    root = os.path.join(repo, "data", "libero_runs")
    rows = list(csv.DictReader(open(os.path.join(repo, "data", "analysis", "features.csv"))))
    by_id = {r["episode_id"]: r for r in rows}
    out = []

    # 1. categories
    out += ["## Failure categories", "", "| Category | " + " | ".join(GROUPS) + " |", "|---|" + "---|" * len(GROUPS)]
    fails = {g: [r for r in rows if r["group"] == g and r["success"] != "True"] for g in GROUPS}
    for c in CATS:
        cells = []
        for g in GROUPS:
            k = sum(r["category"] == c for r in fails[g])
            cells.append(f"{k} ({100 * k / max(1, len(fails[g])):.0f}%)")
        out.append(f"| {c} | " + " | ".join(cells) + " |")
    out.append("| **failures / episodes** | " + " | ".join(
        f"{len(fails[g])} / {sum(r['group'] == g for r in rows)}" for g in GROUPS) + " |")

    # 2. unseen tasks by scene family
    fam = defaultdict(lambda: [0, 0])
    for r in rows:
        if r["group"] == "ood90":
            f = r["task_name"].split("_SCENE")[0]
            fam[f][0] += r["success"] == "True"
            fam[f][1] += 1
    out += ["", "## LIBERO-90 (unseen tasks): success by scene family", "", "| Scene family | Success |", "|---|---|"]
    for f, (k, n) in sorted(fam.items()):
        out.append(f"| {f} | {k}/{n} ({100 * k / n:.0f}%) |")

    # 3. wrong-object grasps vs the training task of the same scene
    trained = defaultdict(set)  # scene -> objects moved by a LIBERO-10 task in that scene
    trained_tasks = defaultdict(set)
    paths = L.episode_paths(root)
    for p in paths:
        if "/pi05_s1000/libero_10/" not in p:
            continue
        meta, _ = L.load(p)
        m = SCENE.match(meta["task_name"])
        if m:
            trained[m.group(1)].update(L.roles(meta)[0])
            trained_tasks[m.group(1)].add(meta["language"])
    stats = Counter()
    examples = {}
    first_wrong = Counter()  # failed episodes with a wrong grasp: was the episode's first grasp already wrong?
    for p in paths:
        if "/pi05_ood90_" not in p:
            continue
        meta, z = L.load(p)
        r = by_id[meta["episode_id"]]
        if int(r["first_grasp_wrong"]) < 0:
            continue
        m = SCENE.match(meta["task_name"])
        scene = m.group(1) if m else "?"
        movers = set(L.roles(meta)[0])
        grasped = {o for k, o in enumerate(meta["objects"]) if z["grasp"][:, k].any()}
        if r["success"] != "True":
            first_wrong[int(r["first_grasp_wrong"]) == int(r["first_grasp_any"])] += 1
        wrong = grasped - movers
        key = "success" if r["success"] == "True" else "failure"
        if scene not in trained:
            stats[(key, "no_scene")] += 1
        elif wrong <= trained[scene]:
            stats[(key, "explained")] += 1
            examples.setdefault(meta["task_name"], (meta["language"], sorted(wrong), sorted(trained_tasks[scene])))
        else:
            stats[(key, "other")] += 1
    out += ["", "## LIBERO-90 episodes that grasped an object the task does not move", "",
            "| Outcome | Wrong grasps explained by the same scene's LIBERO-10 task | Other objects | Scene not in LIBERO-10 |",
            "|---|---|---|---|"]
    for key in ("failure", "success"):
        out.append(f"| {key} | {stats[(key, 'explained')]} | {stats[(key, 'other')]} | {stats[(key, 'no_scene')]} |")
    out += ["", f"In {first_wrong[True]} of these {sum(first_wrong.values())} failed episodes the first grasp of the "
            "episode was already a wrong one.", "",
            "Examples (instruction → objects grasped instead; the LIBERO-10 task(s) of that scene):", ""]
    for t, (lang, wrong, tasks) in sorted(examples.items())[:12]:
        trained_str = "; ".join('"' + x + '"' for x in tasks)
        out.append('* "' + lang + '" → ' + ", ".join(wrong) + "; trained: " + trained_str)

    # 4. unseen tasks with the most failures
    per_task = defaultdict(Counter)
    for r in rows:
        if r["group"] == "ood90":
            per_task[r["language"]][r["category"]] += 1
    out += ["", "## LIBERO-90 tasks never solved (all episodes failed)", "", "| Instruction | Episodes | Main category |",
            "|---|---|---|"]
    for lang, c in sorted(per_task.items(), key=lambda kv: (-sum(v for k, v in kv[1].items() if k != "success"), kv[0])):
        if c["success"] == 0:
            main_cat, _ = c.most_common(1)[0]
            out.append(f"| {lang} | {sum(c.values())} | {main_cat} |")
    res = os.path.join(repo, "experiments", "analysis", "results")
    os.makedirs(res, exist_ok=True)
    with open(os.path.join(res, "failures.md"), "w") as f:
        f.write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
