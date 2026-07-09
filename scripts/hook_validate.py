#!/usr/bin/env python3
"""PostToolUse hook: after a Write/Edit, if the touched file is a data/ or results/ corpus
file, validate it against the canonical schema and surface any non-conformance as feedback.

Reads the tool payload on stdin; exits 0 (quiet) for non-corpus files or on PASS, and exits 2
with the failures on stderr on non-conformance (which returns the feedback to the agent).
"""
import sys, json, subprocess, pathlib

try:
    payload = json.load(sys.stdin)
except Exception:
    sys.exit(0)

fp = (payload.get("tool_input") or {}).get("file_path") or ""
if not fp:
    sys.exit(0)

p = pathlib.Path(fp)
is_corpus = (p.parent.name == "results" and p.suffix == ".jsonl") or (p.parent.name == "data" and p.suffix == ".py")
if not is_corpus:
    sys.exit(0)

root = pathlib.Path(__file__).resolve().parents[1]
result = subprocess.run(
    [sys.executable, str(root / "scripts" / "validate_corpus_format.py"), fp],
    capture_output=True, text=True, cwd=str(root))
if result.returncode != 0:
    print(f"[data-format-guardian] {fp} does not conform to the corpus format:\n"
          f"{(result.stdout + result.stderr).strip()}", file=sys.stderr)
    sys.exit(2)
sys.exit(0)
