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
