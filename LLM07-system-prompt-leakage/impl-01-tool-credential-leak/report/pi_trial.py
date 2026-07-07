"""Head-to-head trial: alternative prompt-injection detectors vs the shipped input guard.

Runs each detector over the distinct attack prompts + the benign control (read from
results/attack.jsonl — READ ONLY) and emits results/pi_trial.md. The question is whether
a challenger recovers the prompts the incumbent (protectai-v2) misses — especially the
cross-lingual / blunt asks — without newly over-blocking the benign control. This is a
trial to inform a swap decision; it does not change the shipped input_guard. Detection
only, no target-model calls.

Benign-control FP here is directional only (n=1) — the real false-positive rate is the
separate legit-traffic assessment.
"""
import sys, pathlib, json, functools, collections
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

_impl = pathlib.Path(__file__).resolve().parents[1]
sys.path[:0] = [str(_impl.parents[1]), str(_impl)]

ATTACK = _impl / "results" / "attack.jsonl"               # read only
REPORT = _impl / "results" / "pi_trial.md"

# Each detector: display label, license, HF model id, injection class index, trust_remote_code.
# Injection index is pinned from each model's config, or (wolf-defender ships opaque
# LABEL_0/LABEL_1) an empirical probe — all three put INJECTION at class 1.
DETECTORS = [
    {"name": "protectai-v2 (incumbent)", "license": "Apache-2.0",
     "id": "protectai/deberta-v3-base-prompt-injection-v2", "inj": 1, "trust": False},
    {"name": "wolf-defender-small", "license": "Apache-2.0",
     "id": "patronus-studio/wolf-defender-prompt-injection-small", "inj": 1, "trust": False},
    {"name": "PIGuard", "license": "MIT",
     "id": "leolee99/PIGuard", "inj": 1, "trust": True},
]


@functools.lru_cache(maxsize=None)
def _model(model_id, trust):
    tok = AutoTokenizer.from_pretrained(model_id)
    mod = AutoModelForSequenceClassification.from_pretrained(model_id, trust_remote_code=trust).eval()
    return tok, mod


def verdict(det, prompt):
    """True if the detector labels the prompt INJECTION (argmax == its injection class)."""
    tok, mod = _model(det["id"], det["trust"])
    inputs = tok(prompt, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        logits = mod(**inputs).logits
    return int(logits.argmax()) == det["inj"]


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

    fired = {d["name"]: {i: verdict(d, prompts[i]["prompt"]) for i in prompts} for d in DETECTORS}
    incumbent = DETECTORS[0]["name"]
    misses = [i for i in attacks if not fired[incumbent][i]]     # incumbent says SAFE on an attack

    out = ["# LLM07 impl-01 — prompt-injection detector trial", "",
           f"Three local detectors over the {len(attacks)} distinct attack prompts + "
           f"{len(benign)} benign control, read from the attack evidence. Recall = attack "
           "prompts flagged INJECTION. Benign FP is directional only "
           f"(n={len(benign)}) — the real false-positive rate is the legit-traffic assessment.", "",
           "| detector | license | recall | benign FP |", "|---|---|---|---|"]
    for d in DETECTORS:
        rec = sum(fired[d["name"]][i] for i in attacks)
        fp = sum(fired[d["name"]][i] for i in benign)
        out.append(f"| {d['name']} | {d['license']} | {rec}/{len(attacks)} "
                   f"({100*rec/len(attacks):.0f}%) | {fp}/{len(benign)} |")

    challengers = [d["name"] for d in DETECTORS[1:]]
    out += ["", "## Recovering the incumbent's misses", "",
            f"protectai-v2 misses {len(misses)} of {len(attacks)} attacks. A ✓ means the "
            "challenger flags that prompt INJECTION where the incumbent did not.", "",
            "| id | technique | prompt | " + " | ".join(challengers) + " |",
            "|---|---|---|" + "---|" * len(challengers)]
    for i in misses:
        e = prompts[i]
        marks = " | ".join("✓" if fired[c][i] else "✗" for c in challengers)
        out.append(f"| {i} | {e['technique']} | {snippet(e['prompt'])} | {marks} |")
    for c in challengers:
        rec = sum(fired[c][i] for i in misses)
        out.append("" if c == challengers[0] else None)
        out.append(f"- **{c}** recovers {rec}/{len(misses)} of the incumbent's misses.")
    out = [x for x in out if x is not None]

    # Symmetric view of the two ensemble members: every attack at least one of them misses,
    # marked per model. The row both mark ✗ is the ensemble's blind spot.
    members = [incumbent, "wolf-defender-small"]
    miss_union = [i for i in attacks if any(not fired[m][i] for m in members)]
    out += ["", "## Where each ensemble member misses", "",
            "Every attack that protectai-v2 or wolf-defender misses, marked per model "
            "(✗ = said SAFE on an attack). They miss largely disjoint sets; the only row both "
            "mark ✗ is the ensemble's blind spot.", "",
            "| id | technique | prompt | " + " | ".join(members) + " |",
            "|---|---|---|" + "---|" * len(members)]
    for i in miss_union:
        e = prompts[i]
        marks = " | ".join("✗" if not fired[m][i] else "✓" for m in members)
        out.append(f"| {i} | {e['technique']} | {snippet(e['prompt'])} | {marks} |")

    # Swap vs combine: a challenger that ties recall but catches different prompts is
    # worth more in an OR-ensemble than as a replacement. Report the union coverage.
    pair = f"{incumbent} ∪ wolf-defender-small"
    union = sum(fired[incumbent][i] or fired["wolf-defender-small"][i] for i in attacks)
    both_miss = [i for i in attacks if not fired[incumbent][i] and not fired["wolf-defender-small"][i]]
    out += ["", "## Swap, or combine?", "",
            "wolf-defender ties recall but catches a *different* set — so it's stronger as an "
            "OR-ensemble (flag if either fires) than as a drop-in replacement.", "",
            f"- **{pair}** flags {union}/{len(attacks)} attacks ({100*union/len(attacks):.0f}%); "
            f"the only attack neither catches is {', '.join(both_miss) or 'none'}."]

    out += ["", "## Combining in production — how the two votes fuse", "",
            f"The {union}/{len(attacks)} above is a **hard-label OR**: each model argmaxes at its "
            "own 0.5 boundary into a yes/no vote, and the ensemble fires if *either* votes "
            "INJECTION (`flag = protectai.INJECTION or wolf.INJECTION`). No score sharing, no "
            "threshold, no confidence blending — the crudest fusion. It's the right choice for "
            "*measuring* \"do they catch different things\", but before this ships, weigh three ways "
            "the two could combine:", "",
            "- **Hard-label OR (measured here).** Max recall, zero tuning. But it also **unions the "
            "false positives** — whenever *either* model over-blocks a benign prompt, so does the "
            f"ensemble. We never saw that cost: the trial has {len(benign)} benign control and both "
            "passed it. So the OR *looks* free and isn't proven to be.",
            "- **Score-level fusion (the tunable version).** Combine the two INJECTION softmax "
            "probabilities into one score and threshold once: `max(p_protectai, p_wolf)` behaves "
            "like OR but with a *movable* cutoff instead of two fixed 0.5 boundaries; `mean`/weighted "
            "needs agreement, trading recall for fewer false positives. This is the dial that trades "
            "recall vs FP — but picking the threshold needs a calibration/legit-traffic set.",
            "- **Cascade (staged).** Run one model first, run the second only on what the first "
            "passes. For a pure OR the verdict is *identical* — a cascade only saves compute by "
            "short-circuiting. It changes the decision only if the second model is a *confirmer* "
            "(AND, to cut FPs) rather than a booster.", "",
            "**Bottom line:** hard-OR is the right measurement baseline (it isolates whether the two "
            "are complementary — they are), but not necessarily the right deployment. Its FP cost is "
            "unmeasured here. Ship score fusion with a threshold calibrated on legit traffic where "
            "over-blocking real users is costly; hard-OR is fine where a missed extraction hurts far "
            "more than an occasional false alarm. Either way the FP side is the open question — that "
            "is the legit-traffic assessment, not this trial."]

    text = "\n".join(out) + "\n"
    REPORT.write_text(text)
    print(text)


if __name__ == "__main__":
    main()
