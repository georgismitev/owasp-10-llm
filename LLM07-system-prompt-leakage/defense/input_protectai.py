"""Input-only defense: protectai-v2 prompt-injection classifier.

Wraps protectai/deberta-v3-base-prompt-injection-v2 (local, CPU). flag() returns
True when the classifier predicts INJECTION. Detection only — it scores the user
prompt, so it is model-agnostic (independent of which target model would answer)
and makes no target-model call. No blocking or rewriting here. Composed with the
wolf-defender guard in input_two_model.py.
"""
import functools
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

MODEL = "protectai/deberta-v3-base-prompt-injection-v2"   # labels {0: SAFE, 1: INJECTION}


@functools.lru_cache(maxsize=1)
def _model():
    tok = AutoTokenizer.from_pretrained(MODEL)
    mod = AutoModelForSequenceClassification.from_pretrained(MODEL).eval()
    return tok, mod


def flag(prompt: str) -> bool:
    """True if the classifier labels the prompt INJECTION (argmax over SAFE/INJECTION)."""
    tok, mod = _model()
    inputs = tok(prompt, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        logits = mod(**inputs).logits
    return mod.config.id2label[int(logits.argmax())] == "INJECTION"
