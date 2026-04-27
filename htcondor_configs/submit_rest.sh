#!/bin/bash

source /app/.venv/bin/activate
# export LOGURU_LEVEL="DEBUG"
gunicorn --log-level debug -w 1 --threads 16 -k uvicorn.workers.UvicornWorker htcondor_rest.app:app --bind 0.0.0.0:8008 &

wait
