#!/usr/bin/env bash
set -euo pipefail

###########################################################################
# Relaunch in the background when invoked without --foreground.
# This allows the script to be double-clicked or run from Automator without
# leaving a visible terminal window. The re-launched instance runs detached
# from the current shell, while this initial invocation exits immediately.
###########################################################################
if [[ "${1-}" != "--foreground" ]]; then
    SCRIPT_PATH="$(cd "$(dirname "$0")" && pwd)/$(basename "$0")"
    nohup "$SCRIPT_PATH" --foreground >/dev/null 2>&1 &
    disown
    exit 0
fi
shift || true

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
