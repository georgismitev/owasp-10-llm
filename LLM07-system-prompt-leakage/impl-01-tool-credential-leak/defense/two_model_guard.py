"""Two-model input defense: flag a prompt if EITHER prompt-injection classifier fires.

A second input-guard variant beside the single-model input_guard. It ORs the incumbent
protectai-v2 (via input_guard.flag) with patronus wolf-defender — the two miss largely
disjoint prompts, so the union catches more (48/49 on the attack corpus vs 44/49 each).
Detection only, model-agnostic (scores the prompt), no target-model call.

Hard-label OR: max recall, but it also unions the two models' false positives — the
legit-traffic assessment is what weighs that cost. See report/input_guard_comparison.py.
"""
import functools
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

from defense.input_guard import flag as _protectai_flag

WOLF = "patronus-studio/wolf-defender-prompt-injection-small"   # LABEL_1 = INJECTION (probed)


@functools.lru_cache(maxsize=1)
def _wolf():
    tok = AutoTokenizer.from_pretrained(WOLF)
    mod = AutoModelForSequenceClassification.from_pretrained(WOLF).eval()
    return tok, mod


def _wolf_flag(prompt: str) -> bool:
    tok, mod = _wolf()
    inputs = tok(prompt, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        logits = mod(**inputs).logits
    return int(logits.argmax()) == 1


def flag(prompt: str) -> bool:
    """True if either classifier labels the prompt INJECTION (hard-label OR)."""
    return _protectai_flag(prompt) or _wolf_flag(prompt)
