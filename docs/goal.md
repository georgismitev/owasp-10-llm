# Goal — OWASP Top 10 for LLM Applications (2025): Reproduce → Defend → Prove

A hands-on lab repo that reproduces each OWASP LLM Top 10 (2025) attack against
self-hosted open-weight models, ships a defense for each, and **measures the
before/after** so the defense is proven, not asserted.

> A learning project. Every attack and every defense is written by hand. Tooling
> and agents build the platform and scaffolding only — never the exploits or the
> mitigations.

## What we are aiming to do

For each attack a reader can: **clone → set up → run the attack → see the effect →
enable the defense → re-run → see the residual risk** — with real numbers at each step.

Each lab is a self-contained folder on a fixed layout, so the repo reads as one
coherent body of work rather than 10 one-off demos. What makes it worth publishing is
**measurement rigor applied uniformly**: every lab reports a baseline attack success
rate, a defended attack success rate, and the utility cost of the defense.

**Two depth tiers.** Phase 1 = 4 flagship labs done to the full Definition of Done.
Phase 2 = the remaining 6, lighter (smaller demo, lighter measurement, shorter writeup)
or documented as scoped-out where local reproduction isn't meaningful. Finish the 4
before starting the 6.

> Why 4: the overall plan is **8 flagships = 4 LLM + 4 agentic**, chosen so the agentic
> four reuse the LLM four (this repo is the LLM half). The 4 LLM flagships are
> LLM07 → LLM01 → LLM05 → LLM06; the matching agentic four (in the other repo) are
> ASI01, ASI02, ASI06, ASI05.

No deadlines. The order is a sequence, not a schedule.

## The attack plan

### Phase 1 — the 4 flagships (full Definition of Done), in build order

| # | ID | Title | Why here |
|---|----|-------|----------|
| 1 | LLM07 | System Prompt Leakage | Simplest attack; first real lab, exercises the whole harness on an easy target |
| 2 | LLM01 | Prompt Injection | The canonical attack; everything else references it |
| 3 | LLM05 | Improper Output Handling | The output side — injection's payload reaching a downstream sink |
| 4 | LLM06 | Excessive Agency | Introduces the toy tool-using agent; the bridge to the agentic repo |

### Phase 2 — the remaining 6 (lighter / documented), suggested order

| ID | Title | Treatment |
|----|-------|-----------|
| LLM02 | Sensitive Information Disclosure | Solid demo, canary-friendly; could be promoted to a 5th flagship |
| LLM08 | Vector & Embedding Weaknesses | Needs a RAG layer; RAG poisoning + cross-tenant leakage |
| LLM10 | Unbounded Consumption | Cheap and very measurable (tokens / latency / $) |
| LLM04 | Data & Model Poisoning | Backdoor via LoRA fine-tune — substantial even at "lighter" tier; needs fine-tune compute |
| LLM03 | Supply Chain | More plumbing than model-in-loop |
| LLM09 | Misinformation | Softer to measure objectively |

> Each attack's own README carries its threat model and the specific scenarios we
> implement (paraphrased from the *OWASP Top 10 for LLM Applications 2025*, CC BY-SA 4.0).
> We implement the scenarios reproducible on self-hosted open models; a few are scoped out.

## Definition of Done

A Phase-1 lab is **not finished** until all 8 are true:

1. **Reproduces** deterministically, or — if stochastic — reports ASR over N ≥ 20 trials
   with seed / temperature / model logged.
2. **Visible effect** a non-expert can see (leaked canary, executed action, popped alert,
   cost spike).
3. **Baseline ASR** measured.
4. **Defense** implemented as a separable component and measured off vs on — not
   hard-wired into the target.
5. **Defended ASR** measured — the proof.
6. **Utility cost** measured (over-refusal / false-positive rate). A defense that blocks
   the attack by refusing everything is not a defense.
7. **One bypass** of your own defense, timeboxed and documented as residual risk — one
   attack → defend → attack turn, then write down what still gets through and why.
8. **A writeup** complete enough to publish.

Phase 2 labs may relax 3 / 5 / 6 / 7 to lightweight but must still state what they did
and did not measure.

## Working principles

- **Pin everything** in each report — model + digest, quantization, serving backend +
  version, temperature + seed.
- Run every attack across the **transfer set (5 models)** — "does it transfer?" is a
  recurring finding.
- **Source of truth is plain Python, not notebooks** — notebooks invite hidden state and
  out-of-order execution and diff badly in git. Keep exploratory notebooks as throwaway
  scratch, out of the reproducible path.
- **One bypass turn per lab, timeboxed** — then document residual risk and what a real
  system would stack on top (defense in depth).
- Test the final repo from a **fresh clone on a clean machine** before publishing.
