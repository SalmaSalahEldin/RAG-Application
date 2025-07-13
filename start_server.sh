#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
export PYTHONPATH=src
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 