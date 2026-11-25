#!/bin/zsh
# One-command refresh: rebuild and execute notebooks 01-09 on the data currently on disk, regenerate the report,
# export HTML copies, zip the deliverables and mirror the project to the SSD. Takes ~25 minutes.
#   /Users/CSMA/Project/_build/refresh_all.sh            # full refresh
#   /Users/CSMA/Project/_build/refresh_all.sh 06 07 08 09 # only some notebooks (in order)
set -e
P=/Users/CSMA/Project
cd "$P/_build/nb"
LOG="$P/_build/logs/refresh_$(date +%Y%m%d_%H%M).log"
echo "log: $LOG"
caffeinate -i ../venv/bin/python -I build.py "$@" --run 2>&1 | tee "$LOG"
cd "$P"
./_build/venv/bin/python -I _build/make_report.py 2>&1 | tee -a "$LOG"
./_build/package.sh 2>&1 | tee -a "$LOG"
echo "refresh complete"
