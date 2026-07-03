"""OpenAI-compatible model client. Platform only.

Single-turn chat over Ollama's /v1 endpoint. Determinism defaults
(temperature=0, seed=0) match docs/USED_MODELS.md. Responses are cached on disk;
pass bypass_cache=True to force a fresh call.
"""
import os, json, urllib.request
from openai import OpenAI
from . import cache

OLLAMA = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
_client = OpenAI(base_url=f"{OLLAMA}/v1", api_key="ollama")


def _native_chat(model, messages, temperature, seed, num_predict):
    """Ollama native /api/chat with reasoning disabled (think:false). The /v1 endpoint
    ignores `think`, so reasoning models (e.g. qwen3.5) must use this path to avoid
    empty output when truncated at a token cap."""
    body = {"model": model, "messages": messages, "stream": False, "think": False,
            "options": {"temperature": temperature, "seed": seed}}
    if num_predict is not None:
        body["options"]["num_predict"] = num_predict
    req = urllib.request.Request(f"{OLLAMA}/api/chat", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r)["message"]["content"]


def call(model: str, prompt: str, *, system: str | None = None,
         temperature: float = 0, seed: int = 0, bypass_cache: bool = False,
         native: bool = False, **params) -> dict:
    """Single-turn chat call. Returns {model, params, output, cached}.
    native=False: OpenAI /v1 endpoint. native=True: Ollama /api/chat with reasoning
    disabled — for reasoning models the /v1 endpoint can't quiet."""
    messages = ([{"role": "system", "content": system}] if system else []) + \
               [{"role": "user", "content": prompt}]
    key_obj = {"model": model, "messages": messages,
               "temperature": temperature, "seed": seed, "params": params}
    if native:
        key_obj["native"] = True
    key = json.dumps(key_obj, sort_keys=True)
    output = None if bypass_cache else cache.get(key)
    cached = output is not None
    if not cached:
        if native:
            output = _native_chat(model, messages, temperature, seed, params.get("max_tokens"))
        else:
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
