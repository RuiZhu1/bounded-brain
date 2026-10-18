# CLAUDE.md — working agreements for coding agents

Read this file first, then `README.md`, `TODO.md`, and `docs/02-facts-register.md`.

## Project in one line

Verified (Lean 4), bounded runtime monitors for a finite-trace temporal-logic fragment, integrated with
open-source robot foundation models (π0 via LeRobot) and a continuous safety filter, evaluated in simulation.

## The owner

Rui Zhu, the sole author. Strong in math and programming; **new to robot learning and to Lean** (Q6). Follows a
Theory of Computation course this semester (primitive recursion, minimisation, coding, Turing machines,
computability, then complexity; mapping in `docs/05`). Works alone; no robot arm and no local GPU; Google Colab is
available (`TODO.md` §0). Personal and institutional context is kept out of the public repository: it lives in
`private/` on the owner's machine (git-ignored). Read it there when it matters; never copy it into tracked files.

* Talk to the owner in **Chinese**. Repository artifacts (code, docs, commits, paper) are in **English**.
* Treat the owner as a capable adult: be direct about what will and will not work.

## Ground rules

1. **Epistemic discipline.** Every factual claim in `docs/` carries a status in
   `docs/02-facts-register.md`: `VERIFIED-READ` (full text read), `VERIFIED-SNIPPET` (search snippet
   only), `SECONDARY`, `MEMORY` (recalled, not checked), `UNVERIFIED`, `DEBUNKED`. Never upgrade a status
   without actually checking. Before adding a citation to `paper/refs.bib`, confirm that the arXiv ID
   resolves and the authors/title match; otherwise add `% UNVERIFIED`. Never invent numbers, dates or venues.
2. **Claims discipline.** Forbidden in any document: "provably safe", "guarantees safety", "beats π0 / any
   named system", "solves". Allowed form: *"Under assumptions A1–A4, the monitor's verdict is correct with
   respect to the LTLf semantics (machine-checked in Lean)."*
3. **Do not rebuild the project around the origin myth.** The project began from a pasted third-party message
   claiming primitive recursion/Turing machines give robots safety, 1000× less compute, and a 38.9% win. Those
   claims are catalogued as `DEBUNKED`/`UNVERIFIED` in the facts register (D1–D5, F7). Termination is not
   safety; the Turing-machine framing in the cited paper is a metaphor for "explicit state + explicit rules".
4. **Scope control.** Discrete layer first. Do not try to verify neural networks. Do not formalize continuous
   dynamics in Lean unless Gate G1 explicitly widens the scope.
5. **Neutral public tone.** The repository is public. No adversarial framing toward any company or person.
   π0 is a base we build on (open weights), not a target. No personal or institutional details (affiliation,
   advisor, time budget, policy questions) in tracked files: those go to `private/`.
6. **Ask only what you cannot verify.** If a question is answerable from the repo, the web, or the machine,
   do that instead. Genuinely blocking questions are listed in `TODO.md` §0; batch them into one message.
7. **Stuck rule.** After three failed attempts at the same blocker, stop and report what you tried.
8. **Keep docs and code in the same change.** Update `TODO.md` checkboxes, `docs/02`, and `docs/07`
   whenever you do work that affects them.

## Lean rules

* `lake build` must pass. `sorry` only when tracked by a TODO ID in the docstring. No `axiom`.
* Keep the core free of Mathlib unless a task needs it; record the decision in `docs/07`.
* Toolchain pinned in `lean/lean-toolchain` (Lean v4.35.0, D-012). `lake build` is green with no
  warnings (all stated theorems proved, 2026-10-18).
* Python and Lean simplification rules must stay identical (TT/FF absorption only, no deduplication).
  `monitor/tests/test_lean_conformance.py` checks this against the Lean binary (`cd lean && lake build bbmon`).

## Python rules

* Python ≥ 3.10 (the agent's device VM has 3.10.12 and `uv`; the owner's own setup is unknown). The monitor package has **no runtime
  dependencies** on purpose.
* Tests are small-scope exhaustive plus (to be added) Hypothesis. A change to `progress` or `holds` must keep
  `monitor/tests` green and must be mirrored in Lean.

## Git and files

* **Never commit or push unless the owner asks.** The repository is public:
  `https://github.com/RuiZhu1/bounded-brain`, branch `main` (first push 2026-10-18).
* Commit identity (repo-local `.git/config`): `Rui Zhu <327512019+RuiZhu1@users.noreply.github.com>`, GitHub's
  no-reply address for the owner's account, so no personal email appears in the public history.
* CI (`.github/workflows/ci.yml`) runs on every push. Keep it green; `make ci` runs the same checks locally.
* Never commit: course PDFs (instructor's material) or solutions to course exercises, model weights, datasets,
  `.env`/secrets, build output, `private/`. The `.gitignore` already covers these; do not weaken it.
* Small, conventional commits ("feat(lean): …", "test(monitor): …") when asked to commit.

## Environment gotchas (as of 2026-10-17)

* **The agent's device shell is not the owner's system.** It is an isolated VM (Ubuntu 22.04, 2 vCPU, 3.8 GiB RAM,
  ~9 GB free disk) that mounts only this folder. Tools found there (Python 3.10.12, `uv`, Node, `pdflatex` +
  `latexmk`, git, curl, zstd; no `gh`) describe the VM. Anything installed outside the mounted folder is
  per-session and invisible to the owner. The owner's own system has not been inspected.
* **Lean in agent sandboxes.** elan downloads toolchains from `release.lean-lang.org` (facts F22), which is not
  allow-listed, so `elan toolchain install` fails there. Lean releases are also published as GitHub release assets
  (allow-listed). What worked on 2026-10-17 in the cloud sandbox: run `elan-init.sh` from
  `https://raw.githubusercontent.com/leanprover/elan/master/` with `-y --default-toolchain none`, download
  `lean-4.35.0-linux.tar.zst` from the `v4.35.0` GitHub release, check its sha256 against the releases API (F21),
  and unpack it as `~/.elan/toolchains/leanprover--lean4---v4.35.0` (~3 GB). The owner installs Lean the normal
  way (`lean/README.md`).
* Shell access to the owner's folder is sandboxed; **deleting files is not permitted by default** (request
  permission once if truly needed). A plain `git status` can leave a stale `.git/index.lock` that it then
  cannot remove; use `GIT_OPTIONAL_LOCKS=0 git status` for read-only checks. (Two stale empty locks were moved
  aside to `.git/index.lock.stale-from-probe` and `.git/index.lock.stale-from-probe-2`; both are safe to delete
  by hand.)
* Outbound network from the agent's sandbox is allow-listed (package registries, GitHub). Do not work around refusals.
* **Cloud containers are reset between sessions** (2026-10-18): earlier working copies and the Lean install were gone.
  The owner's folder and GitHub are the sources of truth. A fresh container had no `zstd`; the Lean tarball was
  unpacked with Python's `zstandard` instead. The GitHub API (`gh`) only reaches repositories attached to the session.
* **Writing files to the owner's folder from the cloud sandbox:** on 2026-10-18 `device_commit_files` wrote an older
  copy when the same staged path was committed a second time. Stage each version under a new name and check the
  md5 on the device after writing.
* **Hugging Face is not reachable from either sandbox** (cloud or device VM): policy weights cannot be loaded there.
  LIBERO's assets are also in the LIBERO GitHub repo (405 MB). In the CPU-only cloud sandbox LIBERO runs with Mesa
  EGL, but `AsyncVectorEnv` workers die even without our logger. The Colab kit was tested there with a random-weight
  ACT policy; the real checkpoints are first loaded on Colab.

## Definition of done (any task)

Tests/builds pass · docs and TODO updated · facts register updated for any new fact · no forbidden claims ·
a short note to the owner (Chinese) saying what changed and what is next.
