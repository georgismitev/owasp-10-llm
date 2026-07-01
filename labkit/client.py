"""OpenAI-compatible model client. Platform only.

Single-turn chat over Ollama's /v1 endpoint. Determinism defaults
(temperature=0, seed=0) match docs/USED_MODELS.md.
"""
import os
from openai import OpenAI

OLLAMA = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
_client = OpenAI(base_url=f"{OLLAMA}/v1", api_key="ollama")


def call(model: str, prompt: str, *, system: str | None = None,
         temperature: float = 0, seed: int = 0, **params) -> dict:
    """Single-turn chat call. Returns {model, params, output}."""
    messages = ([{"role": "system", "content": system}] if system else []) + \
               [{"role": "user", "content": prompt}]
    resp = _client.chat.completions.create(
        model=model, messages=messages,
        temperature=temperature, seed=seed, **params)
    return {
        "model": model,
        "params": {"temperature": temperature, "seed": seed, **params},
        "output": resp.choices[0].message.content,
    }
