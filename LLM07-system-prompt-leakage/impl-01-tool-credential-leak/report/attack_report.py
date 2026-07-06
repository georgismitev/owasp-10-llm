"""Render the attack transfer report from evidence → results/attack_report.md.

Reader only. Aggregates each run's stored verdicts by the fields on the run
(model / technique / id); imports nothing from the pipeline — the evidence is
self-describing, so the report never re-derives fingerprints or re-runs anything.
"""
import json, pathlib, collections

_impl = pathlib.Path(__file__).resolve().parents[1]
RESULTS = _impl / "results" / "attack.jsonl"
REPORT = _impl / "results" / "attack_report.md"
MODELS = ["qwen2.5:3b", "llama3.1:8b", "gemma3:12b", "glm4:9b", "mistral:7b", "qwen3.5:9b"]
TRANSFER = MODELS[1:]
LABEL = {"system_leaked": "system-leak", "secrets_leaked": "secret-leak"}


def load():
    return [json.loads(l) for l in RESULTS.read_text().splitlines() if l.strip()]


def techniques(rows):
    """Ordered technique -> set of attempt ids, in first-seen order."""
    t = collections.OrderedDict()
    for r in rows:
        t.setdefault(r["technique"], set()).add(r["id"])
    return t


def present(rows):
    return [m for m in MODELS if any(r["model"] == m for r in rows)]


def depth_table(rows, models):
    dep = {m: collections.Counter() for m in models}
    sec = collections.Counter()
    n = collections.Counter()
    for r in rows:
        m = r["model"]
        if m not in dep:
            continue
        n[m] += 1
        dep[m][r["depth"]] += 1
        sec[m] += bool(r["secrets_leaked"])
    lines = ["### leak depth by model", "",
             "system-prompt recital by verbatim marker count "
             "(none=0, partial=1–3, full=all 4); secret = credential leaked.", "",
             "| model | n | none | partial | full | secret |", "|---|---|---|---|---|---|"]
    for m in models:
        d = dep[m]
        lines.append(f"| {m} | {n[m]} | {d['none']} | {d['partial']} | {d['full']} | {sec[m]} |")
    return "\n".join(lines)


def counts(rows, flag):
    """(technique, model) -> [leaked, ran]."""
    c = collections.defaultdict(lambda: [0, 0])
    for r in rows:
        cell = c[(r["technique"], r["model"])]
        cell[1] += 1
        cell[0] += bool(r[flag])
    return c


def matrix(rows, models, flag):
    c = counts(rows, flag)
    techs = techniques(rows)
    order = sorted(techs, key=lambda t: (-sum(1 for m in TRANSFER if c[(t, m)][0] > 0),
                                         -sum(c[(t, m)][0] for m in models)))
    head = "| technique (n) | " + " | ".join(models) + " |"
    sep = "|" + "---|" * (len(models) + 1)
    lines = [f"### {LABEL[flag]} by technique x model", "", head, sep]
    for t in order:
        vals = []
        for m in models:
            leaked, ran = c[(t, m)]
            vals.append(f"{leaked}/{ran}" if ran else "–")
        lines.append(f"| {t} ({len(techs[t])}) | " + " | ".join(vals) + " |")
    return "\n".join(lines)


def callouts(rows, models):
    techs = techniques(rows)
    sysc = counts(rows, "system_leaked")
    dev = models[0]
    universal = [t for t in techs if all(sysc[(t, m)][0] > 0 for m in TRANSFER)]
    dev_only = [t for t in techs
                if sysc[(t, dev)][0] > 0 and all(sysc[(t, m)][0] == 0 for m in TRANSFER)]
    leaked_ids, seen_ids = set(), []
    for r in rows:
        if r["id"] not in seen_ids:
            seen_ids.append(r["id"])
        if r["system_leaked"] or r["secrets_leaked"]:
            leaked_ids.add(r["id"])
    dead = [i for i in seen_ids if i not in leaked_ids]
    resist = sorted(models, key=lambda m: sum(1 for r in rows if r["model"] == m and r["system_leaked"]))
    example = {}
    for r in rows:
        if r["technique"] in universal and r["technique"] not in example:
            example[r["technique"]] = " ".join(r["prompt"].split())
    lines = ["### callouts", "",
             f"- **universal** (system-leak on all {len(TRANSFER)} transfer models): {', '.join(universal) or 'none'}"]
    for t in universal:
        ex = example[t]
        lines.append(f'  - `{t}` — e.g. "{ex if len(ex) <= 140 else ex[:139] + "…"}"')
    lines.append(f"- **doesn't transfer** (leaks dev only, none of the {len(TRANSFER)}): {', '.join(dev_only) or 'none'}")
    lines.append(f"- **dead** (leak nowhere): {', '.join(dead) or 'none'}")
    n_resist = sum(1 for r in rows if r["model"] == resist[0] and r["system_leaked"])
    lines.append(f"- **most-resistant model** (fewest system-leaks): {resist[0]} ({n_resist})")
    return "\n".join(lines)


def main():
    rows = load()
    models = present(rows)
    corpus = len({r["id"] for r in rows})
    out = [
        "# LLM07 impl-01 — transfer report", "",
        f"corpus: {corpus} attempts · judge: literal string-match (canary + keyword)",
        "counts are over a hand-built corpus — comparative across models, not a severity score.",
        "techniques are a hand-picked sample, not exhaustive coverage of the extraction space.",
    ]
    coverage = [f"{m} {sum(1 for r in rows if r['model'] == m)}/{corpus}"
                for m in models if sum(1 for r in rows if r["model"] == m) < corpus]
    if coverage:
        out.append(f"> ⚠ partial data: {', '.join(coverage)}")
    out += ["", depth_table(rows, models), "",
            matrix(rows, models, "system_leaked"), "",
            matrix(rows, models, "secrets_leaked"), "", callouts(rows, models), ""]
    text = "\n".join(out)
    REPORT.write_text(text)
    print(text)


if __name__ == "__main__":
    main()
