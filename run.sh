#!/usr/bin/env bash
# Sobe a API + interface em http://localhost:8000
set -euo pipefail
cd "$(dirname "$0")"
exec uvicorn entrypoint:app --host 0.0.0.0 --port 8000 --reload
