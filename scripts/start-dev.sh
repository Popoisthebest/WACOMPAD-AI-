#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$ROOT/run" "$ROOT/logs"

# parse options
OPEN_BROWSER=0
FOLLOW_LOGS=0
while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --open)
      OPEN_BROWSER=1
      shift
      ;;
    --follow-logs)
      FOLLOW_LOGS=1
      shift
      ;;
    *)
      shift
      ;;
  esac
done


echo "Starting backend..."
if [ -x "$ROOT/web_server/venv/bin/python" ]; then
  # Run from web_server dir so uvicorn can import module 'main'
  (cd "$ROOT/web_server" && "$ROOT/web_server/venv/bin/python" -m uvicorn main:app --host 127.0.0.1 --port 8000 > "$ROOT/logs/backend.log" 2>&1 & echo $! > "$ROOT/run/backend.pid")
else
  (cd "$ROOT/web_server" && python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 > "$ROOT/logs/backend.log" 2>&1 & echo $! > "$ROOT/run/backend.pid")
fi

sleep 1

echo "Starting frontend (this will run in background)..."
cd "$ROOT/frontend"
npm start > "$ROOT/logs/frontend.log" 2>&1 &
echo $! > "$ROOT/run/frontend.pid"
cd "$ROOT"

# Wait a short time for services to bind
sleep 1

if [ "$OPEN_BROWSER" -eq 1 ]; then
  # wait for port 3000 to be listening
  timeout=10
  i=0
  while [ $i -lt $timeout ]; do
    if lsof -iTCP:3000 -sTCP:LISTEN -P -n >/dev/null 2>&1; then
      open "http://localhost:3000" || true
      break
    fi
    i=$((i+1))
    sleep 1
  done
fi

echo "Started. Backend PID: $(cat "$ROOT/run/backend.pid"), Frontend PID: $(cat "$ROOT/run/frontend.pid")"
echo "Logs: $ROOT/logs/ (backend: backend.log, frontend: frontend.log)"

if [ "$FOLLOW_LOGS" -eq 1 ]; then
  echo "Following logs (CTRL+C to stop)..."
  tail -n +1 -f "$ROOT/logs/backend.log" "$ROOT/logs/frontend.log"
fi