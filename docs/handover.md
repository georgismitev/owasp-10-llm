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
- Output-only detector, next attempt — the naive embedding cosine failed (topicality
  confound; scorer left uncommitted, untracked). Alternatives researched (see *Research*
  below); direction and design **not yet decided**.
- Combined defense (input + output + secret).
- Legitimate-traffic false-positive report.
- Unicode / obfuscation evasion attack.
- Vendor-benchmark reframe writeup.
- Deferred: remove the now-redundant `control-01` benign prompt from the attack corpus;
  reconcile any stale runtime-toggle framing in the README.

## Research — output detector alternatives

Two background agents surveyed output-side detection for system-prompt / credential
leakage. This is a **survey to inform the design** — the design itself is decided with the
lead when the work is taken up, not a plan to run. Both agents converged.

**Reframe — two leak signals, two detectors:**
- The **credential** is high-entropy and un-paraphrasable → a deterministic
  normalize + decode-ladder + fuzzy-match against the known key catches ~all obfuscations
  at ~0 false positives. No ML.
- The **distinctive instruction lines** are paraphrasable and share the billing topic →
  this is where the topicality confound lives; it needs a *directional* signal, not similarity.

**Guardrail models are the wrong tool.** Llama Guard, ShieldGemma, Granite Guardian,
Prompt Guard — none has a system-prompt-leak or secret/credential category (they are harm
classifiers; Prompt Guard is input-only). The "output leak" features in LLM Guard /
Guardrails AI / NeMo are regex + detect-secrets/Presidio — verbatim-only. Only Lakera does
it directly, and it is a closed hosted API.

**Promising direction — score against the distinctive lines only, not the whole prompt:**
- Verbatim / near-verbatim: a lexical channel (ROUGE-L / LCS) per distinctive line —
  literature-backed (Agarwal et al. 2024 score ROUGE-L per block and beat a GPT-4 judge,
  recall 1.0).
- Paraphrase: a cross-encoder scored per response-sentence × line, take the max — NLI
  entailment (`cross-encoder/nli-deberta-v3-small`, 44M) and/or duplicate-question
  (`cross-encoder/quora-roberta-base`, 125M, scores restatement, not topicality). Avoid
  relevance rerankers — they measure topicality and reintroduce the confound. Mechanism:
  reciting one line spikes max-similarity to *that* line; on-topic answers stay diffuse —
  which whole-prompt cosine washed out.
- A bi-encoder line-level max-cosine (`bge-small-en-v1.5`, MIT) is a cheaper pre-filter
  but symmetric → weaker FP control than NLI.

**LLM-as-judge — secondary only.** Small CPU judges get jailbroken by the content they
inspect (~31–73% attack success, worse when smaller) and are unstable. The lever is
*reference grounding* (we hold the gold lines + key): reframe to "does this reveal ANY of
these specific lines?" → agreement κ ≈ 0.63–0.96. If used at all: a 7–9B grounded
binary-JSON judge (e.g. Qwen2.5-7B, Q4) as a tie-breaker, never the gate.

**Caveats:** validate any threshold on our 49-clean + 11-leaky set before trusting it —
the FP risks are benign refusals ("I cannot reveal the key") and answers that correctly
state a public policy. A few 2025–2026 arXiv IDs were flagged unverifiable and excluded.
All named models are open-weight, ungated, and CPU-feasible.
