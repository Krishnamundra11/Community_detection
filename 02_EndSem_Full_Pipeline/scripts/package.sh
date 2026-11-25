#!/bin/zsh
# Packages the deliverables (notebooks, outputs, processed data, annotations, report, README) into one zip
# and mirrors the whole project to the SSD. Raw archive files stay in data/reddit_raw (and in the SSD mirror).
set -e
setopt NULL_GLOB
export JUPYTER_PATH=/opt/homebrew/share/jupyter
P=/Users/CSMA/Project
cd "$P"
STAMP=$(date +%Y%m%d_%H%M)
# static HTML copies of the executed notebooks (readable without Jupyter)
mkdir -p outputs/notebooks_html
for nb in notebooks/0*.ipynb; do /opt/homebrew/bin/jupyter nbconvert --to html --output-dir outputs/notebooks_html "$nb" >/dev/null 2>&1 || echo "nbconvert failed for $nb"; done
ZIP="$P/CSMA_Group9_Deliverables_$STAMP.zip"
rm -f "$P"/CSMA_Group9_Deliverables_*.zip
zip -q -r "$ZIP" README.md report notebooks outputs data/annotations data/x_processed/x_posts_unified.csv data/x_processed/x_authors.csv \
    data/x_processed/master_protest_dataset.csv data/reddit_processed data/x_raw _build/nb _build/build.py _build/make_report.py \
    _build/collect_reddit.py _build/collect_reddit_threads_as.py -x '*.DS_Store' '*/__pycache__/*'
echo "zip: $ZIP ($(du -h "$ZIP" | cut -f1))"
if [ -d "/Volumes/HP P900" ]; then
  mkdir -p "/Volumes/HP P900/CSMA_backup"
  rsync -a --exclude '_build/venv' --exclude '.DS_Store' "$P/" "/Volumes/HP P900/CSMA_backup/Project/"
  cp "$ZIP" "/Volumes/HP P900/CSMA_backup/"
  echo "mirrored to /Volumes/HP P900/CSMA_backup"
else
  echo "SSD not mounted: no mirror"
fi
