#!/bin/bash

export CONDOR_CONFIG=/data/htcondorlogs/95-NERSC.conf

mkdir -p /logs/condor/log
mkdir -p /logs/condor/spool

mkdir -p /scratch/log
mkdir -p /scratch/spool

exec condor_master -f &

# shellcheck source=/dev/null
source /app/.venv/bin/activate

exec gunicorn --log-level debug -w 1 --threads 16 -k uvicorn.workers.UvicornWorker htcondor_rest.app:app --bind 0.0.0.0:8008 &

wait

