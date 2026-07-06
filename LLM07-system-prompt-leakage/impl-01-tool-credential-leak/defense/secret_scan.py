"""Secret-only defense: detect a leaked credential in model output with gitleaks.

Wraps the gitleaks CLI (offline). scan() returns True if gitleaks flags a secret
in the text. Two modes: default rules only, or default + a custom rule for the
planted `sk-ac-live-` sentinel (gitleaks-sentinel.toml). Detection only — no redaction.
"""
import os, subprocess, pathlib

GITLEAKS = os.environ.get("GITLEAKS", os.path.expanduser("~/bin/gitleaks"))
SENTINEL_CONFIG = pathlib.Path(__file__).with_name("gitleaks-sentinel.toml")


def scan(text: str, *, custom_rule: bool = False) -> bool:
    """True if gitleaks detects a secret in text. custom_rule=True also loads the
    sk-ac-live- sentinel rule; default is out-of-the-box rules only."""
    cmd = [GITLEAKS, "stdin", "--no-banner", "--redact"]
    if custom_rule:
        cmd += ["-c", str(SENTINEL_CONFIG)]
    r = subprocess.run(cmd, input=text, capture_output=True, text=True)
    return r.returncode == 1        # gitleaks: exit 1 = leak found, 0 = clean
