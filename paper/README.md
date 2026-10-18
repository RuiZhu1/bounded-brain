# paper/

LaTeX skeleton (`main.tex`) and bibliography (`refs.bib`).

* Build: `cd paper && latexmk -pdf -outdir=build main.tex` (needs `latexmk` + a TeX distribution; the owner's
  machine has both; the skeleton compiled in the scaffolding environment).
* Build output goes to `paper/build/` (git-ignored).
* `refs.bib` contains only entries whose metadata was checked; others carry `UNVERIFIED`.
* Every claim in the paper must appear in the claims table (TODO P7-1) with its evidence file.
* Remove the temporary `\nocite{*}` once real citations exist.
