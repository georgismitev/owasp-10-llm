# OWASP Top 10 for LLM Applications (2025) — hands-on lab

Reproduce each attack, ship a defense, and measure the before/after. See
[`PLAN.md`](PLAN.md) for the full plan.

## Layout

- [`PLAN.md`](PLAN.md) — the full project plan.
- [`docs/`](docs/) — project documentation.
  - [`docs/CHANGELOG.md`](docs/CHANGELOG.md) — **step-by-step log of everything we
    do**, including actions with no git trace (e.g. installing Ollama, pulling models).
- [`CLAUDE.md`](CLAUDE.md) — rules of engagement.
- [`labkit/`](labkit/) — the shared platform: a minimal OpenAI-compatible model
  client + on-disk cache. Platform only — **no attack / defense / eval logic.**
- `pyproject.toml` / `uv.lock` — Python packaging via [`uv`](https://docs.astral.sh/uv/).
- `LLM<NN>-<slug>/` — one folder per lab (e.g.
  [`LLM07-system-prompt-leakage/`](LLM07-system-prompt-leakage/)).

## Lab structure

Each lab follows the same convention.

- **`LLM<NN>-<slug>/`** — an **attack-level README** (threat model, adversary,
  trust boundaries) plus one or more implementations `impl-<NN>-<slug>/`.
- **`impl-<NN>-<slug>/`** — a standard five-directory layout:
  - **`target/`** — the vulnerable app (e.g. a system prompt wired through `labkit`).
  - **`attack/`** — the attempt corpus (`attempts.py`) + a runner (`run.py`) that
    fires it and logs to `results/`.
  - **`eval/`** — the judge + ASR / report generator (`judge.py`, `report.py`);
    the authoritative measurement.
  - **`defense/`** — the measured mitigation, toggled by `DEFENSE=on` (env flag,
    no code edit).
  - **`results/`** — baseline vs defended ASR, utility retention, transcripts.

**Two-README convention:** the lab-level README carries the threat model; each
impl README carries the impl-specific detail.
