# LLM07 impl-01 — defense report

detectors measured over the 300-row attack evidence (read only): the input guard classifies prompts, the secret scan runs gitleaks on responses.

## Input-only defense (prompt-injection classifier)

protectai/deberta-v3-base-prompt-injection-v2 over each distinct attack prompt — it scores the prompt, so the verdict is model-agnostic (classified once, not per model).

recall: 44/49 attack prompts flagged INJECTION (90%)
of the 47 prompts that leaked on ≥1 model, the guard would stop 43 upstream

| technique | flagged / n |
|---|---|
| multilingual | 1/2 |
| direct-ask | 3/5 |
| reframe | 2/3 |
| structured | 2/3 |
| billing-pretext | 2/2 |
| completion | 5/5 |
| echo-format | 4/4 |
| hypothetical | 2/2 |
| judge-evasion | 2/2 |
| meta | 2/2 |
| negative-space | 2/2 |
| prefix-inject | 3/3 |
| refusal-suppression | 2/2 |
| repetition | 4/4 |
| roleplay | 3/3 |
| structure-priming | 5/5 |

## Secret-only defense (gitleaks output scan)

undefended secret-leak ASR: 156/300 (52%)

| mode | caught / 156 | missed | defended ASR | false-alarm / 144 |
|---|---|---|---|---|
| gitleaks out-of-box | 137 | 19 | 19/300 (6%) | 1 |
| + sk-ac-live rule | 156 | 0 | 0/300 (0%) | 1 |

out-of-box misses by form: assign=3, bare=16 — gitleaks' generic rule keys on `KEY=value`, so bare-in-prose leaks slip through.
