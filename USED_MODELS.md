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
| `qwen3:8b` | Alibaba | Q4_K_M | `sha256:500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41` | Qwen3-8B — run `/no_think` to keep non-reasoning |
| `glm4:9b` | Zhipu | **Q4_0** | `sha256:5b699761eca535dc55047ad9d2dbf54e3b8697709419ef78a70503ed4bfbcf44` | GLM-4-9B-chat (only Q4_0 published on Ollama, not Q4_K_M) |
| `mistral:7b` | Mistral | Q4_K_M | `sha256:6577803aa9a036369e481d648a2baebb381ebc6e897f2bb9a766a2aa7bfbc1cf` | Mistral-7B-Instruct-v0.3 |

All five verified serving over `/v1` (deterministic `pong` reply, `temperature=0`, `seed=0`).
