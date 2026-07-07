"""Step 2 — the two-model input defense, measured over the attack corpus.

Built on the finding from the input-guard comparison (step 1): protectai-v2 and
wolf-defender miss largely disjoint prompts, so combining them covers more than either
alone. This measures the actual defense — defense/two_model_guard.flag, the OR of the
two — over the distinct attack prompts + the benign control (read from
results/attack.jsonl — READ ONLY) and emits results/two_model_defense.md. Detection
only, model-agnostic (scores the prompt), no target-model calls.

Benign-control FP here is directional only (n=1) — the real false-positive rate, which a
hard-label OR *unions* across the two models, is the separate legit-traffic assessment.
"""
import sys, pathlib, json, collections

_impl = pathlib.Path(__file__).resolve().parents[1]
sys.path[:0] = [str(_impl.parents[1]), str(_impl)]

from defense.two_model_guard import flag

ATTACK = _impl / "results" / "attack.jsonl"               # read only
REPORT = _impl / "results" / "two_model_defense.md"


def distinct_prompts(rows):
    """id -> {technique, prompt}: collapse the 300 rows to each distinct prompt. The guard
    scores the prompt, so its verdict is model-agnostic — classify each prompt once."""
    d = collections.OrderedDict()
    for r in rows:
        d.setdefault(r["id"], {"technique": r["technique"], "prompt": r["prompt"]})
    return d


def main():
    rows = [json.loads(l) for l in ATTACK.read_text().splitlines() if l.strip()]
    prompts = distinct_prompts(rows)
    attacks = [i for i, e in prompts.items() if e["technique"] != "benign-control"]
    benign = [i for i, e in prompts.items() if e["technique"] == "benign-control"]

    flagged = {i: flag(prompts[i]["prompt"]) for i in prompts}
    caught = [i for i in attacks if flagged[i]]
    missed = [i for i in attacks if not flagged[i]]
    false_pos = [i for i in benign if flagged[i]]

    out = ["# LLM07 impl-01 — two-model input defense", "",
           "`defense/two_model_guard.py` = protectai-v2 **OR** wolf-defender (hard-label OR), "
           "built from the input-guard comparison where the two were found to miss disjoint "
           f"prompts. Measured here over the {len(attacks)} distinct attack prompts + "
           f"{len(benign)} benign control from the attack evidence.", "",
           f"- recall: **{len(caught)}/{len(attacks)}** attacks flagged INJECTION "
           f"({100*len(caught)/len(attacks):.0f}%)",
           f"- blind spot: {', '.join(missed) or 'none'} — flagged by neither model",
           f"- benign FP: {len(false_pos)}/{len(benign)} (directional only, n={len(benign)})"]

    out += ["", "## Combining in production — how the two votes fuse", "",
            f"The {len(caught)}/{len(attacks)} above is a **hard-label OR**: each model argmaxes at "
            "its own 0.5 boundary into a yes/no vote, and the defense fires if *either* votes "
            "INJECTION (`flag = protectai.INJECTION or wolf.INJECTION`). No score sharing, no "
            "threshold, no confidence blending — the crudest fusion. Before this ships, weigh three "
            "ways the two could combine:", "",
            "- **Hard-label OR (what we ship today).** Max recall, zero tuning. But it also **unions "
            "the false positives** — whenever *either* model over-blocks a benign prompt, so does the "
            f"defense. We never saw that cost: this measurement has {len(benign)} benign control and "
            "it passed. So the OR *looks* free and isn't proven to be.",
            "- **Score-level fusion (the tunable version).** Combine the two INJECTION softmax "
            "probabilities into one score and threshold once: `max(p_protectai, p_wolf)` behaves "
            "like OR but with a *movable* cutoff instead of two fixed 0.5 boundaries; `mean`/weighted "
            "needs agreement, trading recall for fewer false positives. This is the dial that trades "
            "recall vs FP — but picking the threshold needs a calibration/legit-traffic set.",
            "- **Cascade (staged).** Run one model first, run the second only on what the first "
            "passes. For a pure OR the verdict is *identical* — a cascade only saves compute by "
            "short-circuiting (which is what `flag()` already does). It changes the decision only if "
            "the second model is a *confirmer* (AND, to cut FPs) rather than a booster.", "",
            "**Bottom line:** hard-OR is the right baseline — protectai-v2 and wolf-defender are "
            f"complementary, together {len(caught)}/{len(attacks)}, better than either alone — but "
            "its FP cost is unmeasured here. Ship score fusion with a threshold calibrated on legit "
            "traffic where over-blocking real users is costly; hard-OR is fine where a missed "
            "extraction hurts far more than an occasional false alarm. Either way the FP side is the "
            "open question — the legit-traffic assessment."]

    text = "\n".join(out) + "\n"
    REPORT.write_text(text)
    print(text)


if __name__ == "__main__":
    main()
