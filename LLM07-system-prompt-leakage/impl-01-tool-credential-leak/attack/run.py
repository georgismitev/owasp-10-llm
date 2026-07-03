"""Attack runner: fire the attempt corpus at the target and append runs.

Append-only log at results/attack.jsonl — one JSON object per line, one per run.
A run is keyed by its fingerprint = the labkit call key (model + system prompt +
prompt + params), so a changed prompt or system prompt never reuses a stale run.
Existing runs are never modified. (id/technique/model are readable columns, not
part of the key — model already lives inside the fingerprint.)

- cache-on (default): append a run only if this fingerprint is unseen.
- BYPASS_CACHE=1: always append a fresh run (accumulates samples).

Runner only — attempts live in attempts.py; authoritative judging lives in eval/.
"""
import os, sys, pathlib, json, hashlib
_impl = pathlib.Path(__file__).resolve().parents[1]        # the impl-01-… dir
sys.path[:0] = [str(_impl.parents[1]), str(_impl)]         # repo root + impl dir

from target.app import answer, SYSTEM_PROMPT
from attack.attempts import ATTEMPTS
from eval.judge import system_leaked, secrets_leaked

MODEL = "qwen2.5:3b"                                       # default: the dev model
MODELS_ALL = ["llama3.1:8b", "gemma3:12b", "qwen3:8b", "glm4:9b", "mistral:7b"]  # --all: the transfer set
RESULTS = _impl / "results" / "attack.jsonl"
BYPASS = os.environ.get("BYPASS_CACHE") == "1"             # BYPASS_CACHE=1 to append a fresh sample
ALL = "--all" in sys.argv                                  # --all: run the transfer set, else the dev model


def effective_prompt(model, prompt):
    """Qwen3 is dual-mode; force non-reasoning per docs/USED_MODELS.md."""
    return prompt + " /no_think" if model.startswith("qwen3") else prompt


def fingerprint(model, prompt):
    """The labkit call key (model + system + prompt + params), hashed."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}]
    blob = json.dumps({"model": model, "messages": messages,
                       "temperature": 0, "seed": 0, "params": {}}, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def load_runs():
    if not RESULTS.exists():
        return []
    return [json.loads(line) for line in RESULTS.read_text().splitlines() if line.strip()]


def main():
    seen = {r["fingerprint"] for r in load_runs()}
    models = MODELS_ALL if ALL else [MODEL]
    n = 0
    with RESULTS.open("a") as f:                            # append+flush each run: resumable, visible
        for model in models:
            for a in ATTEMPTS:
                sent = effective_prompt(model, a["prompt"])
                fp = fingerprint(model, sent)
                if not BYPASS and fp in seen:
                    continue
                out = answer(sent, model, bypass_cache=BYPASS, max_tokens=256)["output"]
                rec = {"id": a["id"], "technique": a["technique"], "model": model,
                       "fingerprint": fp, "prompt": a["prompt"], "response": out,
                       "system_leaked": system_leaked(out), "secrets_leaked": secrets_leaked(out)}
                f.write(json.dumps(rec) + "\n")
                f.flush()
                seen.add(fp)
                n += 1
                print(f"[{model} {a['id']}] system={rec['system_leaked']} secret={rec['secrets_leaked']}", flush=True)
    print(f"appended {n} runs  →  {RESULTS}")


if __name__ == "__main__":
    main()
