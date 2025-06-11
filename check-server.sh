#!/usr/bin/env bash
set -euo pipefail

# Create virtual environment if missing
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
# Activate venv
source venv/bin/activate

# Install server dependencies only
pip install -q -r requirements-server.txt

python -c "import fastapi; print('fastapi', fastapi.__version__)"

# Start server in background
uvicorn server:app --app-dir app --port 8000 --reload &
PID=$!

# wait for server
for i in {1..10}; do
    sleep 1
    status=$(curl -s http://127.0.0.1:8000/health || true)
    if [ "$status" = '{"status":"ok"}' ]; then
        echo "Health check OK"
        kill $PID
        wait $PID 2>/dev/null || true
        deactivate
        exit 0
    fi
    echo "Waiting for server... ($i)"
done

echo "Health check failed"
kill $PID
wait $PID 2>/dev/null || true
deactivate
exit 1
