# 00 — Context and history

Written 2026-10-17 from the founding conversation. Purpose: give a fresh agent the background without
making it re-derive it, including what was *corrected* along the way.

## Who and why

The owner (see `CLAUDE.md`) wants to build something real in robot learning that uses a strong
mathematical/theory background. The project is deliberately framed as a **research question**, not as a
competition with any company.

## How the idea evolved (and what was corrected)

1. **Initial idea:** use computability theory (primitive recursion, Turing machines) to "optimize robot
   brains". *Assessment:* these concepts describe what is computable; modern robot policies (Transformers +
   diffusion/flow heads) are already computable functions, so they do not add capability.
2. **A pasted third-party message** claimed that primitive recursion guarantees physical safety, that an
   "Embodied Turing Machine" approach needs 1/1000 of the compute and beats VLA models by 38.9%. *Assessment:*
   one real paper exists (arXiv 2610.12369, code-as-policy with a Turing-machine *framing*); the rest is
   unsupported or a category error. See facts register F6, F7, D1–D5.
3. **Reframing that survived scrutiny:** a **verified runtime monitor / safety layer** for robot foundation
   models. Real literature already covers *continuous* constraints (CBF/ATACOM filters on VLAs). The plausible gap
   is the **discrete, temporal, task-level** layer with **machine-checked** correctness. Whether that gap is real
   is exactly what Phase 1 must establish (Gate G1).
4. **Course relevance corrected:** the course gives *tools for thinking about bounded computation and
   limits* (see `05-course-mapping.md`), not robot capability. Automata and temporal logic — the actually
   relevant theory — are mostly **outside** the course and must be learned separately.

## Landscape snapshot (web search, 2026-10-17; details in `03-related-work.md`)

* Robot foundation-model companies (Physical Intelligence, Skild AI, Generalist) publish models and funding
  news; **no public formal-verification work from them was found** (absence of evidence only).
* Academic work on safety layers for VLAs is active and crowded for continuous constraints (CBF filters,
  ATACOM). Temporal-logic *evaluation* exists (SENTINEL). A machine-checked *runtime monitor* in a proof
  assistant for VLA pipelines was **not found** in the searches done — not proof that none exists.

## Constraints and unknowns

* Owner is a PhD student with an unrelated thesis topic: time is the scarcest resource. See `TODO.md` §0 (Q2).
* Hardware (robot, GPU) unknown (Q1). Plan assumes **simulation first**.
* Lean experience: none assumed (Q6).
