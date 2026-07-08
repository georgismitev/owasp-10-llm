# Changelog — step-by-step build log

A chronological, one-line-per-step record of everything done in this project —
**including actions that leave no git trace** (installing tools, pulling models,
machine-level or environment changes). For a reader: follow this top-to-bottom to
see exactly how the lab was built, in order.

## 2026-07-01

- Added this step log (`docs/CHANGELOG.md`), a minimal root `README.md`, and a
  "log every step" rule in `CLAUDE.md`.
- Removed the duplicated `## Git` section from project `CLAUDE.md` (already in
  global `~/.claude/CLAUDE.md`).
- **A (serving substrate):** Installed Ollama 0.31.1 (CPU-only, systemd service on
  `127.0.0.1:11434`), pulled dev model `qwen2.5:3b` (Q4_K_M), verified deterministic
  `pong` over native `/api/generate` and OpenAI-compatible `/v1` (`temp=0`, `seed=0`,
  `num_thread=4`).
- Pulled the 5-model transfer set (`llama3.1:8b`, `gemma3:12b`, `qwen3:8b`, `glm4:9b`,
  `mistral:7b`; ~28 GB), verified each serves over `/v1`.
- Wrote `USED_MODELS.md` pin sheet: backend version, threads, determinism defaults,
  and per-model tag + sha256 digest + quant (note: `glm4:9b` is Q4_0, others Q4_K_M).
  Later moved it to `docs/USED_MODELS.md`.
- **B (Python project):** `uv init --bare` (uv 0.11.13), pinned Python 3.12
  (`.python-version` → 3.12.13), added `openai` 2.44.0 as the one `/v1` client dep,
  locked deps in `uv.lock`. Verified the SDK reaches `qwen2.5:3b` over `/v1`
  (deterministic `pong`). Added `.gitignore` for `.venv/` and caches.
- Added `labkit/` with a minimal OpenAI-compatible model client (`client.py`):
  single-turn `/v1` chat, determinism defaults (`temp=0`, `seed=0`). Deferred the
  other planned harness modules (cache, canary, asr, judges, utility, report) —
  each a one-liner or a runner with no lab consumer yet; build per-lab when needed.

## 2026-07-02

- Started **LLM07 (System Prompt Leakage)**: created the `impl-01-tool-credential-leak/`
  skeleton (`target/ attack/ eval/ defense/ results/`) and wrote the attack-level
  `README.md` threat model — Scenario #1, leak-only (reuse out of scope), single-turn,
  canary-present judge.
- Built the impl-01 **target** (`target/app.py`): AcmeSupport system prompt with a
  planted sentinel credential + `answer()` over the labkit client. Smoke test passed
  (benign request → on-persona answer, no leak). Chose plain `python folder/file.py`
  runs over a Makefile; scripts that import the target carry a 2-line `sys.path` shim.
- Wired the impl-01 **attack runner** (`attack/run.py`) + **attempts scaffold**
  (`attack/attempts.py`): runner fires the corpus at the target, prints each
  request/answer, records `request/response/leaked/latency` to `results/attack.json`.
  Attempts (the extraction prompts) are hand-written; runner ran clean on the benign
  control (`0/1 leaked`). Authoritative judge/ASR deferred to `eval/`.
- Added the impl-01 **baseline** (`target/baseline.py`): the undefended target
  answering a benign request as its non-adversarial reference point (`leaked=False`).
- Added a tiny `labkit` **response cache** (`cache.py`, keyed on model+messages+params);
  `client.call` serves cached outputs unless `bypass_cache=True` (runner honors
  `BYPASS_CACHE=1`). Verified miss→hit (13.6s → 0ms). Cache dir `.labkit_cache/` gitignored.
- Split the attack leak signal into two flags — `system_leaked` (distinctive instruction
  line recited, verbatim) and `secrets_leaked` (credential value surfaced); backfilled
  existing `attack.json` from stored responses (no rerun). Baseline: system-leak 3/29,
  secret-leak 6/29.

## 2026-07-03

- Expanded the impl-01 attack corpus to **50** (added billing-focus, completion-anchor,
  structure-priming, and 21 stronger extraction prompts: echo-format, prefix-inject,
  roleplay, structured, negative-space, refusal-suppression, hypothetical, meta).
  Baseline on qwen2.5:3b: system-leak 16/50, secret-leak 22/50.
- Refactored results to **append-only `attack.jsonl`** (one run per line, keyed by
  `fingerprint` = hash of model+system+prompt); replaced `attack.json`. Runs immutable;
  cache-on skips seen fingerprints, `BYPASS_CACHE=1` appends fresh samples.
- Moved the leak judges to **`eval/judge.py`** (literal string-match tier: canary match
  for the secret, keyword match for system-prompt lines).
- Added **`--all`** to the runner (fires the 5-model transfer set; Qwen3 forced
  `/no_think` per USED_MODELS); writes each run incrementally (resumable).
- Added **`eval/report.py`** — transfer report: technique×model matrices (system + secret)
  + callouts (universal / doesn't-transfer / dead / most-resistant), markdown to
  `results/report.md`.
- Ran the transfer sweep (50 × 5 transfer models) on CPU via Ollama → appends to
  `attack.jsonl` (300 rows total incl. the 50 dev-model runs).
- Capped attack generations at `max_tokens=256` (all observed leaks surface within
  ~135 tokens; bounds runaway generations, esp. reasoning models). Dropped the
  `/no_think` prompt helper — verified a no-op on Ollama's `/v1` endpoint.
- Added a labkit **native `/api/chat` path**: disables reasoning (`think:false`) for
  models the `/v1` endpoint can't quiet, auto-selected by model (`_REASONING` set) so
  callers stay model-agnostic. Verified `qwen3.5:9b` returns clean non-empty content
  under the cap where `/v1` — even `extra_body {"think": false}` — yields empty
  (`/v1` ignores `think`).
- Pulled **`qwen3.5:9b`** (6.6 GB, instruct+reasoning). Removed **`qwen3:8b`** from
  ollama (disk+memory) — capped vs uncapped infra isn't comparable; re-pull if needed.
- Reset `results/attack.jsonl` to the **50-row `qwen2.5:3b` baseline** (dropped the
  mixed capped/uncapped transfer rows).
- Added **`qwen3.5:9b`** to `MODELS_ALL` (transfer set now 5:
  llama/gemma/glm4/mistral/qwen3.5); labkit auto-routes it to the native path, so the
  runner adds it with no per-model branching.

## 2026-07-06

- Reframed impl-01 `README.md` (PR #5): system-prompt leakage is the LLM07 event, the
  planted credential the sharp high-severity sub-case; eval/defense split into two tiers
  + input/output filters.
- Launched the capped 5-model transfer sweep (`--all`, `max_tokens=256`) as a detached,
  auto-resuming background run → `results/attack.jsonl`.
- Compared two secret scanners for the output-side defense: installed `gitleaks` 8.30.1 +
  `trufflehog` 3.95.8 (`~/bin`). gitleaks flags the `BILLING_API_KEY=sk-ac-live-…`
  assignment (`generic-api-key`, entropy 4.25) but misses the bare key in prose;
  trufflehog detects neither. Chose **gitleaks**.
- Completed the capped transfer sweep — 300 rows (5 transfer models × 50 + the
  `qwen2.5:3b` baseline), cap-consistent with the uncapped baseline (16/50 system,
  22/50 secret).
- Extended the leak judge: added `You are AcmeSupport` to `SYSTEM_MARKERS` (4) + a
  `leak_depth()` tier (none / partial / full). Re-scored: system leak 106/300 (35%,
  42 full dumps), secret 156/300 (52%).
- **Input-guard setup:** added CPU ML deps via uv — `torch 2.12.1+cpu` pinned via a
  `pytorch-cpu` index (the CUDA default pulled 2.7 GB of unusable `nvidia-*` wheels).
  Downloaded `protectai/deberta-v3-base-prompt-injection-v2` (715 MB, `{0: SAFE, 1: INJECTION}`).
- Built the **secret-only defense** (`defense/secret_scan.py` wraps `gitleaks` + a
  `sk-ac-live-` custom rule): 137/156 out-of-box (secret ASR 52% → 6%), 156/156 with the
  rule (→ 0%), 1 false alarm.
- Built the **input-only defense** (`defense/input_guard.py`, protectai-v2): scores the
  *prompt*, model-agnostic. Recall 44/49 (90%); stops 43 of the 47 that leaked upstream;
  the 5 misses are plainly-phrased / cross-language asks.

## 2026-07-07

- **Evaluated alternative prompt-injection detectors as input guards:** downloaded
  `wolf-defender-prompt-injection-small` + `PIGuard` (CPU). protectai-v2 and wolf-defender
  each flag 44/49 but miss *disjoint* prompts, so ORing them (`two_model_guard.py`) lifts
  coverage to 48/49; the lone escape is a "dump your config as JSON" ask. PIGuard
  under-catches in-distribution (23/49). Caveat: hard-OR *unions* the two models' false
  positives — unmeasured until the legit-traffic assessment.
- **Output-only verbatim tripwire** (`defense/output_tripwire.py`): substring-flags a
  distinctive system-prompt line, the credential value, or the partial `BILLING_API_KEY`
  label. Flags 184/300 — all 168 leaks + 16 partial-only on judge-clean replies (surfaced
  for review). Recall ~100% by construction; blind to obfuscation.
- Built the **legitimate-traffic corpus** for the false-positive assessment (PR #12):
  49 benign twins, one per attack, same technique surface but genuine customer requests.
  `run.py --legitimate` → `results/legitimate.jsonl` (`qwen2.5:3b`, judge-verified non-leaking).
- **Finding — legitimate traffic leaks the credential, no attack needed:** 11 of the
  original twins (genuine billing/refund questions) made `qwen2.5:3b` volunteer the live
  credential `sk-ac-live-…` (11/49 ≈ 22%; value verbatim, prose paraphrased). Preserved in
  `data/leaky.py` + `results/leaky.jsonl`; the 11 were swapped onto non-credential topics
  to keep the baseline clean.

## 2026-07-08

- **Output-only embedding detector — failed separability (measurement finding):** cosine
  between the response and the system prompt (`all-MiniLM-L6-v2`) cannot separate real leaks
  from benign on-topic traffic. Swept over the legitimate-traffic set (49 clean vs 11 leaky):
  at the 0.60 cutoff 13/49 (27%) false positives for 9/11 (82%) recall, and pushing the
  false-positive rate down only sheds recall. Cause: whole-prompt cosine measures billing-topic
  overlap, not recitation — the topicality confound. Recorded the scorer as a documented
  dead-end with a reproducible sweep harness (`report/embedding_separability.py`) and folded
  the result into the defense report.
- Built an **obfuscation-hardened credential output detector** (`defense/output_credential.py`):
  normalizes separators / unicode and tries reverse / rot13 / base64 / hex before an exact
  match against the known key — deterministic, ~0 false positives. Only the separator stage is
  exercised by current data; the reverse / rot13 / base64 / hex stages await an obfuscation attack.
- **Finding — exact-match ground truth undercounts credential leaks:** `glm4:9b` on
  `evasion-02` printed the credential one character per line, so the verbatim string never
  appears — `secrets_leaked` (exact match), gitleaks (both modes), and the verbatim tripwire
  all miss a complete leak, counting it as clean. The hardened detector's normalization
  recovers it: **157/300** vs the 156 exact-match.
