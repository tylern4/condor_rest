#!/bin/bash



if [[ -n "$HTCONDOR_WORKER" ]]; then
    case "${HTCONDOR_WORKER,,}" in
        0|false|False)
            echo "DAEMON_LIST = MASTER COLLECTOR NEGOTIATOR SCHEDD" >> /etc/condor/condor_config.local
            ;;
    esac
fi

if [[ -n "$HTCONDOR_PORT" ]]; then
    echo "COLLECTOR_PORT = ${HTCONDOR_PORT}" >> /etc/condor/condor_config.local
fi