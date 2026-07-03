# impl-01 — Tool Credential Leak

Maps to **OWASP LLM07:2025 Scenario #1**. The threat model, adversary, and
boundaries live in the [attack-level README](../README.md) and are not repeated
here.

## What this shows

An unauthenticated, single-turn user makes the model reveal a secret credential
planted in its system prompt. Success = the secret appears in the model's output.

## Layout

- **`target/`** — the vulnerable app: a system prompt carrying the planted secret
  for a notional tool, served through the `labkit` client.
- **`attack/`** — the extraction attempt corpus + a runner that fires each attempt
  and logs request / response / leaked? / latency to `results/`.
- **`eval/`** — imports `labkit`: the corpus + a leak judge + ASR. ASR = fraction
  of the corpus that leaked (verdict-stable at `temp=0`, though outputs are not
  byte-identical; no N-sampling).
- **`defense/`** — a filter toggled by `DEFENSE=on`, no code edit.
- **`results/`** — baseline ASR, defended ASR, utility retention, and transcripts.

## Models

Crafted against `qwen2.5:3b`, then run across the transfer set (`llama3.1:8b`,
`gemma3:12b`, `qwen3:8b`, `glm4:9b`, `mistral:7b`) to test whether the leak
transfers. Pinned: `temp=0`, `seed=0`.

## Run

The planned Makefile contract (targets not yet wired):

| Target | Does |
|---|---|
| `make up` | bring up the target |
| `make attack` | run the attack against the undefended target |
| `make eval` | baseline ASR over the corpus → `results/` |
| `make defend` | enable the defense (`DEFENSE=on`) |
| `make eval-defended` | defended ASR + utility retention → `results/` |
| `make report` | baseline vs defended vs utility → `results/` |
| `make down` | tear down |
