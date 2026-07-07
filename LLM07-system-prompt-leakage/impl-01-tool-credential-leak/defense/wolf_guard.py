"""Input-only defense: wolf-defender prompt-injection classifier.

Wraps patronus-studio/wolf-defender-prompt-injection-small (local, CPU; multilingual
ModernBERT/mmBERT). flag() returns True when the classifier predicts INJECTION. Detection
only — it scores the user prompt, so it is model-agnostic and makes no target-model call.
Composed with the protectai guard in two_model_guard.py.
"""
import functools
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

MODEL = "patronus-studio/wolf-defender-prompt-injection-small"
INJECTION_LABEL = 1        # opaque LABEL_0/LABEL_1; probed LABEL_1 = INJECTION


@functools.lru_cache(maxsize=1)
def _model():
    tok = AutoTokenizer.from_pretrained(MODEL)
    mod = AutoModelForSequenceClassification.from_pretrained(MODEL).eval()
    return tok, mod


def flag(prompt: str) -> bool:
    """True if the classifier labels the prompt INJECTION (argmax == INJECTION_LABEL)."""
    tok, mod = _model()
    inputs = tok(prompt, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        logits = mod(**inputs).logits
    return int(logits.argmax()) == INJECTION_LABEL
