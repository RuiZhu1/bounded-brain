# Local versions of the CI checks (.github/workflows/ci.yml). `make help` lists them.
.PHONY: help test lint lean nanoda conformance notebook paper ci clean

PYTHON ?= python3

help:
	@echo "make test         Python monitor tests (no Lean needed)"
	@echo "make lint         ruff with the pinned rule set (ruff.toml, monitor/pyproject.toml)"
	@echo "make lean         lake build --wfail, leanchecker, lean/Checks.lean (statements and axioms)"
	@echo "make nanoda       re-check the library with the nanoda type checker (needs Rust)"
	@echo "make conformance  build bbmon and compare the Lean and Python monitors"
	@echo "make notebook     check that the Colab notebook is in sync with its kit"
	@echo "make paper        latexmk build of paper/main.tex into paper/build/"
	@echo "make ci           everything above except nanoda"
	@echo "make clean        remove build output (paper/build, lean/.lake)"

test:
	cd monitor && $(PYTHON) -m pytest -q

lint:
	ruff check .
	$(PYTHON) -m compileall -q experiments monitor

lean:
	cd lean && lake build --wfail && lake env leanchecker && lake env lean Checks.lean

nanoda: lean
	cd lean && bash scripts/nanoda.sh

conformance:
	cd lean && lake build --wfail bbmon
	cd monitor && BB_REQUIRE_LEAN=1 $(PYTHON) -m pytest -q tests/test_lean_conformance.py

notebook:
	$(PYTHON) experiments/colab/build_notebook.py
	git diff --exit-code -- experiments/colab/libero_traces.ipynb

paper:
	cd paper && latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build main.tex

ci: lint test lean conformance notebook paper

clean:
	rm -rf paper/build lean/.lake
