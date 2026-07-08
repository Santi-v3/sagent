#!/bin/bash
# Sagent startup script (Linux/macOS)
set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Sagent Development Server ==="
echo ""

# Start backend
echo "Starting backend..."
export PYTHONPATH="$ROOT_DIR/apps/agent-api/src:$ROOT_DIR/packages/tools/src:$ROOT_DIR/packages/agent-core/src:$ROOT_DIR/packages/memory/src"
uv run uvicorn sagent_agent_api.main:app --app-dir src --host 127.0.0.1 --port 8765 --reload &
BACKEND_PID=$!

sleep 3

# Start frontend
echo "Starting frontend..."
pnpm dev &
FRONTEND_PID=$!

echo ""
echo "Backend:  http://127.0.0.1:8765"
echo "Frontend: http://127.0.0.1:3000"
echo ""
echo "Press Ctrl+C to stop"

cleanup() {
    echo ""
    echo "Shutting down..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}
trap cleanup SIGINT SIGTERM

wait
