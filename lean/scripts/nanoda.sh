#!/usr/bin/env bash
# Re-check the whole BoundedBrain library with nanoda, an independent Lean 4 type checker written in Rust
# (https://github.com/ammkrn/nanoda_lib), so the proofs do not rest on Lean's own kernel alone.
#
#   cd lean && lake build && bash scripts/nanoda.sh     # needs git, Rust (cargo) and about 2 GB of free disk
#
# Steps: export the library and everything it depends on with lean4export (the release tagged like our
# toolchain), then type-check every exported declaration with nanoda. Only Lean's standard axioms are permitted,
# plus `Lean.trustCompiler`, which parts of Lean's core library use; `sorryAx` is not, so a `sorry` fails the check.
# Adapted from leanprover/lean-action's run_nanoda.sh (v1.6.2), with the tool versions pinned here.
set -euo pipefail

MODULE=BoundedBrain
NANODA_REPO=https://github.com/ammkrn/nanoda_lib.git
NANODA_SHA=f67473ba5f9397266f89c7852082c9c914b5d219   # master on 2026-10-15; reads lean4export format 3.x
LEAN_VERSION="$(cut -d: -f2 lean-toolchain)"           # lean4export publishes a tag per Lean release

command -v cargo >/dev/null || { echo "nanoda needs Rust: install cargo (https://rustup.rs) and retry" >&2; exit 1; }

WORK="$(mktemp -d "${RUNNER_TEMP:-/tmp}/nanoda.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT

echo "::group::Build lean4export $LEAN_VERSION"
git clone -q --depth 1 --branch "$LEAN_VERSION" https://github.com/leanprover/lean4export.git "$WORK/lean4export"
cp lean-toolchain "$WORK/lean4export/"
(cd "$WORK/lean4export" && lake build)
echo "::endgroup::"

echo "::group::Build nanoda ${NANODA_SHA:0:12}"
git init -q "$WORK/nanoda"
git -C "$WORK/nanoda" fetch -q --depth 1 "$NANODA_REPO" "$NANODA_SHA"
git -C "$WORK/nanoda" checkout -q FETCH_HEAD
(cd "$WORK/nanoda" && cargo build --release --locked)
echo "::endgroup::"

echo "Exporting $MODULE ..."
lake env "$WORK/lean4export/.lake/build/bin/lean4export" "$MODULE" > "$WORK/export.ndjson"
echo "export: $(wc -l < "$WORK/export.ndjson") lines"

cat > "$WORK/config.json" <<EOF
{
  "export_file_path": "$WORK/export.ndjson",
  "use_stdin": false,
  "permitted_axioms": ["propext", "Classical.choice", "Quot.sound", "Lean.trustCompiler"],
  "unpermitted_axiom_hard_error": false,
  "nat_extension": true,
  "string_extension": true,
  "print_success_message": true
}
EOF

echo "Type-checking with nanoda ..."
"$WORK/nanoda/target/release/nanoda_bin" "$WORK/config.json"
