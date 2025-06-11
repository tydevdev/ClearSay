#!/usr/bin/env bash
set -euo pipefail

# Resolve repository root even if script is moved inside the repo
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)"
cd "$ROOT_DIR"

# Activate Python virtual environment
source "$ROOT_DIR/venv/bin/activate"

# Start FastAPI server in background
pushd app >/dev/null
uvicorn server:app &
SERVER_PID=$!
popd >/dev/null

cleanup() {
    echo "Shutting down server..."
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
}
trap cleanup EXIT

# Launch Electron app and wait for it to exit
pushd electron >/dev/null
npm run start
popd >/dev/null
