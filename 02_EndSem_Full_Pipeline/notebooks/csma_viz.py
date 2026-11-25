"""Readable network figures: community-grouped layout, discs per group, hub labels with halos, legends.

Use: from csma_viz import draw_grouped, draw_meta
"""
from collections import defaultdict

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib.lines import Line2D

from csma_lib import COMM_COLORS, PALETTE, savefig

try:
    from adjustText import adjust_text
except Exception:  # optional dependency
    adjust_text = None


def group_members(G, groups):
    members = defaultdict(list)
    for n in G.nodes():
        members[groups.get(n, "other")].append(n)
    return members


def grouped_layout(G, groups, seed=1, margin=0.20):
    """Place each group on its own disc (centres from a spring layout of the group meta-graph, overlaps pushed apart),
    then lay out the nodes of each group inside its disc. Returns pos, centres, radii, members."""
    members = group_members(G, groups)
    gids = sorted(members, key=lambda g: -len(members[g]))
    M = nx.Graph(); M.add_nodes_from(gids)
    for u, v in G.edges():
        gu, gv = groups.get(u, "other"), groups.get(v, "other")
        if gu != gv:
            M.add_edge(gu, gv, weight=M[gu][gv]["weight"] + 1 if M.has_edge(gu, gv) else 1)
    n_tot = max(G.number_of_nodes(), 1)
    radius = {g: 0.07 + 0.45 * np.sqrt(len(members[g]) / n_tot) for g in gids}
    if len(gids) > 1:
        centres = nx.spring_layout(M, seed=seed, weight="weight", k=1.1 / np.sqrt(len(gids)), iterations=300, scale=1.0)
    else:
        centres = {gids[0]: np.zeros(2)}
    C = {g: np.array(centres[g], dtype=float) for g in gids}
    for _ in range(600):  # remove overlaps between discs
        moved = False
        for i, a in enumerate(gids):
            for b in gids[i + 1:]:
                d = C[b] - C[a]; dist = float(np.linalg.norm(d)); need = radius[a] + radius[b] + margin
                if dist < need:
                    direction = d / dist if dist > 1e-9 else np.array([1.0, 0.0])
                    push = direction * (need - dist) / 2
                    C[a] -= push; C[b] += push; moved = True
        if not moved:
            break
    pos = {}
    deg = dict(G.degree(weight="weight")); golden = np.pi * (3 - np.sqrt(5))
    for g in gids:
        ns = sorted(members[g], key=lambda n: -deg.get(n, 0))   # hubs in the centre of the disc
        m = len(ns)
        for i, n in enumerate(ns):
            r = radius[g] * 0.88 * np.sqrt((i + 0.5) / m) if m > 1 else 0.0
            theta = i * golden
            pos[n] = C[g] + np.array([r * np.cos(theta), r * np.sin(theta)])
    return pos, C, radius, members


def _sample(G, groups, max_nodes_per_group):
    deg = dict(G.degree(weight="weight")); keep = []
    for g, ns in group_members(G, groups).items():
        keep += sorted(ns, key=lambda n: -deg.get(n, 0))[:max_nodes_per_group]
    return G.subgraph(keep).copy()


def draw_grouped(G, groups, title, name, group_labels=None, node_color=None, color_legend=None, top_labels_per_group=2,
                 max_nodes_per_group=None, seed=1, figsize=(14, 11), edge_alpha=0.18, label_size=7.5, tag_size=8):
    """G: (di)graph with 'weight' on edges. groups: node -> group id. group_labels: group id -> tag text.
    node_color: optional node -> colour (e.g. stance); color_legend: list of (label, colour) for that colouring."""
    if max_nodes_per_group:
        G = _sample(G, groups, max_nodes_per_group)
    pos, C, radius, members = grouped_layout(G, groups, seed=seed)
    gids = sorted(members, key=lambda g: -len(members[g]))
    cmap = {g: COMM_COLORS[i % len(COMM_COLORS)] for i, g in enumerate(gids)}
    deg = dict(G.degree(weight="weight")); dmax = max(deg.values()) if deg else 1
    fig, ax = plt.subplots(figsize=figsize)
    for g in gids:
        ax.add_patch(plt.Circle(C[g], radius[g], color=cmap[g], alpha=0.08, lw=0))
    Gu = G.to_undirected() if G.is_directed() else G
    within = [(u, v) for u, v in Gu.edges() if groups.get(u, "other") == groups.get(v, "other")]
    cross = [(u, v) for u, v in Gu.edges() if groups.get(u, "other") != groups.get(v, "other")]
    if cross:
        nx.draw_networkx_edges(Gu, pos, edgelist=cross, ax=ax, edge_color="#9a9a9a", alpha=edge_alpha * 0.8, width=0.5)
    if within:
        nx.draw_networkx_edges(Gu, pos, edgelist=within, ax=ax, edge_color=[cmap[groups.get(u, "other")] for u, v in within], alpha=edge_alpha, width=0.6)
    colors = [cmap[groups.get(n, "other")] for n in G.nodes()] if node_color is None else [node_color.get(n, "#bdbdbd") for n in G.nodes()]
    sizes = [14 + 300 * np.sqrt(deg.get(n, 0) / dmax) for n in G.nodes()]
    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=sizes, node_color=colors, alpha=0.92, linewidths=0.4, edgecolors="white")
    texts, tags = [], []
    for g in gids:
        for n in sorted(members[g], key=lambda n: -deg.get(n, 0))[:top_labels_per_group]:
            texts.append(ax.text(pos[n][0], pos[n][1], n, fontsize=label_size, ha="center", va="center", color="#111111",
                                 path_effects=[pe.withStroke(linewidth=2.6, foreground="white")], zorder=5))
        tag = (group_labels or {}).get(g, str(g))
        if len(tag) > 26:   # wrap long tags on two lines at the last separator before the middle
            cut = max(tag.rfind(" · ", 0, len(tag) // 2 + 8), tag.rfind(" ", 0, len(tag) // 2 + 8))
            tag = tag[:cut] + "\n" + tag[cut:].lstrip(" ·") if cut > 0 else tag
        tags.append(ax.text(C[g][0], C[g][1] + radius[g] + 0.02, tag, fontsize=tag_size, ha="center", va="bottom", color=cmap[g], fontweight="bold",
                            path_effects=[pe.withStroke(linewidth=2.2, foreground="white")], zorder=6))
    if adjust_text is not None and (texts or tags):
        try:
            adjust_text(texts, ax=ax, expand=(1.15, 1.35), arrowprops=dict(arrowstyle="-", color="#666666", lw=0.4))
            adjust_text(tags, ax=ax, expand=(1.05, 1.3), only_move={"text": "xy"}, force_text=(0.4, 0.8))
        except Exception:
            pass
    if color_legend:
        ax.legend(handles=[Line2D([0], [0], marker="o", color="w", markerfacecolor=c, markersize=8, label=l) for l, c in color_legend],
                  loc="lower left", fontsize=8, frameon=True)
    ax.set_title(title, fontsize=12); ax.set_aspect("equal"); ax.axis("off"); ax.grid(False)
    xs = np.array([p[0] for p in pos.values()]); ys = np.array([p[1] for p in pos.values()])
    pad = 0.25; ax.set_xlim(xs.min() - pad, xs.max() + pad); ax.set_ylim(ys.min() - pad, ys.max() + pad * 1.4)
    savefig(name); plt.show()
    return pos, C, radius


def draw_meta(meta_edges, sizes, labels, name, title, centres=None, seed=1, figsize=(10, 9)):
    """Community meta-network: nodes = groups (size ∝ members), directed edges with width ∝ weight, self-loops dropped.
    meta_edges: iterable of (from, to, weight); sizes: group -> n members; labels: group -> text; centres: optional group -> (x, y)."""
    M = nx.DiGraph()
    for g in sizes:
        M.add_node(g)
    for u, v, w in meta_edges:
        if u != v and u in sizes and v in sizes:
            M.add_edge(u, v, weight=w)
    gids = sorted(sizes, key=lambda g: -sizes[g]); cmap = {g: COMM_COLORS[i % len(COMM_COLORS)] for i, g in enumerate(gids)}
    pos = {g: np.array(centres[g]) for g in gids} if centres else nx.circular_layout(M)
    fig, ax = plt.subplots(figsize=figsize)
    wmax = max([d["weight"] for _, _, d in M.edges(data=True)] or [1])
    for u, v, d in M.edges(data=True):
        ax.annotate("", xy=pos[v], xytext=pos[u], arrowprops=dict(arrowstyle="-|>", color="#555555", alpha=0.25 + 0.6 * d["weight"] / wmax,
                                                                 lw=0.4 + 5 * d["weight"] / wmax, connectionstyle="arc3,rad=0.18", shrinkA=14, shrinkB=14))
    smax = max(sizes.values())
    nx.draw_networkx_nodes(M, pos, ax=ax, nodelist=gids, node_size=[300 + 2600 * sizes[g] / smax for g in gids], node_color=[cmap[g] for g in gids], alpha=0.9, linewidths=0.6, edgecolors="white")
    for g in gids:
        ax.text(pos[g][0], pos[g][1], labels.get(g, str(g)), fontsize=7.5, ha="center", va="center", color="#111111",
                path_effects=[pe.withStroke(linewidth=2.2, foreground="white")], zorder=5)
    ax.set_title(title, fontsize=12); ax.set_aspect("equal"); ax.axis("off"); ax.grid(False)
    xs = np.array([p[0] for p in pos.values()]); ys = np.array([p[1] for p in pos.values()]); pad = 0.3
    ax.set_xlim(xs.min() - pad, xs.max() + pad); ax.set_ylim(ys.min() - pad, ys.max() + pad)
    savefig(name); plt.show()
