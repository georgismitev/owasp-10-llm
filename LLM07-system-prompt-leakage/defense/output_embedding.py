"""Output-only defense #2: flag a response that is semantically close to the system prompt.

Catches paraphrased / obfuscated recitation the literal match (output_literal_match.py) misses.
Embeds the response and the known SYSTEM_PROMPT with all-MiniLM-L6-v2 (mean-pooled over tokens,
L2-normalized) and scores their cosine similarity; flags at a calibrated THRESHOLD. Loads the
local model through transformers — no sentence-transformers dependency. Detection only.
"""
import torch
from transformers import AutoTokenizer, AutoModel
from target.app import SYSTEM_PROMPT

MODEL = "sentence-transformers/all-MiniLM-L6-v2"
THRESHOLD = 0.60          # calibrated over the clean-legitimate vs leaked cosine distributions

_tok = AutoTokenizer.from_pretrained(MODEL)
_model = AutoModel.from_pretrained(MODEL).eval()


def _embed(text: str):
    """Mean-pooled, L2-normalized sentence embedding (the all-MiniLM-L6-v2 recipe)."""
    enc = _tok(text, truncation=True, max_length=256, return_tensors="pt")
    with torch.no_grad():
        tokens = _model(**enc).last_hidden_state           # (1, T, H)
    mask = enc["attention_mask"].unsqueeze(-1)             # (1, T, 1)
    pooled = (tokens * mask).sum(1) / mask.sum(1)          # average over real tokens
    return torch.nn.functional.normalize(pooled, dim=1)    # unit vector → cosine == dot


_REF = _embed(SYSTEM_PROMPT)


def score(response: str) -> float:
    """Cosine similarity (0..1) between the response and the system prompt."""
    return float(_embed(response) @ _REF.T)


def flag(response: str) -> bool:
    """True if the response is at least THRESHOLD cosine-similar to the system prompt."""
    return score(response) >= THRESHOLD
