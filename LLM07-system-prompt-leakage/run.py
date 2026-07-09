"""Conductor: fire a corpus at the target and judge each response; append the
evidence to results/. Wiring only — no attack/judge logic of its own.

  python run.py                 fire the attack corpus at the dev model (qwen2.5:3b)
  python run.py --all           fire the attack corpus at the transfer set
  python run.py --legitimate    fire the legitimate corpus (add --all for the transfer set)
  python run.py --paraphrase    fire the paraphrase corpus at the dev model

The judge runs on every response either way — a legitimate prompt that elicits a leak
is exactly what we want recorded. Append-only, one JSON object per run, keyed by
fingerprint (model + system + prompt + params) so a changed prompt never reuses a
stale run and reruns are resumable.
"""
import os, sys, pathlib, json, hashlib, subprocess
_impl = pathlib.Path(__file__).resolve().parent           # the lab dir
sys.path[:0] = [str(_impl.parents[0]), str(_impl)]        # repo root + lab dir

from target.app import answer, SYSTEM_PROMPT
from data.attack import ATTEMPTS
from data.legitimate import LEGITIMATE
from data.paraphrase import PARAPHRASE
from eval.judge import system_leaked, secrets_leaked, leak_depth

MODEL = "qwen2.5:3b"                                       # default: the dev model
MODELS_ALL = ["llama3.1:8b", "gemma3:12b", "glm4:9b", "mistral:7b", "qwen3.5:9b"]  # --all: transfer set
BYPASS = os.environ.get("BYPASS_CACHE") == "1"
ALL = "--all" in sys.argv
RUN_LEGITIMATE = "--legitimate" in sys.argv               # run the legitimate corpus instead of the attack corpus
RUN_PARAPHRASE = "--paraphrase" in sys.argv               # run the paraphrase corpus (output-detector eval)
CORPUS = PARAPHRASE if RUN_PARAPHRASE else LEGITIMATE if RUN_LEGITIMATE else ATTEMPTS
RESULTS = _impl / "results" / ("paraphrase.jsonl" if RUN_PARAPHRASE
                               else "legitimate.jsonl" if RUN_LEGITIMATE else "attack.jsonl")


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
    """Fire the corpus at the target and judge each response (append-only, resumable)."""
    seen = {r["fingerprint"] for r in load_runs()}
    models = MODELS_ALL if ALL else [MODEL]
    n = 0
    with RESULTS.open("a") as f:
        for model in models:
            for a in CORPUS:
                fp = fingerprint(model, a["prompt"])
                if not BYPASS and fp in seen:
                    continue
                out = answer(a["prompt"], model, bypass_cache=BYPASS, max_tokens=256)["output"]
                label = {"pair": a["pair"]} if RUN_LEGITIMATE else {"technique": a["technique"]}
                rec = {"id": a["id"], **label, "model": model,
                       "fingerprint": fp, "prompt": a["prompt"], "response": out,
                       "system_leaked": system_leaked(out), "secrets_leaked": secrets_leaked(out),
                       "leak_depth": leak_depth(out)}
                f.write(json.dumps(rec) + "\n")
                f.flush()
                seen.add(fp)
                n += 1
                print(f"[{model} {a['id']}] system={rec['system_leaked']} secret={rec['secrets_leaked']}", flush=True)
    print(f"appended {n} runs  →  {RESULTS}")
    # format-check what we just wrote — the Write/Edit hook can't see this Bash-driven write
    subprocess.run([sys.executable, str(_impl.parents[0] / "scripts" / "validate_corpus_format.py"), str(RESULTS)])


if __name__ == "__main__":
    main()
