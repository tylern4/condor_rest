#!/bin/bash

# If variable is set and the file does not exist make a new "Random" password
# if [[ ! -f "/etc/condor/passwords.d/${PASSWORDFILE}" ]]; then
#     uuidgen -r | sed 's/-//g' > /etc/condor/passwords.d/"${PASSWORDFILE}"
#     cp /etc/condor/passwords.d/"${PASSWORDFILE}" /app/"${PASSWORDFILE}"
#     chown submituser:submituser /app/"${PASSWORDFILE}"
#     cat /etc/condor/passwords.d/"${PASSWORDFILE}" 
# fi

# # If variable is set and the file does not exist make a new "Random" password
# if [[ ! -f "/app/${PASSWORDFILE}" ]]; then
#     cp /etc/condor/passwords.d/"${PASSWORDFILE}" /app/"${PASSWORDFILE}"
#     chown submituser:submituser /app/"${PASSWORDFILE}"
#     cat /app/"${PASSWORDFILE}" 
# fi

# chown -R submituser:submituser /app
