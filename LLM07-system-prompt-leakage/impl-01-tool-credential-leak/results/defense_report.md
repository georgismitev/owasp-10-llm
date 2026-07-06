# LLM07 impl-01 — defense report

detector fire-counts over 300 stored responses · no model calls.

## Secret-only defense (gitleaks output scan)

undefended secret-leak ASR: 156/300 (52%)

| mode | caught / 156 | missed | defended ASR | false-alarm / 144 |
|---|---|---|---|---|
| gitleaks out-of-box | 137 | 19 | 19/300 (6%) | 1 |
| + sk-ac-live rule | 156 | 0 | 0/300 (0%) | 1 |

out-of-box misses by form: assign=3, bare=16 — gitleaks' generic rule keys on `KEY=value`, so bare-in-prose leaks slip through.
