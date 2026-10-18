import Lean.Data.Json
import BoundedBrain

/-
  bbmon — run the verified monitor (`BoundedBrain.progress`, `run`, `accepts`) on JSON input (TODO P3-7).

  Used for differential testing against the Python monitor (monitor/tests/test_lean_conformance.py,
  experiments/analysis/lean_conformance.py). Formulas use the JSON form of `spec.to_dict` in Python:
  {"op": "tt" | "ff" | "lit" | "and" | "or" | "next" | "pending" | "always" | "always_within" |
  "eventually_within", ...}. A trace is a list of labels; a label is the list of atom names that hold.

    lake exe bbmon batch CASES.jsonl
        one JSON object per line, {"id": ..., "specs": [F, ...], "trace": [[...], ...]};
        prints one line per case, {"id": ..., "results": [R, ...]}
    lake exe bbmon run SPEC.json TRACE.jsonl
        TRACE.jsonl has one label (JSON list of atom names) per line;
        prints the verdict after every step, then the final answer

  R = {"verdicts": [...], "sizes": [...], "residual": F, "accepts": bool}: the verdict ("pending",
  "satisfied", "violated") and residual size after each step, the final residual, and `accepts`.

  This file only parses and prints; the monitor functions are the ones proved correct in
  BoundedBrain/Monitor.lean. The parser is not verified.
-/

open Lean (Json FromJson ToJson toJson)
open BoundedBrain

namespace BBMon

partial def formulaOfJson (j : Json) : Except String (Formula String) := do
  let op ← j.getObjValAs? String "op"
  let sub (key : String) : Except String (Formula String) := do formulaOfJson (← j.getObjVal? key)
  match op with
  | "tt" => pure .tt
  | "ff" => pure .ff
  | "lit" =>
    let positive := (j.getObjValAs? Bool "positive").toOption.getD true
    pure (.lit (← j.getObjValAs? String "name") positive)
  | "and" => pure (.conj (← sub "left") (← sub "right"))
  | "or" => pure (.disj (← sub "left") (← sub "right"))
  | "next" => pure (.next (← sub "arg"))
  | "pending" => pure (.pending (← sub "arg"))
  | "always" => pure (.always (← sub "arg"))
  | "always_within" => pure (.alwaysWithin (← j.getObjValAs? Nat "bound") (← sub "arg"))
  | "eventually_within" => pure (.eventuallyWithin (← j.getObjValAs? Nat "bound") (← sub "arg"))
  | other => throw s!"unknown op: {other}"

def formulaToJson : Formula String → Json
  | .tt => Json.mkObj [("op", "tt")]
  | .ff => Json.mkObj [("op", "ff")]
  | .lit p b => Json.mkObj [("op", "lit"), ("name", Json.str p), ("positive", Json.bool b)]
  | .conj a b => Json.mkObj [("op", "and"), ("left", formulaToJson a), ("right", formulaToJson b)]
  | .disj a b => Json.mkObj [("op", "or"), ("left", formulaToJson a), ("right", formulaToJson b)]
  | .next a => Json.mkObj [("op", "next"), ("arg", formulaToJson a)]
  | .pending a => Json.mkObj [("op", "pending"), ("arg", formulaToJson a)]
  | .always a => Json.mkObj [("op", "always"), ("arg", formulaToJson a)]
  | .alwaysWithin k a => Json.mkObj [("op", "always_within"), ("bound", toJson k), ("arg", formulaToJson a)]
  | .eventuallyWithin k a => Json.mkObj [("op", "eventually_within"), ("bound", toJson k), ("arg", formulaToJson a)]

/-- A label from the list of atoms that hold. -/
def labelOf (atoms : Array String) : Label String := fun p => atoms.contains p

def verdictName : Formula String → String
  | .tt => "satisfied"
  | .ff => "violated"
  | _ => "pending"

/-- Verdict and residual size after every step, plus the final residual and `accepts`. -/
def monitorJson (spec : Formula String) (trace : List (Label String)) : Json := Id.run do
  let mut residual := spec
  let mut verdicts : Array Json := #[]
  let mut sizes : Array Json := #[]
  for σ in trace do
    residual := progress σ residual
    verdicts := verdicts.push (Json.str (verdictName residual))
    sizes := sizes.push (toJson residual.size)
  Json.mkObj [("verdicts", Json.arr verdicts), ("sizes", Json.arr sizes),
              ("residual", formulaToJson (run spec trace)), ("accepts", Json.bool (accepts spec trace))]

def runCase (j : Json) : Except String Json := do
  let specsJson ← match j.getObjVal? "specs" with
    | .ok s => s.getArr?
    | .error _ => do pure #[← j.getObjVal? "spec"]
  let specs ← specsJson.mapM formulaOfJson
  let trace := ((← j.getObjValAs? (Array (Array String)) "trace").map labelOf).toList
  pure (Json.mkObj [("id", j.getObjValD "id"), ("results", Json.arr (specs.map (monitorJson · trace)))])

def batch (path : String) : IO UInt32 := do
  let out ← IO.getStdout
  let mut failures : UInt32 := 0
  for line in ← IO.FS.lines path do
    if line.toList.all Char.isWhitespace then continue
    match Json.parse line >>= runCase with
    | .ok r => out.putStrLn r.compress
    | .error e =>
      failures := failures + 1
      out.putStrLn (Json.mkObj [("error", Json.str e)]).compress
  return if failures == 0 then 0 else 1

def runOne (specPath tracePath : String) : IO UInt32 := do
  match Json.parse (← IO.FS.readFile specPath) >>= formulaOfJson with
  | .error e => IO.eprintln s!"spec: {e}"; return 1
  | .ok spec =>
    let mut residual := spec
    let mut labels : Array (Label String) := #[]
    for line in ← IO.FS.lines tracePath do
      if line.toList.all Char.isWhitespace then continue
      match Json.parse line >>= fun l => (FromJson.fromJson? l : Except String (Array String)) with
      | .error e => IO.eprintln s!"trace line {labels.size + 1}: {e}"; return 1
      | .ok atoms =>
        let σ := labelOf atoms
        labels := labels.push σ
        residual := progress σ residual
        IO.println s!"step {labels.size}: {verdictName residual} (residual size {residual.size})"
    IO.println s!"accepts: {accepts spec labels.toList}"
    return 0

end BBMon

def main (args : List String) : IO UInt32 := do
  match args with
  | ["batch", path] => BBMon.batch path
  | ["run", spec, trace] => BBMon.runOne spec trace
  | _ =>
    IO.eprintln "usage: bbmon batch CASES.jsonl | bbmon run SPEC.json TRACE.jsonl"
    return 2
