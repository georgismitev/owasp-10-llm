"""Corpus format guardian — validate data/ and results/ files against the canonical schema.

The lab's corpora follow one fixed shape so every generator, judge, and report can rely on it.
This checker enforces it deterministically. It only READS files — results/*.jsonl are immutable.

  uv run python scripts/validate_corpus_format.py <path> [<path> ...]   validate specific files
  uv run python scripts/validate_corpus_format.py --all                 validate every corpus file

Format
  results/*.jsonl : one JSON object per line, keys in this exact order —
      id, (technique | pair), model, fingerprint, prompt, response,
      system_leaked, secrets_leaked, leak_depth
    id non-empty str; the 2nd key is technique OR pair (a str, the same choice for every row in
    the file); model/prompt/response str; fingerprint a 16-char lowercase-hex str;
    system_leaked/secrets_leaked bool; leak_depth one of "none"/"partial"/"full". No other keys.
  data/*.py : a module with a docstring that defines exactly one UPPERCASE list of dicts, each
    dict being {id: str (non-empty), technique|pair: str, prompt: str} — nothing else.
"""
import sys, json, ast, re, pathlib

HEX16 = re.compile(r"^[0-9a-f]{16}$")
LEAK_DEPTH = {"none", "partial", "full"}
RESULTS_TAIL = ["model", "fingerprint", "prompt", "response", "system_leaked", "secrets_leaked", "leak_depth"]


def _check_second_key(keys, err, where):
    """The 2nd key must be technique or pair; return it (or None on failure)."""
    if len(keys) < 2 or keys[1] not in ("technique", "pair"):
        err(where, f"2nd key must be 'technique' or 'pair', got {keys[1] if len(keys) > 1 else '<none>'}")
        return None
    return keys[1]


def validate_results(path):
    errors = []
    err = lambda w, m: errors.append((w, m))
    file_second = None
    for i, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as e:
            err(f"line {i}", f"not valid JSON: {e}")
            continue
        if not isinstance(row, dict):
            err(f"line {i}", "not a JSON object")
            continue
        keys = list(row.keys())
        second = _check_second_key(keys, err, f"line {i}")
        if second is None:
            continue
        if file_second is None:
            file_second = second
        elif second != file_second:
            err(f"line {i}", f"2nd key '{second}' inconsistent with '{file_second}' used earlier in the file")
        expected = ["id", second] + RESULTS_TAIL
        if keys != expected:
            err(f"line {i}", f"keys/order must be {expected}, got {keys}")
            continue
        for k in ("id", second, "model", "prompt", "response"):
            if not isinstance(row[k], str):
                err(f"line {i}", f"{k} must be a string")
        if isinstance(row["id"], str) and not row["id"]:
            err(f"line {i}", "id is empty")
        if not (isinstance(row["fingerprint"], str) and HEX16.match(row["fingerprint"])):
            err(f"line {i}", f"fingerprint must be 16 lowercase hex chars, got {row['fingerprint']!r}")
        for k in ("system_leaked", "secrets_leaked"):
            if not isinstance(row[k], bool):
                err(f"line {i}", f"{k} must be a boolean")
        if row["leak_depth"] not in LEAK_DEPTH:
            err(f"line {i}", f"leak_depth must be one of {sorted(LEAK_DEPTH)}, got {row['leak_depth']!r}")
    return errors


def validate_data(path):
    errors = []
    err = lambda w, m: errors.append((w, m))
    tree = ast.parse(path.read_text())
    if not ast.get_docstring(tree):
        err("module", "missing module docstring")
    lists = [(n.targets[0].id, n.value) for n in tree.body
             if isinstance(n, ast.Assign) and len(n.targets) == 1
             and isinstance(n.targets[0], ast.Name) and n.targets[0].id.isupper()
             and isinstance(n.value, ast.List)]
    if len(lists) != 1:
        err("module", f"expected exactly one UPPERCASE list of entries, found {len(lists)}")
        return errors
    name, node = lists[0]
    try:
        entries = ast.literal_eval(node)
    except (ValueError, SyntaxError) as e:
        err(name, f"list is not a plain literal: {e}")
        return errors
    file_second = None
    for idx, entry in enumerate(entries):
        where = f"{name}[{idx}]"
        if not isinstance(entry, dict):
            err(where, "entry is not a dict")
            continue
        keys = list(entry.keys())
        second = _check_second_key(keys, err, where)
        if second is None:
            continue
        if file_second is None:
            file_second = second
        elif second != file_second:
            err(where, f"2nd key '{second}' inconsistent with '{file_second}' earlier in the list")
        expected = ["id", second, "prompt"]
        if keys != expected:
            err(where, f"keys/order must be {expected}, got {keys}")
            continue
        for k in ("id", second, "prompt"):
            if not isinstance(entry[k], str):
                err(where, f"{k} must be a string")
        if isinstance(entry["id"], str) and not entry["id"]:
            err(where, "id is empty")
    return errors


def validate(path):
    """Route a file to the right validator by its folder; None if it is not a corpus file."""
    p = pathlib.Path(path)
    if p.parent.name == "results" and p.suffix == ".jsonl":
        return validate_results(p)
    if p.parent.name == "data" and p.suffix == ".py":
        return validate_data(p)
    return None


def discover(root):
    skip = {".venv", "__pycache__", ".git", "worktrees"}
    for p in sorted(pathlib.Path(root).rglob("*")):
        if skip & set(p.parts):
            continue
        if (p.parent.name == "results" and p.suffix == ".jsonl") or (p.parent.name == "data" and p.suffix == ".py"):
            yield p


def main(argv):
    root = pathlib.Path(__file__).resolve().parents[1]
    paths = list(discover(root)) if argv == ["--all"] else [pathlib.Path(a) for a in argv]
    if not paths:
        print("usage: validate_corpus_format.py <path> ... | --all")
        return 2
    failed = 0
    for p in paths:
        errors = validate(p)
        if errors is None:
            print(f"SKIP {p}  (not a data/results corpus file)")
            continue
        rel = p.resolve().relative_to(root) if p.resolve().is_relative_to(root) else p
        if errors:
            failed += 1
            print(f"FAIL {rel}")
            for where, msg in errors:
                print(f"   {where}: {msg}")
        else:
            print(f"PASS {rel}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
