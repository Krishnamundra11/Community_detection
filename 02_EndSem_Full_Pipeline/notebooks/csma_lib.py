"""Shared helpers for the CSMA CJP / Jantar Mantar notebooks.

Every notebook does `from csma_lib import *` and then calls the small functions below, so the
notebooks stay short and all paths, colours and definitions live in one place.
"""
from __future__ import annotations

import json
import os
import re
import warnings
from collections import Counter
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ------------------------------------------------------------------ paths
ROOT = Path(os.environ.get("CSMA_ROOT", Path(__file__).resolve().parent.parent))
DATA = ROOT / "data"
X_RAW, X_PROC = DATA / "x_raw", DATA / "x_processed"
R_RAW, R_PROC = DATA / "reddit_raw", DATA / "reddit_processed"
OUT = ROOT / "outputs"
TABLES, FIGURES, GEXF = OUT / "tables", OUT / "figures", OUT / "gexf"
for p in (X_PROC, R_PROC, TABLES, FIGURES, GEXF):
    p.mkdir(parents=True, exist_ok=True)

WINDOW_START = pd.Timestamp("2026-06-01 00:00:00")
WINDOW_END = pd.Timestamp("2026-07-31 23:59:59")

# Dated events used to annotate time-series plots (from the Wikipedia article on the protests and
# the Cockroach Janta Party, checked against press coverage).
EVENTS = [
    ("2026-06-06", "First CJP protest at Jantar Mantar"),
    ("2026-06-11", "Exam manifesto; nationwide campaign"),
    ("2026-06-20", "Second protest; indefinite sit-in begins"),
    ("2026-06-28", "Wangchuk starts hunger strike"),
    ("2026-07-07", "HC orders CJP X account unblocked"),
    ("2026-07-16", "Kejriwal joins protest"),
    ("2026-07-18", "Wangchuk removed; Dipke detained, fasts"),
    ("2026-07-20", "Parliament march; lathi charge, tear gas"),
    ("2026-07-23", "Fast-track courts; Wangchuk ends fast"),
    ("2026-07-25", "Pradhan resigns; CJP calls off protest"),
    ("2026-07-31", "Modi 'forgive the students' remarks"),
]

# ------------------------------------------------------------------ plotting
PALETTE = {
    "x": "#1f5fbf", "reddit": "#e2662b", "neutral": "#8a8f98",
    "PRO": "#2a9d8f", "ANTI": "#c8553d", "NEUTRAL": "#8a8f98",
    "A": "#4c72b0", "B": "#55a868", "C": "#c44e52", "D": "#8172b2",
}
COMM_COLORS = plt.cm.tab20.colors + plt.cm.tab20b.colors + plt.cm.tab20c.colors


def setup_plots():
    plt.rcParams.update({
        "figure.dpi": 110, "savefig.dpi": 200, "figure.figsize": (9, 4.5),
        "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
        "grid.alpha": 0.25, "axes.titlesize": 12, "axes.labelsize": 10, "legend.fontsize": 9,
        "font.family": "DejaVu Sans",
    })


def savefig(name: str):
    path = FIGURES / f"{name}.png"
    plt.tight_layout()
    plt.savefig(path, bbox_inches="tight")
    print(f"figure saved: {path.relative_to(ROOT)}")


def save_table(df: pd.DataFrame, name: str, index=False):
    path = TABLES / f"{name}.csv"
    df.to_csv(path, index=index)
    print(f"table saved: {path.relative_to(ROOT)}  ({len(df)} rows)")
    return df


def annotate_events(ax, events=EVENTS, every=1, ymax=None):
    ymax = ymax or ax.get_ylim()[1]
    for i, (d, label) in enumerate(events):
        if i % every:
            continue
        ax.axvline(pd.Timestamp(d), color="#444", alpha=0.25, lw=0.8)
        ax.text(pd.Timestamp(d), ymax * 0.98, label, rotation=90, va="top", ha="right", fontsize=6.5, color="#333")


# ------------------------------------------------------------------ text
URL_RE = re.compile(r"https?://\S+")
HANDLE_RE = re.compile(r"@\w+")
WS_RE = re.compile(r"\s+")
DEVANAGARI_RE = re.compile(r"[ऀ-ॿ]")


def clean_text(s) -> str:
    s = "" if s is None or (isinstance(s, float) and np.isnan(s)) else str(s)
    s = URL_RE.sub(" ", s).replace("&amp;", "&").replace("&gt;", ">").replace("&lt;", "<")
    return WS_RE.sub(" ", s).strip()


def script_of(text: str) -> str:
    """Rough language signal: Devanagari (Hindi), Latin (English or romanised Hindi), or mixed."""
    dev = len(DEVANAGARI_RE.findall(text))
    lat = len(re.findall(r"[A-Za-z]", text))
    if dev and lat:
        return "mixed" if min(dev, lat) / max(dev + lat, 1) > 0.15 else ("devanagari" if dev > lat else "latin")
    return "devanagari" if dev else ("latin" if lat else "other")


# Theme lexicon: each theme = list of regexes (English, Hindi, romanised Hindi).  A post can carry
# several themes.  Used for the "Themes" part of community classification.
THEMES = {
    "exam_integrity": r"\bneet\b|paper[\s\-]*leak|\bnta\b|cbse|cuet|\bssc\b|re-?exam|irregularit|नीट|पेपर\s*लीक|परीक्षा|exam",
    "minister_accountability": r"pradhan|education\s*minister|resign|istifa|इस्तीफ़?ा|शिक्षा\s*मंत्री|प्रधान",
    "police_repression": r"police|lathi|tear\s*gas|pellet|detain|arrest|barricad|crackdown|\bfir\b|पुलिस|लाठी|हिरासत|गिरफ्तार|brutal",
    "wangchuk_fast": r"wangchuk|hunger\s*strike|anshan|fast(?:ing)?\b|अनशन|वांगचुक",
    "opposition_politics": r"rahul\s*gandhi|congress|kejriwal|\baap\b|akhilesh|owaisi|opposition|विपक्ष|राहुल|केजरीवाल|कांग्रेस",
    "government_bjp": r"\bmodi\b|\bbjp\b|nadda|amit\s*shah|\brss\b|hindutva|godi|मोदी|भाजपा|सरकार|government|govt",
    "conspiracy_funding": r"foreign\s*fund|b-?team|soros|pakistan|\bisi\b|toolkit|tool\s*kit|urban\s*naxal|anti[\s\-]*india|paid\s*protest|funded|controlled\s*opposition|terrorist|आतंकवादी",
    "mobilisation": r"join|reach|aa\s*rahe|come|gather|march|chalo|venue|day\s*\d|tonight|overnight|sit[\s\-]*in|volunteer|जुड़|चलो|पहुंच",
    "media_coverage": r"media|journalist|anchor|channel|coverage|reporter|godi|मीडिया|पत्रकार",
    "students_youth": r"student|aspirant|youth|gen\s*z|young|छात्र|युवा|विद्यार्थी",
    "satire_cji_remark": r"parasite|\bcji\b|chief\s*justice|surya\s*kant|satir|\bmeme\b|cockroach\s*(?:remark|comment|jibe|statement)|🪳",
    "student_unions": r"\baisa\b|\bsfi\b|\bnsui\b|\babvp\b|\baisf\b|\bkys\b|student\s*union|students?'?\s*federation|jnu|neha\s*bora|aishe",
}
THEME_RE = {k: re.compile(v, re.I) for k, v in THEMES.items()}


def themes_of(text: str) -> list[str]:
    return [k for k, rx in THEME_RE.items() if rx.search(text or "")]


# Relevance signals (same spirit as the X preprocessing step); used for Reddit filtering.
CORE_RE = re.compile(
    r"cockroach|कॉ.?क्रोच|कोकरोच|\bcjp\b|dipke|जंतर\s*मंतर|jantar[\s\-]*mantar|dharmendra\s*pradhan|"
    r"wangchuk|chalo\s*sansad|pradhan\s*go\s*back|cockroachjantaparty",
    re.I,
)
CONTEXT_RE = re.compile(
    r"\bneet\b|paper[\s\-]*leak|education\s*minister|pradhan|protest|hunger\s*strike|lathi|tear\s*gas|"
    r"delhi\s*police|parliament|student|aspirant|aisa|\bsfi\b|nsui|abvp|नीट|पेपर\s*लीक|प्रदर्शन|आंदोलन",
    re.I,
)


# ------------------------------------------------------------------ data loaders
def load_x_master() -> pd.DataFrame:
    df = pd.read_csv(X_PROC / "master_protest_dataset.csv", dtype=str, keep_default_na=False, encoding="utf-8-sig")
    df.columns = [c.lstrip("﻿") for c in df.columns]
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    for c in ["retweet_count", "reply_count", "like_count", "quote_count", "impression_count", "author_followers", "author_following"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)
    for c in ["is_reply", "is_quote_tweet", "is_retweet", "verified"]:
        df[c] = df[c].astype(str).str.lower().isin(["true", "yes", "1"])
    df["author"] = df["author"].str.strip().str.lstrip("@").str.lower()
    df["text"] = df["text_clean"].map(clean_text)
    df["group_primary"] = df["groups"].str[0]
    return df


def load_x_unified() -> pd.DataFrame:
    df = pd.read_csv(X_PROC / "x_posts_unified.csv", dtype={"post_id": str, "parent_id": str, "thread_id": str}, keep_default_na=False)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    return df


def load_reddit_unified() -> pd.DataFrame:
    df = pd.read_csv(R_PROC / "reddit_items_unified.csv", dtype={"post_id": str, "parent_id": str, "thread_id": str}, keep_default_na=False)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    return df


def load_edges(platform: str) -> pd.DataFrame:
    df = pd.read_csv(TABLES / f"04_{platform}_edges_raw.csv", dtype=str, keep_default_na=False)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    return df


def load_graph(platform: str) -> nx.DiGraph:
    return nx.read_gexf(GEXF / f"{platform}_interaction_network.gexf")


def load_membership(platform: str) -> pd.DataFrame:
    return pd.read_csv(TABLES / f"05_{platform}_community_membership.csv", dtype={"node": str})


def load_stance(platform: str) -> pd.DataFrame:
    return pd.read_csv(TABLES / f"06_{platform}_post_stance.csv", dtype={"post_id": str}, keep_default_na=False)


# ------------------------------------------------------------------ network helpers
def build_digraph(edges: pd.DataFrame) -> nx.DiGraph:
    """Weighted directed graph from a raw edge list (source, target, edge_type, ...)."""
    agg = edges.groupby(["source", "target"]).agg(weight=("edge_type", "size"),
                                                   types=("edge_type", lambda s: "|".join(sorted(set(s))))).reset_index()
    G = nx.DiGraph()
    for r in agg.itertuples(index=False):
        G.add_edge(r.source, r.target, weight=int(r.weight), types=r.types)
    return G


def largest_wcc(G: nx.DiGraph) -> nx.DiGraph:
    comp = max(nx.weakly_connected_components(G), key=len)
    return G.subgraph(comp).copy()


def network_summary(G: nx.DiGraph, name: str) -> dict:
    wcc = list(nx.weakly_connected_components(G))
    big = max(wcc, key=len)
    und = G.to_undirected()
    return {
        "network": name, "nodes": G.number_of_nodes(), "edges": G.number_of_edges(),
        "total_weight": int(sum(d["weight"] for _, _, d in G.edges(data=True))),
        "density": round(nx.density(G), 6), "reciprocity": round(nx.reciprocity(G), 4),
        "weakly_connected_components": len(wcc), "largest_wcc_nodes": len(big),
        "largest_wcc_share": round(len(big) / G.number_of_nodes(), 4),
        "avg_clustering": round(nx.average_clustering(und), 4),
        "mean_in_degree": round(np.mean([d for _, d in G.in_degree()]), 3),
    }


def louvain_stable(G_und: nx.Graph, seeds=range(20), resolution=1.0):
    """Run Louvain with several seeds; return the best-modularity partition plus the per-seed modularity values
    and the mean pairwise NMI (how stable the partition is)."""
    from sklearn.metrics import normalized_mutual_info_score as nmi
    runs = []
    for s in seeds:
        parts = nx.community.louvain_communities(G_und, weight="weight", seed=s, resolution=resolution)
        q = nx.community.modularity(G_und, parts, weight="weight")
        runs.append((q, s, parts))
    nodes = list(G_und.nodes())
    labels = []
    for q, s, parts in runs:
        m = {n: i for i, c in enumerate(parts) for n in c}
        labels.append([m[n] for n in nodes])
    nmis = [nmi(labels[i], labels[j]) for i in range(len(runs)) for j in range(i + 1, len(runs))]
    best = max(runs, key=lambda r: r[0])
    return best[2], {"modularity_best": best[0], "seed_best": best[1],
                     "modularity_mean": float(np.mean([r[0] for r in runs])), "modularity_sd": float(np.std([r[0] for r in runs])),
                     "mean_pairwise_nmi": float(np.mean(nmis)) if nmis else 1.0, "n_runs": len(runs)}


def ei_index(G: nx.Graph, membership: dict, weight="weight") -> float:
    """Krackhardt E-I index: (external - internal) / total edge weight; -1 = fully segregated, +1 = all external."""
    E = I = 0.0
    for u, v, d in G.edges(data=True):
        w = d.get(weight, 1)
        if membership.get(u) == membership.get(v):
            I += w
        else:
            E += w
    return (E - I) / (E + I) if (E + I) else float("nan")


def participation_coefficient(G: nx.Graph, membership: dict, weight="weight") -> dict:
    """Guimerà-Amaral participation coefficient on the undirected weighted graph: 0 = all links inside own
    community, close to 1 = links spread evenly over communities."""
    pc = {}
    for n in G.nodes():
        k = 0.0
        per = Counter()
        for nb in G.neighbors(n):
            w = G[n][nb].get(weight, 1)
            k += w
            per[membership.get(nb)] += w
        pc[n] = 1 - sum((x / k) ** 2 for x in per.values()) if k else 0.0
    return pc


def random_walk_controversy(G_und: nx.Graph, side_a: set, side_b: set, k=10, n_walks=2000, seed=0, max_len=50):
    """Garimella et al. (2018) RWC between two sides: start random walks on each side, record which side's
    top-k hubs they reach first.  RWC = P(aa)P(bb) - P(ab)P(ba); 0 = no controversy, 1 = fully separated."""
    rng = np.random.default_rng(seed)
    deg = dict(G_und.degree(weight="weight"))
    hubs = {"a": set(sorted(side_a, key=lambda n: -deg.get(n, 0))[:k]), "b": set(sorted(side_b, key=lambda n: -deg.get(n, 0))[:k])}
    sides = {"a": list(side_a), "b": list(side_b)}
    counts = {("a", "a"): 0, ("a", "b"): 0, ("b", "a"): 0, ("b", "b"): 0}
    for start_side in ("a", "b"):
        for _ in range(n_walks):
            node = sides[start_side][rng.integers(len(sides[start_side]))]
            for _step in range(max_len):
                if node in hubs["a"]:
                    counts[(start_side, "a")] += 1; break
                if node in hubs["b"]:
                    counts[(start_side, "b")] += 1; break
                nbrs = list(G_und.neighbors(node))
                if not nbrs:
                    break
                w = np.array([G_und[node][x].get("weight", 1) for x in nbrs], dtype=float)
                node = nbrs[rng.choice(len(nbrs), p=w / w.sum())]
    def p(s, e):
        tot = counts[(s, "a")] + counts[(s, "b")]
        return counts[(s, e)] / tot if tot else 0.0
    return p("a", "a") * p("b", "b") - p("a", "b") * p("b", "a"), counts


def export_gexf(G: nx.Graph, name: str, attrs: dict[str, dict] | None = None):
    """Write GEXF for Gephi. Numeric attributes default to 0 and strings to '' for nodes without a value."""
    H = G.copy()
    for key, mapping in (attrs or {}).items():
        numeric = all(isinstance(v, (int, float, np.integer, np.floating)) for v in list(mapping.values())[:50])
        default = 0 if numeric else ""
        vals = {}
        for n in H.nodes():
            v = mapping.get(n, default)
            if isinstance(v, (np.integer,)): v = int(v)
            elif isinstance(v, (np.floating,)): v = float(v)
            if v is None or (isinstance(v, float) and np.isnan(v)): v = default
            vals[n] = v
        nx.set_node_attributes(H, vals, key)
    for n in H.nodes():
        for k, v in list(H.nodes[n].items()):
            if isinstance(v, (np.integer,)): H.nodes[n][k] = int(v)
            elif isinstance(v, (np.floating,)): H.nodes[n][k] = float(v)
            elif v is None or (isinstance(v, float) and np.isnan(v)): H.nodes[n][k] = ""
    path = GEXF / f"{name}.gexf"
    nx.write_gexf(H, path)
    print(f"gexf saved: {path.relative_to(ROOT)}")


def draw_network(G: nx.Graph, membership: dict, title: str, name: str, top_labels=12, seed=1, node_scale=30, stance=None):
    """Spring layout, nodes coloured by community (or stance), sized by degree, labels on the largest hubs."""
    pos = nx.spring_layout(G, seed=seed, k=0.8 / np.sqrt(max(G.number_of_nodes(), 1)), weight="weight")
    deg = dict(G.degree(weight="weight"))
    comms = sorted(set(membership.values()), key=lambda c: -sum(1 for v in membership.values() if v == c))
    cmap = {c: COMM_COLORS[i % len(COMM_COLORS)] for i, c in enumerate(comms)}
    if stance:
        colors = [PALETTE.get(stance.get(n, "NEUTRAL"), PALETTE["neutral"]) for n in G.nodes()]
    else:
        colors = [cmap.get(membership.get(n), "#cccccc") for n in G.nodes()]
    sizes = [10 + node_scale * np.sqrt(deg.get(n, 0)) for n in G.nodes()]
    fig, ax = plt.subplots(figsize=(11, 9))
    nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.12, width=0.5, arrows=False, edge_color="#555")
    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=sizes, node_color=colors, alpha=0.85, linewidths=0.3, edgecolors="white")
    labels = {n: n for n in sorted(G.nodes(), key=lambda n: -deg.get(n, 0))[:top_labels]}
    nx.draw_networkx_labels(G, pos, labels, ax=ax, font_size=7, font_color="black")
    ax.set_title(title); ax.axis("off"); ax.grid(False)
    savefig(name)
    plt.show()


def jsonl_iter(path):
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def pct(a, b):
    return round(100 * a / b, 1) if b else float("nan")
