# Mapping Polarization and Cross-Community Interaction in the CJP-led Jantar Mantar Protests

Computational Social Media Analysis · Group 9 (Sejal Gupta, Krishna Mundra, Adamya Aggarwal, Anmol Chaturvedi)

Study window: **1 June – 31 July 2026** (UTC). Platforms: **X** (primary, captured with Zeeschuimer + Schuifmaat) and **Reddit** (secondary, collected from the PullPush and Arctic Shift public archives).

## Pipeline (one notebook per stage)

| # | Notebook | What it does | Main outputs |
|---|---|---|---|
| 01 | `01_Data_Collection.ipynb` | X capture method and keyword groups A–D; Reddit collector (keyword submissions, full comment threads, keyword comments) | `data/reddit_raw/*.jsonl`, `outputs/tables/01_*` |
| 02 | `02_Data_Cleaning_Preprocessing.ipynb` | window + relevance filters, de-duplication, one shared schema for both platforms, author tables | `data/x_processed/x_posts_unified.csv`, `data/reddit_processed/reddit_items_unified.csv` |
| 03 | `03_Exploratory_Data_Analysis.ipynb` | volume over time with protest events, keyword groups, language, engagement, hashtags, subreddits, shared domains, top accounts | `03_*` tables and figures |
| 04 | `04_Interaction_Networks.ipynb` | directed weighted user networks (reply / quote / mention on X, reply / u-mention on Reddit), metrics, centralities, Gephi export; replicates the midsem network | `04_*`, `outputs/gexf/*_interaction_network.gexf` |
| 05 | `05_Community_Detection.ipynb` | Louvain on the largest component with seed and resolution stability checks, community summaries, meta-network | `05_*`, `*_largest_wcc_communities.gexf` |
| 06 | `06_Community_Classification.ipynb` | stance classifier trained on 636 hand-labelled items (PRO / ANTI / NEUTRAL + hostile), user and community stance, themes, distinctive terms, factors, representative posts | `06_*` |
| 07 | `07_Information_Diffusion.ipynb` | adoption curves, cascades, spread of domains and hashtags across communities, X→Reddit link flow, weekly cross-community interaction | `07_*` |
| 08 | `08_Polarization_CrossCommunity.ipynb` | modularity, E–I index, stance assortativity, Random-Walk Controversy, configuration-model null, stance mixing matrices, hostility of cross-stance contact, bridge users | `08_*` |
| 09 | `09_Interaction_vs_Polarization.ipynb` | final community tables, X-vs-Reddit comparison table, criterion-by-criterion verdict | `09_*` (CSV + XLSX) |

`notebooks/csma_lib.py` holds the shared paths, lexicons, event list and network helpers.

## Folder layout

```
data/x_raw/Group A|B|C|D/     Zeeschuimer CSV exports (Group D is empty: the student-union searches returned too few X posts)
data/x_processed/             team master dataset + unified X table + author table
data/reddit_raw/              archive JSONL files + collector state/log
data/reddit_processed/        unified Reddit table + author table + excluded submissions
data/annotations/             manual stance annotations and guidelines (README.md)
outputs/tables|figures|gexf/  every table (CSV), figure (PNG) and Gephi file, prefixed by notebook number
report/                       final written report
_build/                       notebook sources (specs), build script, venv, collectors, logs
```

## How to run

```bash
cd _build && /opt/homebrew/opt/python@3.11/bin/python3.11 -m venv --system-site-packages venv
./venv/bin/pip install openpyxl python-docx langdetect wordcloud emoji nbformat nbclient ipykernel
./venv/bin/python -m ipykernel install --user --name csma --display-name "Python (csma)"
cd nb && ../venv/bin/python build.py --run          # rebuilds and executes notebooks 01-09 in order
```

Requirements: pandas, numpy, scipy, scikit-learn, networkx ≥ 3.0, matplotlib, seaborn (all in the Homebrew Python 3.11 site-packages). Notebooks also run cell by cell in Jupyter with the `csma` kernel; notebook 01 uses the cached raw files unless `RUN_COLLECTION = True`.

## Group D (student unions) and more X data

Group D was searched on X with several keyword sets but returned too few posts to form a dataset; it is covered on Reddit only. To add more X data later: in Firefox with Zeeschuimer enabled, run X advanced searches for 1 Jun – 31 Jul 2026, e.g. `AISA "Jantar Mantar"`, `SFI CJP`, `NSUI NEET protest`, `ABVP CJP`, `"Cockroach Students" union`, `AISF Jantar Mantar`, `KYS protest Delhi`; let Schuifmaat scroll to the end.
2. Export each search as CSV and drop the files into `data/x_raw/Group D/`.
3. Extend `data/x_processed/master_protest_dataset.csv` with the team's `Preprocessing.ipynb` (same rules), then re-run notebooks 02–09.

## Re-running the Reddit collection

The collectors in `_build/collect_reddit.py` (PullPush keyword search) and `_build/collect_reddit_threads_as.py` (Arctic Shift comment threads) are resumable and respect the archives' rate limits (about 10 requests per minute); a full run takes several hours. For a faster or more complete re-collection, the same stages can be run against Reddit's official API with a registered application (PRAW), which returns full comment trees in one call per thread.
