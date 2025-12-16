#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

stop_if_pidfile() {
  local f="$1"
  if [ -f "$f" ]; then
    pid=$(cat "$f")
    if ps -p "$pid" > /dev/null 2>&1; then
      echo "Stopping PID $pid..."
      kill "$pid" || true
      sleep 1
      if ps -p "$pid" > /dev/null 2>&1; then
        echo "PID $pid still running, killing..."
        kill -9 "$pid" || true
      fi
    fi
    rm -f "$f"
  fi
}

stop_if_pidfile "$ROOT/run/frontend.pid"
stop_if_pidfile "$ROOT/run/backend.pid"

echo "Stopped services (logs remain in $ROOT/logs)"