"""Step 1 — compare candidate input guards over the attack corpus (the trial).

Consumes the guard defenses from defense/ (protectai_guard, wolf_guard, piguard) — this
report only orchestrates them, it holds no model logic of its own. Runs each over the
distinct attack prompts + the benign control (read from report/attack.jsonl — READ ONLY)
and emits report/input_guard_comparison.md: per-guard recall, which candidate recovers the
incumbent's misses, and where the two front-runners (protectai-v2, wolf-defender) each miss.
The point is to *understand the differences* between the candidates. The finding —
protectai-v2 and wolf-defender miss largely disjoint prompts — motivates step 2, the
two-model defense (built and measured in report/two_model_defense.py). Detection only,
model-agnostic (scores the prompt), no target-model calls.

Benign-control FP here is directional only (n=1).
"""
import sys, pathlib, json, collections

_impl = pathlib.Path(__file__).resolve().parents[1]
sys.path[:0] = [str(_impl.parents[1]), str(_impl)]

from defense.protectai_guard import flag as protectai_flag
from defense.wolf_guard import flag as wolf_flag
from defense.piguard import flag as piguard_flag

ATTACK = _impl / "report" / "attack.jsonl"               # read only
REPORT = _impl / "report" / "input_guard_comparison.md"

# Candidate input-guard defenses being compared, each referred to by an explicit name rather
# than a list position. The flag() for each lives in defense/ (imported above) — this report
# only orchestrates them; label + license are display metadata.
PROTECTAI = "protectai-v2"      # incumbent single-model input guard
WOLF = "wolf-defender"          # ensemble partner — recovers the incumbent's misses
PIGUARD = "PIGuard"             # also-ran — low-FP-tuned, under-flags in-distribution

GUARDS = {
    PROTECTAI: {"label": "protectai-v2 (incumbent)", "license": "Apache-2.0", "flag": protectai_flag},
    WOLF: {"label": "wolf-defender-small", "license": "Apache-2.0", "flag": wolf_flag},
    PIGUARD: {"label": "PIGuard", "license": "MIT", "flag": piguard_flag},
}
ORDER = [PROTECTAI, WOLF, PIGUARD]                         # display order in the report tables


def distinct_prompts(rows):
    """id -> {technique, prompt, leaked}: collapse the 300 rows to each distinct prompt,
    leaked = it leaked on >=1 model. The guard scores the prompt, so it's model-agnostic."""
    d = collections.OrderedDict()
    for r in rows:
        e = d.setdefault(r["id"], {"technique": r["technique"], "prompt": r["prompt"], "leaked": False})
        e["leaked"] = e["leaked"] or bool(r["system_leaked"] or r["secrets_leaked"])
    return d


def snippet(text, n=60):
    s = " ".join(text.split())
    return (s[:n] + "…") if len(s) > n else s


def main():
    rows = [json.loads(l) for l in ATTACK.read_text().splitlines() if l.strip()]
    prompts = distinct_prompts(rows)
    attacks = [i for i, e in prompts.items() if e["technique"] != "benign-control"]
    benign = [i for i, e in prompts.items() if e["technique"] == "benign-control"]

    fired = {name: {i: GUARDS[name]["flag"](prompts[i]["prompt"]) for i in prompts} for name in ORDER}
    incumbent_misses = [i for i in attacks if not fired[PROTECTAI][i]]   # attacks protectai-v2 calls SAFE

    out = ["# LLM07 impl-01 — input-guard options compared", "",
           f"Three local prompt-injection classifiers as candidate input guards over the "
           f"{len(attacks)} distinct attack prompts + {len(benign)} benign control, read from the "
           "attack evidence. Recall = attack prompts flagged INJECTION. Benign FP is directional "
           f"only (n={len(benign)}) — the real false-positive rate is the legit-traffic assessment.", "",
           "| detector | license | recall | benign FP |", "|---|---|---|---|"]
    for name in ORDER:
        guard = GUARDS[name]
        recall = sum(fired[name][i] for i in attacks)
        false_pos = sum(fired[name][i] for i in benign)
        out.append(f"| {guard['label']} | {guard['license']} | {recall}/{len(attacks)} "
                   f"({100*recall/len(attacks):.0f}%) | {false_pos}/{len(benign)} |")

    challengers = [WOLF, PIGUARD]
    out += ["", "## Recovering the incumbent's misses", "",
            f"protectai-v2 misses {len(incumbent_misses)} of {len(attacks)} attacks. A ✓ means the "
            "challenger flags that prompt INJECTION where the incumbent did not.", "",
            "| id | technique | prompt | " + " | ".join(GUARDS[c]["label"] for c in challengers) + " |",
            "|---|---|---|" + "---|" * len(challengers)]
    for i in incumbent_misses:
        e = prompts[i]
        marks = " | ".join("✓" if fired[c][i] else "✗" for c in challengers)
        out.append(f"| {i} | {e['technique']} | {snippet(e['prompt'])} | {marks} |")
    out.append("")
    for c in challengers:
        recovered = sum(fired[c][i] for i in incumbent_misses)
        out.append(f"- **{GUARDS[c]['label']}** recovers {recovered}/{len(incumbent_misses)} "
                   "of the incumbent's misses.")

    # Symmetric view of the two ensemble members: every attack at least one of them misses,
    # marked per model. The row both mark ✗ is the ensemble's blind spot.
    members = [PROTECTAI, WOLF]
    missed_by_either = [i for i in attacks if any(not fired[m][i] for m in members)]
    out += ["", "## Where each ensemble member misses", "",
            "Every attack that protectai-v2 or wolf-defender misses, marked per model "
            "(✗ = said SAFE on an attack). They miss largely disjoint sets; the only row both "
            "mark ✗ is the ensemble's blind spot.", "",
            "| id | technique | prompt | " + " | ".join(GUARDS[m]["label"] for m in members) + " |",
            "|---|---|---|" + "---|" * len(members)]
    for i in missed_by_either:
        e = prompts[i]
        marks = " | ".join("✗" if not fired[m][i] else "✓" for m in members)
        out.append(f"| {i} | {e['technique']} | {snippet(e['prompt'])} | {marks} |")

    # Finding: the two front-runners tie on recall but miss largely disjoint sets, so combining
    # them should cover nearly everything. That motivates step 2 — the two-model defense, which
    # is built and measured separately (report/two_model_defense.py), not here.
    p_recall = sum(fired[PROTECTAI][i] for i in attacks)
    w_recall = sum(fired[WOLF][i] for i in attacks)
    missed_by_both = [i for i in attacks if not fired[PROTECTAI][i] and not fired[WOLF][i]]
    out += ["", "## Finding", "",
            f"protectai-v2 and wolf-defender tie on recall ({p_recall}/{len(attacks)} and "
            f"{w_recall}/{len(attacks)}) but miss *different* prompts — only "
            f"{', '.join(missed_by_both) or 'none'} escapes both. They're complementary, not "
            "redundant, so combining them should cover nearly everything. That's the next step: "
            "the two-model input defense `defense/two_model_guard.py`, built and measured in "
            "`two_model_defense.md`."]

    text = "\n".join(out) + "\n"
    REPORT.write_text(text)
    print(text)


if __name__ == "__main__":
    main()
