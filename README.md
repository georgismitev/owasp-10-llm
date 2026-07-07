# OWASP Top 10 for LLM Applications (2025) — hands-on lab

Reproduce each OWASP LLM Top 10 (2025) attack against self-hosted open-weight models,
ship a defense for each, and **measure the before/after** — so the defense is proven,
not asserted. For each attack a reader can: **clone → run the attack → see the effect →
enable the defense → re-run → see the residual risk**, with real numbers at each step.

> A learning project. Tooling and agents build the platform and scaffolding only —
> never the exploits or the mitigations.

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

## Layout

- [`docs/setup.md`](docs/setup.md) — the shared machinery: serving, `labkit/`, the
  per-lab layout, and how success is measured.
- [`docs/handover.md`](docs/handover.md) — run-to-run state.
- [`docs/CHANGELOG.md`](docs/CHANGELOG.md) — step-by-step log of everything we do,
  including actions with no git trace (installing Ollama, pulling models).
- [`CLAUDE.md`](CLAUDE.md) — rules of engagement.
- [`labkit/`](labkit/) — the shared platform (OpenAI-compatible model client + on-disk
  cache); platform only, **no attack / defense / eval logic**.
- `LLM<NN>-<slug>/` — one folder per lab (e.g.
  [`LLM07-system-prompt-leakage/`](LLM07-system-prompt-leakage/)).
- `pyproject.toml` / `uv.lock` — Python packaging via [`uv`](https://docs.astral.sh/uv/).
