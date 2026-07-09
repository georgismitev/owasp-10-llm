# Handover — run-to-run state

The doc we hand between runs, and update at session wrap-up. It records **current state
and next-step titles + status only** — never execution plans, recipes, or "next / go"
framing (see `CLAUDE.md` rule #1). The *what* and *where it stands*, not the *how*; the
how is decided with the lead when the step is taken up.

Detail lives in the md files, not here: `LLM07-system-prompt-leakage/report/` (attack and
defense reports, with the numbers), `docs/CHANGELOG.md` (the AI-security log), and
`docs/USED_MODELS.md` (models + serving substrate).

## Current state — LLM07 (System Prompt Leakage)

The first flagship: system-prompt leakage, with a planted tool credential as the sharp
high-severity sub-case. All merged work is on `main`.

**Built** (numbers in the reports):
- Attack corpus + baseline — 50 attempts × 6 models = 300 rows.
- Legitimate-traffic corpus (49 clean) + the finding that benign billing traffic makes the
  dev model volunteer the credential (11/49) with no attack.
- Secret-only defense — gitleaks output scan.
- Input-only defense — prompt-injection classifier, single-model and two-model variants,
  plus a head-to-head trial of alternative guards.
- Output-only credential detector — deterministic normalize + decode-ladder + exact match.
- Output-only literal (verbatim) system-prompt match.
- Output-only embedding cosine — failed separability (topicality confound); kept as a
  documented dead-end.
- Output-only NLI entailment detector + a 50-prompt paraphrase probe set. Verdict: not
  shipped as its own layer — low false alarms, but verbatim is already covered and it
  misses genuine rewording.
- Corpus format validator + PostToolUse hook (platform).

**Open** (titles + status only):
- Distinctive-line lexical detector (ROUGE-L / LCS) — not started.
- Combined defense (input + output + secret) — not started.
- Legitimate-traffic false-positive report (all detectors) — partial; per-detector false
  positives exist in the defense report, not yet consolidated into one writeup.
- Unicode / obfuscation evasion attack — not started.
- Vendor-benchmark reframe writeup for the input guard — not started.
- Deferred: remove the now-redundant `control-01` benign prompt from the attack corpus.
