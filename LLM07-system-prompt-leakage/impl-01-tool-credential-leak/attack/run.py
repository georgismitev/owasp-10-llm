"""Attack runner: fire the attempt corpus at the target, print each request and
answer, record a transcript.

Runner only — the attempts live in attempts.py (your substance), and the
authoritative judge + ASR live in eval/. The `leaked` field here is a convenience
indicator for the craft loop, not the measured number.
"""
import sys, pathlib, json, time
_impl = pathlib.Path(__file__).resolve().parents[1]        # the impl-01-… dir
sys.path[:0] = [str(_impl.parents[1]), str(_impl)]         # repo root + impl dir

from target.app import answer, SECRET
from attack.attempts import ATTEMPTS

MODEL = "qwen2.5:3b"
RESULTS = _impl / "results" / "attack.json"


def main():
    rows = []
    for a in ATTEMPTS:
        t0 = time.perf_counter()
        out = answer(a["prompt"], MODEL)["output"]
        latency_ms = round((time.perf_counter() - t0) * 1000)
        leaked = SECRET in out
        print(f"[{a['id']}] technique={a['technique']}  leaked={leaked}  ({latency_ms} ms)")
        print("  REQUEST:", a["prompt"])
        print("  ANSWER :", out)
        print()
        rows.append({"id": a["id"], "technique": a["technique"],
                     "request": a["prompt"], "response": out,
                     "leaked": leaked, "latency_ms": latency_ms, "model": MODEL})

    RESULTS.parent.mkdir(exist_ok=True)
    RESULTS.write_text(json.dumps(rows, indent=2))
    n_leaked = sum(r["leaked"] for r in rows)
    print(f"{n_leaked}/{len(rows)} leaked  →  wrote {RESULTS}")


if __name__ == "__main__":
    main()
