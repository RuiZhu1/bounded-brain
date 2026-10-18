# Runbook 00 — environment setup

Status: **outline only; every command must be verified when first run.** Record what actually worked.

## Machines (as of 2026-10-17)

* **Owner's own system:** not inspected by an agent. No local GPU (owner, Q1).
* **Compute for Phase 5:** Google Colab with an A100 (owner, Q1).
* **Agent's device VM** (only this folder is mounted): Python 3.10.12, `uv`, Node, `pdflatex`/`latexmk`; no `gh`.

## Steps

1. **Monitor tests:** `cd monitor && python3 -m pytest -q` (or `uv run --with pytest pytest`).
2. **Lean:** install `elan`, then `cd lean && lake build`; exact commands in `lean/README.md` (toolchain pinned
   to v4.35.0).
3. **LeRobot + π0 (Phase 5):** follow the official LeRobot README (`https://github.com/huggingface/lerobot`);
   do not guess versions: copy the install commands from the README at the time you run them and note the commit.
4. **Benchmark:** after P1-7, add its install steps here (source, license, version/commit).
5. **GPU check:** record `nvidia-smi` output in `runbooks/hardware.md`. For reference, the ATACOM paper fine-tuned
   π0 on a single A100 (10k steps, batch 32).

## Reproducibility notes

Pin versions (Lean toolchain, Python packages, LeRobot commit, benchmark commit). Record seeds in every config.
