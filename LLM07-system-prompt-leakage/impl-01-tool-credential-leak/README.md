# impl-01 — Tool Credential Leak

Maps to **OWASP LLM07:2025 Scenario #1**. The threat model, adversary, and
boundaries live in the [attack-level README](../README.md) and are not repeated
here.

## What this shows

An unauthenticated, single-turn user makes the model leak its **system prompt** —
the LLM07 event. This scenario (#1) plants a tool **credential** in that prompt,
so the leak has two tiers: the system-prompt text (persona / rules) recited, and
the sharp sub-case where the exact planted credential surfaces. Success = either
tier appears in the output; the credential is the high-severity,
objectively-detectable case.

## Layout

- **`target/`** — the vulnerable app: a system prompt carrying the planted secret
  for a notional tool, served through the `labkit` client.
- **`attack/`** — the extraction attempt corpus + a runner that fires each attempt
  and logs request / response / leaked? / latency to `report/`.
- **`eval/`** — imports `labkit`: the corpus + a two-tier leak judge (system-prompt
  text; the credential sub-case) + ASR per tier (verdict-stable at `temp=0`, though
  outputs are not byte-identical; no N-sampling).
- **`defense/`** — input- and output-side filters targeting system-prompt leakage
  (both tiers), toggled by `DEFENSE=on`, no code edit.
- **`report/`** — the attack evidence (`attack.jsonl`, immutable), the report generators,
  and the reports they render (`attack_report.md`, `defense_report.md`,
  `input_guard_comparison.md`).

## Models

Crafted against `qwen2.5:3b`, then run across the transfer set (`llama3.1:8b`,
`gemma3:12b`, `glm4:9b`, `mistral:7b`, `qwen3.5:9b`) to test whether the leak
transfers. Pinned: `temp=0`, `seed=0`.

## Run

The planned Makefile contract (targets not yet wired):

| Target | Does |
|---|---|
| `make up` | bring up the target |
| `make attack` | run the attack against the undefended target |
| `make eval` | baseline ASR over the corpus → `report/` |
| `make defend` | enable the defense (`DEFENSE=on`) |
| `make eval-defended` | defended ASR + utility retention → `report/` |
| `make report` | baseline vs defended vs utility → `report/` |
| `make down` | tear down |
