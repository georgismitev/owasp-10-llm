"""Input-only defense: PIGuard prompt-injection classifier.

Wraps leolee99/PIGuard (local, CPU; a DeBERTa-v2 subclass that needs trust_remote_code —
the custom code is a benign CLS-pooling head). flag() returns True when the classifier
predicts INJECTION. Detection only — it scores the user prompt, so it is model-agnostic and
makes no target-model call.
"""
import functools
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

MODEL = "leolee99/PIGuard"
INJECTION_LABEL = 1        # id2label {0: benign, 1: injection}


@functools.lru_cache(maxsize=1)
def _model():
    tok = AutoTokenizer.from_pretrained(MODEL)
    mod = AutoModelForSequenceClassification.from_pretrained(MODEL, trust_remote_code=True).eval()
    return tok, mod


def flag(prompt: str) -> bool:
    """True if the classifier labels the prompt INJECTION (argmax == INJECTION_LABEL)."""
    tok, mod = _model()
    inputs = tok(prompt, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        logits = mod(**inputs).logits
    return int(logits.argmax()) == INJECTION_LABEL
