#!/bin/sh
TRAFFIC='/home/pi/traffic.py'
LOGFILE=/var/log/traffic.log
 
# Fork off node into the background and log to a file
echo "Forking at `date`" >> ${LOGFILE}
python ${TRAFFIC} $@ >>${LOGFILE} 2>&1 </dev/null &
 
# Capture the child process PID
CHILD="$!"
 
# Kill the child process when start-stop-daemon sends us a kill signal
trap "kill $CHILD" exit INT TERM
 
# Wait for child process to exit
wait
