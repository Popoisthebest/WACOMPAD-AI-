#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "Sending test stroke to http://127.0.0.1:8000/analyze_strokes"
RESP=$(curl -s -X POST "http://127.0.0.1:8000/analyze_strokes" -H "Content-Type: application/json" -d '{"records":[{"timestamp_ms": 1, "x":10, "y":10, "pressure":0.5, "button":1},{"timestamp_ms":2,"x":15,"y":12,"pressure":0.4,"button":1},{"timestamp_ms":3,"x":20,"y":14,"pressure":0.0,"button":0}]}' || true)

# pretty print using available python interpreter
if command -v python3 >/dev/null 2>&1; then
  echo "$RESP" | python3 -m json.tool || echo "$RESP"
elif [ -x "$ROOT/web_server/venv/bin/python" ]; then
  echo "$RESP" | "$ROOT/web_server/venv/bin/python" -m json.tool || echo "$RESP"
else
  echo "$RESP"
fi
