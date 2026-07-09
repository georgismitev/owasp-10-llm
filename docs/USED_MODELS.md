# USED MODELS — serving substrate & pin sheet

Reproducibility facts for the serving layer. No lab content here — this is pure
platform. Every eval run pins to the rows below so results are reproducible.

## Serving

| Fact | Value |
|------|-------|
| Backend | Ollama (llama.cpp), CPU-only |
| Ollama version | 0.31.1 |
| Endpoint | `http://127.0.0.1:11434` — native `/api`, OpenAI-compatible `/v1` |
| Quant | Q4_K_M (GGUF) |
| Machine | 8 vCPU / **4 physical cores**, 32 GB, CPU-only |
| Inference threads | 4 (= physical cores) |
| Determinism defaults | `temperature=0`, `seed=0` |

Determinism verified: same prompt over `/v1` twice → identical output.

## Pinned models

Tags can move upstream; the **sha256 digest** is the real pin.

### Dev model (fast iteration loop)

| Field | Value |
|-------|-------|
| Tag | `qwen2.5:3b` |
| Digest | `sha256:357c53fb659c5076de1d65ccb0b397446227b71a42be9d1603d46168015c9e4b` |
| Quant | Q4_K_M |
| Size | 1.9 GB |

### Transfer set (the 5 — one per maker)

All labs run across these. Digests filled once pulled.

| Tag | Maker | Quant | Digest | Notes |
|-----|-------|-------|--------|-------|
| `llama3.1:8b` | Meta | Q4_K_M | `sha256:46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e` | Llama-3.1-8B-Instruct |
| `gemma3:12b` | Google | Q4_K_M | `sha256:f4031aab637d1ffa37b42570452ae0e4fad0314754d17ded67322e4b95836f8a` | Gemma-3-12b-it |
| `qwen3.5:9b` | Alibaba | Q4_K_M | `sha256:6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7` | Qwen3.5-9B (instruct+reasoning) — reasons by default; labs auto-route it to native `/api/chat` (`think:false`), as `/v1` ignores `think` |
| `glm4:9b` | Zhipu | **Q4_0** | `sha256:5b699761eca535dc55047ad9d2dbf54e3b8697709419ef78a70503ed4bfbcf44` | GLM-4-9B-chat (only Q4_0 published on Ollama, not Q4_K_M) |
| `mistral:7b` | Mistral | Q4_K_M | `sha256:6577803aa9a036369e481d648a2baebb381ebc6e897f2bb9a766a2aa7bfbc1cf` | Mistral-7B-Instruct-v0.3 |

All five verified serving over `/v1` (deterministic `pong` reply, `temperature=0`, `seed=0`);
`qwen3.5:9b` is additionally routed via native `/api/chat` to disable reasoning under a token cap.

## Per-attack inventory

Every model and secret-scanning tool a lab actually exercises, and the role each
serves. Inventory only — roles, not findings; efficacy lives in each lab's reports.
Identifiers are the exact tags / Hugging Face ids used in the code.

### LLM07 — System Prompt Leakage

Target models are the serving pins above (cross-referenced, not repeated). The
detectors below are auxiliary models/tools loaded locally by the defenses; the input
guards score the user prompt, so they are model-agnostic and make no target-model call.

| Identifier | Role in the lab | Where used |
|---|---|---|
| `qwen2.5:3b` | target — dev / fast-iteration model (see *Dev model* above) | `target/app.py` |
| `llama3.1:8b`, `gemma3:12b`, `glm4:9b`, `mistral:7b`, `qwen3.5:9b` | target — transfer set, tests whether the leak transfers (see *Transfer set* above) | `target/app.py` |
| `protectai/deberta-v3-base-prompt-injection-v2` | input guard — prompt-injection classifier | `defense/input_protectai.py`, composed in `defense/input_two_model.py`, compared in `report/input_guard_comparison.py` |
| `patronus-studio/wolf-defender-prompt-injection-small` | input guard — prompt-injection classifier | `defense/input_wolf.py`, composed in `defense/input_two_model.py`, compared in `report/input_guard_comparison.py` |
| `leolee99/PIGuard` | input guard — prompt-injection classifier | `defense/input_piguard.py`, compared in `report/input_guard_comparison.py` |
| `sentence-transformers/all-MiniLM-L6-v2` | output detector — paraphrase/similarity embedding of the response against the system prompt | `defense/output_embedding.py`, `report/embedding_separability.py` |
| `cross-encoder/nli-deberta-v3-small` (44M) | output detector — NLI entailment; flags a response that restates a distinctive system-prompt line | `defense/output_nli_entailment.py`, `report/nli_separability.py`, `report/paraphrase_eval.py` |
| `cross-encoder/quora-roberta-base` (125M) | output detector — duplicate-question model trialed as an alternative to NLI; inert on our declarative lines | `report/paraphrase_eval.py` |
| `gitleaks` (CLI tool, **not a model**) | output detector — secret scanner over the response | `defense/output_secret_scan.py` |

The remaining output-side detectors are deterministic and use **no model**:
`defense/output_credential.py` (normalize + decode-ladder exact match against the known
key) and `defense/output_literal_match.py` (verbatim substring match).
