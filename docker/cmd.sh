#!/usr/bin/env bash

/entrypoint.sh &
sleep 10

if [ -f /home/app/api/start.sh ];then
    bash /home/app/api/start.sh &
fi

wait
