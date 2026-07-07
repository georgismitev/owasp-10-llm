# Handover — run-to-run state

The doc we hand between runs, and update at session wrap-up. It records **current state
and next-step titles + status only** — never execution plans, recipes, or "next / go"
framing (see `CLAUDE.md` rule #1). The *what* and *where it stands*, not the *how*; the
how is decided with the lead when the step is taken up.

## Current state — LLM07 impl-01 (tool-credential leak)

The first flagship: **system-prompt leakage**, with a planted tool credential as the
sharp high-severity sub-case. All merged work is on `main`.

**Built:**
- Attack corpus + baseline — 50 attempts × 6 models = 300 rows. Baseline: system-leak
  106/300, secret-leak 156/300.
- Secret-only defense (gitleaks).
- Input-only defense (prompt-injection classifier) — single-model and two-model variants.
- Output-only verbatim tripwire.
- Legitimate-traffic corpus (49 clean) and the finding that benign billing traffic makes
  the dev model volunteer the credential (11/49, no attack).

**Open:**
- Output-only embedding detector — scorer built; separability is negative on this target
  (uncommitted, under review).
- Combined defense (input + output + secret).
- Legitimate-traffic false-positive report.
- Unicode / obfuscation evasion attack.
- Vendor-benchmark reframe writeup.
- Deferred: remove the now-redundant `control-01` benign prompt from the attack corpus;
  reconcile any stale runtime-toggle framing in the README.
