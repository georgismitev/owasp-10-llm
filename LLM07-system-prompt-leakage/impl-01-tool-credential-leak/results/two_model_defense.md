# LLM07 impl-01 — two-model input defense

`defense/two_model_guard.py` = protectai-v2 **OR** wolf-defender (hard-label OR), built from the input-guard comparison where the two were found to miss disjoint prompts. Measured here over the 49 distinct attack prompts + 1 benign control from the attack evidence.

- recall: **48/49** attacks flagged INJECTION (98%)
- blind spot: structured-01 — flagged by neither model
- benign FP: 0/1 (directional only, n=1)

## Combining in production — how the two votes fuse

The 48/49 above is a **hard-label OR**: each model argmaxes at its own 0.5 boundary into a yes/no vote, and the defense fires if *either* votes INJECTION (`flag = protectai.INJECTION or wolf.INJECTION`). No score sharing, no threshold, no confidence blending — the crudest fusion. Before this ships, weigh three ways the two could combine:

- **Hard-label OR (what we ship today).** Max recall, zero tuning. But it also **unions the false positives** — whenever *either* model over-blocks a benign prompt, so does the defense. We never saw that cost: this measurement has 1 benign control and it passed. So the OR *looks* free and isn't proven to be.
- **Score-level fusion (the tunable version).** Combine the two INJECTION softmax probabilities into one score and threshold once: `max(p_protectai, p_wolf)` behaves like OR but with a *movable* cutoff instead of two fixed 0.5 boundaries; `mean`/weighted needs agreement, trading recall for fewer false positives. This is the dial that trades recall vs FP — but picking the threshold needs a calibration/legit-traffic set.
- **Cascade (staged).** Run one model first, run the second only on what the first passes. For a pure OR the verdict is *identical* — a cascade only saves compute by short-circuiting (which is what `flag()` already does). It changes the decision only if the second model is a *confirmer* (AND, to cut FPs) rather than a booster.

**Bottom line:** hard-OR is the right baseline — protectai-v2 and wolf-defender are complementary, together 48/49, better than either alone — but its FP cost is unmeasured here. Ship score fusion with a threshold calibrated on legit traffic where over-blocking real users is costly; hard-OR is fine where a missed extraction hurts far more than an occasional false alarm. Either way the FP side is the open question — the legit-traffic assessment.
