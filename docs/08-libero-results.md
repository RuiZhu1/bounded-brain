# 08 — LIBERO results: π0.5 rollouts and the first monitor evaluation

Status: first analysis, 2026-10-18. Data from the Colab runs of 2026-10-17/18 (`experiments/colab/`, F42).
Scripts and summary tables: `experiments/analysis/` (`results/*.md`). Every number below comes from those tables.

## Data

4,062 episodes of `lerobot/pi05_libero_finetuned` (LeRobot 0.6.1, `n_action_steps=10`), each with the simulator
state at every step (trace format v1), 0 logger errors. For every finished unit the success count in the traces
equals the one `lerobot-eval` reported.

| Group | Units | Episodes | Success |
|---|---|---|---|
| Reproduction: fixed initial states, 10 per task | seeds 1000, 2000, 3000 × Spatial, Object, Goal, 10 | 1,200 | 1,169 (97.4%) |
| Random layouts (`--env.init_states=false`), 5 per task | 7 seeds (4 suites; seed 9000 Spatial only) | 1,250 | 1,218 (97.4%) |
| LIBERO-90 (unseen tasks), 3 per task | 5 seeds (1 with fixed initial states), plus 258 episodes of a cut-off unit | 1,608 | 480 (29.9%) |
| Smoke tests | — | 4 | — |

LIBERO-90 counts as unseen: the checkpoint was fine-tuned on `HuggingFaceVLA/libero`, 1,693 episodes of 40 tasks
(F48), which fits the four standard suites (LIBERO-90 alone has 90 tasks). Whether any pre-training stage saw
LIBERO-90 is not documented.

## 1. Reproduction of the published success rates

Average 97.4% (1,169/1,200; Wilson 95% interval 96.4–98.2%) over three seeds, against 97.5% reported by LeRobot and
96.85% by OpenPI (F25); both lie inside our interval (F43).

| Suite | s1000 | s2000 | s3000 | Pooled | 95% CI | LeRobot | OpenPI |
|---|---|---|---|---|---|---|---|
| Spatial | 98.0 | 99.0 | 98.0 | 98.3 | 96.2–99.3 | 97.0 | 98.8 |
| Object | 100.0 | 100.0 | 99.0 | 99.7 | 98.1–99.9 | 99.0 | 98.2 |
| Goal | 97.0 | 93.0 | 96.0 | 95.3 | 92.3–97.2 | 98.0 | 98.0 |
| 10 | 94.0 | 97.0 | 98.0 | 96.3 | 93.6–97.9 | 96.0 | 92.4 |
| Average | 97.2 | 97.2 | 97.8 | 97.4 | 96.4–98.2 | 97.5 | 96.85 |

Per suite, Goal is lower than both published values (98.0 lies above our interval) and 10 is higher than OpenPI's
92.4; the intervals do not include the published runs' own sampling error. The failures concentrate on a few tasks:
"put both moka pots on the stove" (8/30), "open the top drawer and put the bowl inside" (6/30), "put the wine bottle
on top of the cabinet" (4/30).

## 2. How the policy fails

Categories from privileged state (definitions in `experiments/analysis/README.md`):

| Category | Reproduction | Random layouts | LIBERO-90 |
|---|---|---|---|
| never touched an object | 7 (23%) | 4 (12%) | 66 (6%) |
| touched, never grasped | 3 (10%) | 7 (22%) | 119 (11%) |
| grasped only objects the task does not move | 0 | 4 (12%) | 408 (36%) |
| grasped an object to move, goal unchanged | 7 (23%) | 14 (44%) | 369 (33%) |
| fixture task (open/close/turn on), no progress | 3 (10%) | 0 | 126 (11%) |
| part of the goal reached | 11 (35%) | 3 (9%) | 40 (4%) |
| **failures** | 31 | 32 | 1,128 |

On unseen tasks the most common failure is manipulating the wrong object, and it has a clear pattern (F44).
LIBERO-90 shares scenes with LIBERO-10, on which the checkpoint was fine-tuned. Of the 250 failed LIBERO-90 episodes
in such scenes that grasped an object the task does not move, 238 (95%) grasped only objects that the scene's
LIBERO-10 task moves. In 532 of the 537 failed LIBERO-90 episodes that grasped a wrong object at all, the first
grasp of the episode was already a wrong object. Examples:

* "turn off the stove" → grasps both moka pots (LIBERO-10 in this scene: "put both moka pots on the stove");
* "close the microwave" → grasps the yellow-and-white mug ("put the yellow and white mug in the microwave and
  close it");
* "pick up the tomato sauce and put it in the basket" → grasps the alphabet soup, then the cream cheese ("put both
  the alphabet soup and the cream cheese box in the basket").

The same pattern also produces "successes" with unrequested actions: in 128 successful LIBERO-90 episodes the robot
also grasped the training task's objects (e.g. picked up the bowl, then closed the drawer it was asked to close).
Success by scene family: kitchen 25%, living room 54%, study 5%.

This matches what LIBERO-PRO and LIBERO-Plus report for other VLAs (models keep executing trained behaviour when the
instruction or target changes; F46, F47). What is added here: π0.5, measured with privileged traces, and the share
of wrong grasps that the scene's training task explains.

## 3. The bounded-brain monitor on every episode

Four specs in the bounded LTLf fragment (`monitor/`), one label per snapshot (20 Hz), atoms from `libero_aps.py`:

| Spec | Formula | Meaning |
|---|---|---|
| wrong_object | G ¬grasp_wrong | never grasp an object the task does not move |
| collateral | G (¬tipped ∧ ¬fell ∧ ¬disturbed) | other objects stay upright, on their support and in place |
| engage | F[0,K_e] (grasp_mover ∨ progress) | grasp an object to move, or change a goal predicate, in time |
| deadline | F[0,K_d] done | finish in time |

K_e and K_d are 1.1 × the latest time seen in the successful episodes of the calibration units (pi05_s1000;
pi05_ood90_s1000 for LIBERO-90), capped at the step limit; for example Spatial K_e = 6.5 s, K_d = 8.7 s (limit 14 s).
The calibration units are left out of the rates below (F45).

* The monitor's verdicts equal the reference semantics (`spec.holds` on the full trace) on all 16,248
  (episode, spec) pairs; its state never exceeded 6 formula nodes. The verified Lean monitor (`lean/BBMon.lean`)
  gives the same verdict and residual after every one of the 3.67 million steps (F50).
* Held-out in-distribution episodes (reproduction seeds 2000/3000, random layouts): every failure (20/20, 32/32) is
  flagged before or at the step limit, with 1.8% and 1.2% of successes flagged. Without the deadline spec, half the
  failures are flagged early (10/20, 18/32), a median 2.1 s and 6.3 s before the limit, at about 1% of successes.
* Held-out LIBERO-90 episodes: wrong_object, collateral and engage flag 670 of 941 failures (71%), a median 15.5 s
  before the 20 s limit (77% of the episode still to run). They also flag 139 of 397 successes (35%): in 130 the
  robot grasped an object the task does not move, in the rest it moved or tipped one. These are real events in a
  successful episode (the unrequested manipulations above), not wrong verdicts.

## Limits

* All atoms come from the simulator's true state (A1, `docs/04-architecture.md`); perception is not modelled (P5-6).
* "Lead" is time before the step limit, not before the failure became irreversible. The deadline spec flags every
  failure by construction; its value is only its lead time, which is near zero when K_d is near the limit.
* Few in-distribution failures (52 held out), so those rates are rough.
* One checkpoint, one benchmark, simulation only.
