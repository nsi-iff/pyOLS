#!/bin/sh
cd /Users/wolever/pyOLS

if [[ -e .roundup_pid ]]
then
    echo -n "Already running... Killing old instance first... "
    kill `cat .roundup_pid`
    sleep 1
    echo "Ok."
fi

roundup-server -p1111 -l /tmp/roundup_http_log pyOLS=roundup &
kidder=`jobs -p`
echo $kidder > .roundup_pid
echo "Starting child with pid $kidder at http://localhost:1111..."
sleep 3
open http://localhost:1111/
