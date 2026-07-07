# Goal — OWASP Top 10 for LLM Applications (2025): Reproduce → Defend → Prove

A hands-on lab repo that reproduces each OWASP LLM Top 10 (2025) attack against
self-hosted open-weight models, ships a defense for each, and **measures the
before/after** so the defense is proven, not asserted.

> A learning project. Tooling and agents build the platform and scaffolding only —
> never the exploits or the mitigations.

## What we are aiming to do

For each attack a reader can: **clone → set up → run the attack → see the effect →
enable the defense → re-run → see the residual risk** — with real numbers at each step.

Each lab is a self-contained folder on a fixed layout, with **measurement rigor applied
uniformly**: every lab reports a baseline attack success rate, a defended attack success
rate, and the utility cost of the defense.

## The attack plan

The build order:

| # | ID | Title |
|---|----|-------|
| 1 | LLM07 | System Prompt Leakage |
| 2 | LLM01 | Prompt Injection |
| 3 | LLM05 | Improper Output Handling |
| 4 | LLM06 | Excessive Agency |
| 5 | LLM02 | Sensitive Information Disclosure |
| 6 | LLM08 | Vector & Embedding Weaknesses |
| 7 | LLM10 | Unbounded Consumption |
| 8 | LLM04 | Data & Model Poisoning |
| 9 | LLM03 | Supply Chain |
| 10 | LLM09 | Misinformation |

> Each attack's own README carries its threat model and the specific scenarios we
> implement (paraphrased from the *OWASP Top 10 for LLM Applications 2025*, CC BY-SA 4.0).

## Definition of Done

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

## Working principles

- **Pin everything** in each report — model + digest, quantization, serving backend +
  version, temperature + seed.
- Run every attack across the **transfer set (5 models)** — "does it transfer?" is a
  recurring finding.
- **Source of truth is plain Python, not notebooks** — notebooks invite hidden state and
  out-of-order execution and diff badly in git. Keep exploratory notebooks as throwaway
  scratch, out of the reproducible path.
