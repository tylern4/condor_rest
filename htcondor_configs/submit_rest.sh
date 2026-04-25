#!/bin/bash

source /app/.venv/bin/activate

exec gunicorn -w 4 -k uvicorn.workers.UvicornWorker htcondor_rest.app:app --bind 0.0.0.0:8008
