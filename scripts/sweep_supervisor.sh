#!/usr/bin/env bash
# Resilient transfer-sweep runner. run.py is resumable (append+flush per row,
# fingerprint dedup), so on any crash we just re-launch and it picks up where
# attack.jsonl left off. setsid-detach this so it survives a dropped connection.
set -u
cd /home/ubuntu/owasp-10-llm
RUN="LLM07-system-prompt-leakage/impl-01-tool-credential-leak/attack/run.py"
MAX=60
i=0
echo "=== sweep supervisor start $(date -u +%FT%TZ) ==="
while (( i < MAX )); do
  i=$((i+1))
  echo "--- attempt $i: uv run python $RUN --all ---"
  if uv run python "$RUN" --all; then
    echo "=== sweep complete (exit 0) at attempt $i $(date -u +%FT%TZ) ==="
    exit 0
  fi
  echo "!!! run.py exited non-zero (attempt $i); retry in 15s $(date -u +%FT%TZ)"
  sleep 15
done
echo "=== gave up after $MAX attempts $(date -u +%FT%TZ) ==="
exit 1
