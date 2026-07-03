"""Tiny on-disk response cache. Platform only."""
import hashlib, pathlib

DIR = pathlib.Path(__file__).resolve().parent.parent / ".labkit_cache"


def _f(key):
    return DIR / (hashlib.sha256(key.encode()).hexdigest() + ".txt")


def get(key):
    f = _f(key)
    return f.read_text() if f.exists() else None


def set(key, output):
    DIR.mkdir(exist_ok=True)
    _f(key).write_text(output)
