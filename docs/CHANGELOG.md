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
