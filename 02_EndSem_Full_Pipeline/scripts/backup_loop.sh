#!/bin/zsh
# Mirrors the project (minus venv) to the external SSD every 10 minutes while it is mounted.
while true; do
  if [ -d "/Volumes/HP P900" ]; then
    mkdir -p "/Volumes/HP P900/CSMA_backup" 2>/dev/null
    rsync -a --exclude '_build/venv' --exclude '.DS_Store' /Users/CSMA/Project/ "/Volumes/HP P900/CSMA_backup/Project/" 2>/dev/null && date "+%F %T backup ok" >> /Users/CSMA/Project/_build/logs/backup.log
  else
    date "+%F %T SSD not mounted" >> /Users/CSMA/Project/_build/logs/backup.log
  fi
  sleep 600
done
