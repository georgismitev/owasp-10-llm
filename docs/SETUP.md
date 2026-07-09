# Setup — the shared machinery

How the lab is wired: the serving substrate, the shared `labkit/` harness, the per-lab
layout, and how success is measured. Zero attack logic lives here.

## Serving

Open-weight models served locally at Q4 over Ollama (CPU), behind a thin
OpenAI-compatible client. One model served at a time, compared at the end. Determinism
is pinned per run (temperature 0, seed 0). The transfer set and the per-model pin sheet
(tag + digest + quant) live in `docs/USED_MODELS.md`.

## `labkit/` — shared harness, zero attack logic

- **Model client** (`client.py`) — OpenAI-compatible, single-turn chat with determinism
  defaults (temp 0, seed 0). Logs model + params on every call. Reasoning models are
  routed through the native `/api/chat` path (`think:false`) where the `/v1` endpoint
  can't quiet them.
- **Response cache** (`cache.py`) — keyed on model + messages + params; serves cached
  outputs unless bypassed. Generate once on a slow CPU box, then re-judge / re-report
  from cache instead of re-running the model.

Other machinery (corpora, judges, defenses, reports) lives per-lab rather than in
`labkit/` — built when a lab needs it, kept minimal.

## Per-lab layout

Each implementation is a self-contained target → attack → judge → defense → measurement
unit. Roles (LLM07 is the reference):

- `target/` — the minimal vulnerable app under test.
- `data/` — the send corpora (attack prompts, legitimate prompts).
- `results/` — the run evidence (append-only JSONL, **immutable**); only the runner writes it.
- `eval/` — the judge: did the attack succeed?
- `defense/` — the detectors / mitigations.
- `report/` — renderers that read the evidence and emit markdown; verdicts are computed
  in memory, never persisted (a deterministic function of evidence + detector).

## Measurement

- **Judge** — pick the judge that matches the attack's goal. Each attack's README
  defines its own (e.g. downstream-sink assertion for output handling,
  tool-call assertion for excessive agency, counters for unbounded consumption).
- **Attack success rate** — run the attempt corpus, apply the judge, compute the rate;
  baseline (undefended) vs defended.
- **Utility / false positives** — run legitimate traffic and measure how much still
  succeeds under a defense — the over-refusal cost. A defense that refuses everything
  isn't a defense.
