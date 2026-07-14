# Setup — the shared parts

How the lab is wired: how models are served, the shared `labkit/` code, the per-lab
layout, and how we measure success. No attack logic here.

## Serving

Open-weight models run locally on CPU through Ollama (Q4 quantization), behind a small
OpenAI-compatible client. One model runs at a time; we compare them at the end. Each run
fixes `temperature 0` and `seed 0` so it reproduces. The five models and their exact
versions (tag + digest + quant) are in `docs/USED_MODELS.md`.

## `labkit/` — shared code, no attack logic

- **Model client** (`client.py`) — OpenAI-compatible, single-turn chat with `temp 0`,
  `seed 0` by default. Logs the model and params on every call. Reasoning models are sent
  through the native `/api/chat` path (`think:false`), because the `/v1` endpoint can't
  turn their reasoning off.
- **Response cache** (`cache.py`) — keyed on model + messages + params; returns the cached
  reply unless you bypass it. Generate once on a slow CPU box, then re-judge and re-report
  from the cache instead of re-running the model.

Everything else (corpora, judges, defenses, reports) lives in each lab, not in `labkit/` —
built when a lab needs it, kept small.

## Per-lab layout

Each lab is self-contained: target → attack → judge → defense → measurement. What each
folder holds (LLM07 is the reference):

- `target/` — the small vulnerable app being tested.
- `data/` — the prompts we send (attack prompts, legitimate prompts).
- `results/` — the run evidence (append-only JSONL, **immutable**); only the runner writes it.
- `eval/` — the judge: did the attack succeed?
- `defense/` — the detectors and mitigations.
- `report/` — code that reads the evidence and writes markdown. Verdicts are computed in
  memory and never saved — they're a fixed function of the evidence plus the detector.

## Measurement

- **Judge** — pick the check that matches the attack's goal. Each attack's README defines
  its own (for example: did the leaked value reach a downstream sink, did the model make a
  tool call, did a counter blow past its limit).
- **Attack success rate** — run the attack prompts, apply the judge, compute the rate;
  undefended vs defended.
- **Utility / false positives** — run legitimate traffic and measure how much still gets
  through with a defense on — the over-refusal cost. A defense that refuses everything
  isn't a defense.
