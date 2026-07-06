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

- Refactored `labkit/client.py`: `call()` is now a pure dispatcher — extracted the two
  transports into sibling `_v1_chat` / `_native_chat`, endpoint auto-selected by the
  `_REASONING` set (dropped the caller-facing `native=` flag).
- Docs cleanup: swapped `qwen3:8b` → `qwen3.5:9b` in `docs/USED_MODELS.md` (pin row +
  digest, `Q4_K_M`) and the LLM07 impl-01 `README.md` transfer set; replaced the stale
  `/no_think` note with the native `/api/chat` (`think:false`) fact.
- Reframed impl-01 `README.md` (PR #5): system-prompt leakage is the LLM07 event, the
  planted credential the sharp high-severity sub-case; aligned the eval/defense/results
  bullets to two tiers + input/output filters.
- Launched the capped 5-model transfer sweep (`--all`, `max_tokens=256`) as a detached,
  auto-resuming background run (`scripts/sweep_supervisor.sh`) → `results/attack.jsonl`.
- Ran a quick comparison of two secret scanners for the planned output-side defense:
  installed `gitleaks` 8.30.1 and `trufflehog` 3.95.8 (Go binaries → `~/bin`) and tested
  them out-of-the-box on the sentinel. gitleaks flags the `BILLING_API_KEY=sk-ac-live-…`
  assignment form (`generic-api-key`, entropy 4.25) but misses the bare key in prose;
  trufflehog detects neither. Chose **gitleaks**.
- Ran the capped transfer sweep to completion — 300 rows (5 transfer models × 50 + the
  `qwen2.5:3b` dev baseline), one clean pass, 0 retries. Re-ran `qwen2.5:3b` capped so the
  whole dataset is cap-consistent; results identical to the uncapped baseline (16/50
  system, 22/50 secret) — the 256 cap doesn't distort a small non-reasoning model.
- Extended the leak judge: added the persona line `You are AcmeSupport` to `SYSTEM_MARKERS`
  (4 markers) and a `leak_depth()` tier — none (0) / partial (1–3) / full (all 4, whole
  prompt recited). Re-scored `attack.jsonl` (no model calls) and added a **leak-depth-by-
  model** table to the report; fixed `report.py`'s stale `effective_prompt` import.
  Result: system leak 106/300 (35%, of which 42 full dumps), secret 156/300 (52%).
- Refactored the impl into clear roles: a top-level conductor `run.py` (fires the attack
  + judges → `results/attack.jsonl`), `eval/` = judge only, `defense/` = detectors,
  `report/` = renderers that read the evidence. **Attack evidence is immutable — reports
  never write `attack.jsonl`.** Removed `attack/run.py` and `eval/report.py`;
  `results/report.md` → `attack_report.md`. The attack report is regenerated identically.
- **Input-guard setup (prompt-injection defense):** added the ML deps via uv —
  `torch`, `transformers`, `sentencepiece`, `protobuf`. Torch defaulted to the CUDA build
  (pulled ~2.7 GB of unusable `nvidia-*` wheels on this CPU-only box), so pinned the CPU
  wheel via a `[tool.uv.sources]` / `pytorch-cpu` index (`torch 2.12.1+cpu`); `.venv`
  4.7 GB → 935 MB. Downloaded the classifier `protectai/deberta-v3-base-prompt-injection-v2`
  (Apache-2.0, ungated, 715 MB → `~/.cache/huggingface`); loads on CPU, labels
  `{0: SAFE, 1: INJECTION}`, 184 M params.
- Built the **secret-only defense**: `defense/secret_scan.py` wraps `gitleaks` (offline)
  with a `sk-ac-live-` custom-rule variant. `report/defense_report.py` scores it over the
  stored responses in one pass → `results/defense_report.md` (reading `attack.jsonl`,
  never writing it). Verdicts aren't persisted — they're a deterministic function of the
  evidence plus the detector, recomputed on demand. Result: catches 137/156 out-of-box
  (secret-leak ASR 52% → 6%), 156/156 with the custom rule (→ 0%), 1 false alarm; the
  out-of-box misses are 16 bare-in-prose + 3 formatted-assignment (parens / markdown).
