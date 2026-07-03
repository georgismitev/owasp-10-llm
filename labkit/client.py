"""OpenAI-compatible model client. Platform only.

Single-turn chat over Ollama's /v1 endpoint. Determinism defaults
(temperature=0, seed=0) match docs/USED_MODELS.md. Responses are cached on disk;
pass bypass_cache=True to force a fresh call.
"""
import os, json
from openai import OpenAI
from . import cache

OLLAMA = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
_client = OpenAI(base_url=f"{OLLAMA}/v1", api_key="ollama")


def call(model: str, prompt: str, *, system: str | None = None,
         temperature: float = 0, seed: int = 0, bypass_cache: bool = False,
         **params) -> dict:
    """Single-turn chat call. Returns {model, params, output, cached}."""
    messages = ([{"role": "system", "content": system}] if system else []) + \
               [{"role": "user", "content": prompt}]
    key = json.dumps({"model": model, "messages": messages,
                      "temperature": temperature, "seed": seed, "params": params},
                     sort_keys=True)
    output = None if bypass_cache else cache.get(key)
    cached = output is not None
    if not cached:
        resp = _client.chat.completions.create(
            model=model, messages=messages,
            temperature=temperature, seed=seed, **params)
        output = resp.choices[0].message.content
        cache.set(key, output)
    return {
        "model": model,
        "params": {"temperature": temperature, "seed": seed, **params},
        "output": output,
        "cached": cached,
    }
