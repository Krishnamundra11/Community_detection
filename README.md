# CSMA Project — CJP / Jantar Mantar Protests (X & Reddit, Jun–Jul 2026)

This repository is organized sequentially according to the project workflow.

## Folder Structure

```text
CSMA/
├── 00_Reference_Papers/          # 4 core research papers used for methodology (RWC, cross-partisan interaction, stance clustering)
├── 01_MidSem_Pipeline/           # Phase 1: X-only dataset preprocessing, network analysis, & Louvain communities
│   ├── 01_Raw_Data/              # Extended X exports (Group A: CJP/Protest, Group B: NEET/Paper Leak, Group C: Govt/Police)
│   ├── 02_Preprocessing/         # Preprocessing.ipynb + processed/ (master_protest_dataset.csv, logs, excluded posts)
│   ├── 03_Network_Analysis/      # Directed weighted interaction network (466 nodes, 600 edges), centrality, Figure 1
│   ├── 04_Community_Detection/   # Louvain community detection (21 communities, modularity 0.6237), Figures 2 & 3
│   └── 05_Community_Interaction/ # Raw & aggregated interaction edge lists + group-level interaction summary
├── 02_EndSem_Full_Pipeline/      # Phase 2: Complete multi-platform (X + Reddit) runnable pipeline
│   ├── data/                     # x_raw, x_processed, reddit_raw, reddit_processed, manual annotations
│   ├── notebooks/                # 01_Data_Collection.ipynb -> 09_Interaction_vs_Polarization.ipynb + csma_lib.py
│   ├── outputs/                  # Generated tables/, figures/, and Gephi (.gexf) graphs
│   ├── report/                   # KEY_FINDINGS.md & CSMA_Final_Report_Group9.docx
│   └── scripts/                  # Reddit collectors, notebook builder, report generator
└── 99_Archive_Unused/            # Superseded/backup files preserved without deletion
    ├── Temporary Datasets/       # Initial 5 unmerged X CSVs (superseded by 01_MidSem_Pipeline/01_Raw_Data)
    ├── filtered_datasets/        # Initial 5 date-filtered CSVs (superseded by 01_MidSem_Pipeline/02_Preprocessing/processed)
    ├── CSMA_Project.zip          # Original project archive (contents extracted to 02_EndSem_Full_Pipeline)
    └── macOS_DS_Store/           # macOS .DS_Store metadata files
```

## End-Sem Pipeline Flow (`02_EndSem_Full_Pipeline/notebooks/`)

1. `01_Data_Collection.ipynb` — X (Zeeschuimer) & Reddit (PullPush + Arctic Shift) data collection
2. `02_Data_Cleaning_Preprocessing.ipynb` — Unified schema, relevance filtering, deduplication
3. `03_Exploratory_Data_Analysis.ipynb` — Daily volume, events, hashtags, subreddits, domains
4. `04_Interaction_Networks.ipynb` — Directed weighted interaction graphs + Gephi export
5. `05_Community_Detection.ipynb` — Louvain communities + seed-stability (NMI) checks
6. `06_Community_Classification.ipynb` — Supervised stance classifier (PRO/ANTI/NEUTRAL) + themes
7. `07_Information_Diffusion.ipynb` — Cascades, domain spread, X → Reddit link flow
8. `08_Polarization_CrossCommunity.ipynb` — Modularity, E–I index, RWC, null models, bridge users
9. `09_Interaction_vs_Polarization.ipynb` — Final X vs Reddit comparison & verdict
