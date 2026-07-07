"""Two-model input defense: flag a prompt if EITHER prompt-injection guard fires.

Composes two single-model guard defenses — protectai-v2 (protectai_guard) and wolf-defender
(wolf_guard) — with a hard-label OR. They miss largely disjoint prompts, so the union
catches more (48/49 on the attack corpus vs 44/49 each). Detection only, model-agnostic
(scores the prompt), no target-model call.

Hard-label OR: max recall, but it also unions the two guards' false positives — the
legitimate-traffic assessment weighs that cost. See report/two_model_defense.py.
"""
from defense.protectai_guard import flag as _protectai_flag
from defense.wolf_guard import flag as _wolf_flag


def flag(prompt: str) -> bool:
    """True if either single-model guard labels the prompt INJECTION (hard-label OR)."""
    return _protectai_flag(prompt) or _wolf_flag(prompt)
