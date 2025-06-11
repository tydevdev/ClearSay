#!/usr/bin/env bash
set -euo pipefail

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

pip install --no-index --find-links=./wheels -r requirements-ui.txt
