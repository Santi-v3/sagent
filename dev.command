#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "=== Backend starten ==="
cd apps/agent-api
PYTHONPATH=src:../../packages/tools/src:../../packages/agent-core/src:../../packages/memory/src \
  uv run uvicorn sagent_agent_api.main:app --app-dir src --reload --host 127.0.0.1 --port 8765 &
BACKEND_PID=$!
cd ../..

sleep 2

echo "=== Frontend starten ==="
pnpm --filter @sagent/web dev &
FRONTEND_PID=$!

echo ""
echo "=== Browser öffnen: http://localhost:3000 ==="
echo "=== Drücke Ctrl+C zum Beenden ==="
echo ""

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM
wait
