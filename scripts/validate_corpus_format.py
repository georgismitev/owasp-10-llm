#!/usr/bin/env python3
"""Corpus format validator for the LLM07 lab (pure schema checking).

Run with file paths as argv, or with no argv as a PostToolUse hook that reads the
JSON payload on stdin and validates tool_input.file_path. Non-corpus paths pass
silently; a violation prints one line to stderr and exits 2, a conforming file exits 0.
"""
import importlib.util
import json
import sys
from pathlib import Path

CORPUS_ROOT = "LLM07-system-prompt-leakage"
LEAK_DEPTHS = {"none", "partial", "full"}
# results/<name>.jsonl -> the label key standing in the "technique" slot
RESULTS = {"attack.jsonl": "technique", "paraphrase.jsonl": "technique",
           "legitimate.jsonl": "pair", "leaky.jsonl": "pair"}
# data/<name>.py -> (constant the module exposes, its label key)
DATA = {"attack.py": ("ATTEMPTS", "technique"), "paraphrase.py": ("PARAPHRASE", "technique"),
        "legitimate.py": ("LEGITIMATE", "pair"), "leaky.py": ("LEAKY", "pair")}

def fail(message):
    print(message, file=sys.stderr)
    sys.exit(2)

def check_keys(where, row, expected):
    if set(row) != expected:
        fail(f"{where} wrong keys: missing {expected - set(row)}, unexpected {set(row) - expected}")

def validate_jsonl(path, label):
    expected = {"id", "model", "fingerprint", "prompt", "response",
                "system_leaked", "secrets_leaked", "leak_depth", label}
    strings = {"id", "model", "fingerprint", "prompt", "response", label}
    for n, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as e:
            fail(f"{path}:{n} invalid JSON ({e.msg})")
        check_keys(f"{path}:{n}", row, expected)
        for k in strings:
            if not isinstance(row[k], str):
                fail(f"{path}:{n} {k} must be a string")
        for k in ("system_leaked", "secrets_leaked"):
            if not isinstance(row[k], bool):
                fail(f"{path}:{n} {k} must be a boolean")
        if row["leak_depth"] not in LEAK_DEPTHS:
            fail(f"{path}:{n} leak_depth must be none/partial/full, got {row['leak_depth']!r}")

def validate_data(path, constant, label):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    entries = getattr(module, constant, None)
    if not isinstance(entries, list):
        fail(f"{path} must expose a list constant {constant}")
    expected = {"id", label, "prompt"}
    for i, entry in enumerate(entries):
        where = f"{path} entry {i}"
        check_keys(where, entry, expected)
        for k in expected:
            if not isinstance(entry[k], str):
                fail(f"{where} {k} must be a string")

def validate(path):
    p = Path(path)
    if p.parent.parent.name != CORPUS_ROOT:
        return
    if p.parent.name == "results" and p.name in RESULTS:
        validate_jsonl(p, RESULTS[p.name])
    elif p.parent.name == "data" and p.name in DATA:
        validate_data(p, *DATA[p.name])

def main():
    args = sys.argv[1:]
    paths = args or [json.load(sys.stdin).get("tool_input", {}).get("file_path", "")]
    for path in paths:
        validate(path)

if __name__ == "__main__":
    main()
