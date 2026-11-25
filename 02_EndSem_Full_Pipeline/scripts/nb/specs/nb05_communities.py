FILENAME = "05_Community_Detection"
TITLE = "05 - Community Detection"

CELLS = [
("md", r"""
# 05 · Community Detection

Louvain modularity optimisation (Blondel et al., 2008) on the largest weakly connected component of each network, direction ignored and
opposite-direction weights summed, as in the midsem report. The partition is run with 20 random seeds; the best-modularity run is kept and
the agreement between runs (mean pairwise NMI) is reported as a stability check, together with a resolution sweep.
"""),
("code", r"""
import sys; sys.path.insert(0, '.')
from csma_lib import *
setup_plots()
MIN_MAJOR = {'x': 8, 'reddit': 30}          # a community is "major" (characterised in 06) if it is among the 15 largest and at least this large
TOP_K = 15
Gs = {'x': load_graph('x'), 'reddit': load_graph('reddit')}
"""),
("code", r"""
results, memberships, robustness = {}, {}, []
for p, G in Gs.items():
    W = largest_wcc(G); U = nx.Graph()
    for u, v, d in W.edges(data=True):
        U.add_edge(u, v, weight=U[u][v]['weight'] + d['weight'] if U.has_edge(u, v) else d['weight'])
    parts, stab = louvain_stable(U, seeds=range(20))
    for res in [0.6, 1.0, 1.4]:
        pr, st = louvain_stable(U, seeds=range(5), resolution=res)
        robustness.append({'platform': p, 'resolution': res, 'communities': len(pr), 'communities_>=min_size': sum(len(c) >= MIN_MAJOR[p] for c in pr), 'modularity_best': round(st['modularity_best'], 4), 'mean_pairwise_nmi': round(st['mean_pairwise_nmi'], 3)})
    lp = list(nx.community.label_propagation_communities(U))
    from sklearn.metrics import normalized_mutual_info_score as nmi
    nodes = list(U.nodes()); m1 = {n: i for i, c in enumerate(parts) for n in c}; m2 = {n: i for i, c in enumerate(lp) for n in c}
    stab['nmi_vs_label_propagation'] = nmi([m1[n] for n in nodes], [m2[n] for n in nodes])
    parts = sorted(parts, key=len, reverse=True)
    mem = {n: i + 1 for i, c in enumerate(parts) for n in c}
    results[p] = {'U': U, 'W': W, 'parts': parts, 'stab': stab}; memberships[p] = mem
    print(f"{p}: largest WCC {U.number_of_nodes()} nodes, {len(parts)} communities, Q={stab['modularity_best']:.4f} (mean {stab['modularity_mean']:.4f} ± {stab['modularity_sd']:.4f}), "
          f"stability NMI={stab['mean_pairwise_nmi']:.3f}, vs label propagation NMI={stab['nmi_vs_label_propagation']:.3f}")
rob = pd.DataFrame(robustness); save_table(rob, '05_robustness'); rob
"""),
("md", r"""
**What this shows:** the partitions are stable across seeds (NMI close to 1 means the same groups are found every time) and the number of large communities changes little with the resolution parameter, so the community structure is a property of the data and not of one run.
"""),
("code", r"""
xa = pd.read_csv(X_PROC / 'x_authors.csv'); acct = dict(zip(xa.author, xa.account_type))
r = load_reddit_unified(); r = r[~r.is_bot.astype(str).str.lower().eq('true')]
subr = r.groupby('author').subreddit.agg(lambda s: s.value_counts().index[0]).to_dict()
summaries = {}
for p in Gs:
    U, W, parts, mem = results[p]['U'], results[p]['W'], results[p]['parts'], memberships[p]
    cent = pd.read_csv(TABLES / f'04_{p}_centrality.csv', dtype={'node': str})
    mdf = cent[cent.node.isin(mem)].copy(); mdf['community'] = mdf.node.map(mem); mdf['is_major'] = mdf.community.map(lambda c: c <= TOP_K and len(parts[c - 1]) >= MIN_MAJOR[p])
    mdf['attribute'] = mdf.node.map(acct if p == 'x' else subr).fillna('other')
    save_table(mdf.sort_values(['community', 'weighted_in'], ascending=[True, False]), f'05_{p}_community_membership')
    rows = []
    for i, c in enumerate(parts, 1):
        S = U.subgraph(c); win = W.subgraph(c)
        hubs = sorted(c, key=lambda n: -W.in_degree(n, weight='weight'))[:3]
        senders = sorted(c, key=lambda n: -W.out_degree(n, weight='weight'))[:3]
        comp = pd.Series([mdf.set_index('node').attribute.get(n, 'other') for n in c]).value_counts(normalize=True)
        rows.append({'community': i, 'size': len(c), 'share_of_wcc_%': pct(len(c), U.number_of_nodes()), 'internal_edges': S.number_of_edges(),
                     'internal_weight': int(sum(d['weight'] for _, _, d in S.edges(data=True))), 'density': round(nx.density(S), 4),
                     'top_hubs_in': ', '.join(hubs), 'top_senders_out': ', '.join(senders),
                     'composition_top': '; '.join(f'{k} {v*100:.0f}%' for k, v in comp.head(3).items()), 'is_major': i <= TOP_K and len(c) >= MIN_MAJOR[p]})
    summ = pd.DataFrame(rows); summaries[p] = summ
    save_table(summ, f'05_{p}_community_summary')
display(summaries['x'].head(15)); display(summaries['reddit'].head(15))
"""),
("md", r"""
**What this shows:** on X the largest communities form around the CJP accounts, around Delhi Police / government handles, and around clusters of news media and opposition politicians; on Reddit the large communities follow subreddits (the CJP subreddits, r/india-type general subreddits and the meme/teen subreddits), which already hints at platform-specific sorting mechanisms.
"""),
("code", r"""
fig, axes = plt.subplots(1, 2, figsize=(13, 4))
for ax, p in zip(axes, Gs):
    s = summaries[p]; ax.bar(s.community, s['size'], color=[COMM_COLORS[(i - 1) % len(COMM_COLORS)] for i in s.community])
    ax.axhline(MIN_MAJOR[p], ls='--', color='#444', lw=0.8); ax.set_title(f'{p}: community sizes (dashed = minimum size; the 15 largest are characterised)'); ax.set_xlabel('community'); ax.set_ylabel('accounts')
savefig('05_community_sizes'); plt.show()
from csma_viz import draw_grouped, draw_meta
centres = {}
for p in Gs:
    U, mem, summ = results[p]['U'], memberships[p], summaries[p]
    sizes = dict(zip(summ.community, summ['size'])); hubs = dict(zip(summ.community, summ.top_hubs_in.str.split(', ').str[0]))
    glab = {c: f"C{c} ({sizes[c]}) · {hubs[c]}" for c in sizes}
    if p == 'reddit':
        majors = set(summ[summ.is_major].community); Um = U.subgraph([n for n in U if mem[n] in majors])
        _, C, _ = draw_grouped(Um, mem, f'Reddit: the {len(majors)} largest communities (80 most-connected users each; colour = community, label = top hub)', '05_reddit_communities', group_labels=glab, max_nodes_per_group=80, top_labels_per_group=2)
    else:
        _, C, _ = draw_grouped(U, mem, f'X: Louvain communities in the largest component ({U.number_of_nodes()} accounts; colour = community, label = top hub)', '05_x_communities', group_labels=glab, top_labels_per_group=2)
    centres[p] = C
"""),
("code", r"""
# Community meta-network: how much interaction flows between communities (directed weights), majors only
for p in Gs:
    W, mem, summ = results[p]['W'], memberships[p], summaries[p]
    majors = set(summ[summ.is_major].community)
    M = nx.DiGraph()
    for u, v, d in W.edges(data=True):
        cu, cv = mem[u], mem[v]
        if cu in majors and cv in majors:
            M.add_edge(cu, cv, weight=M[cu][cv]['weight'] + d['weight'] if M.has_edge(cu, cv) else d['weight'])
    meta = pd.DataFrame([{'from_community': u, 'to_community': v, 'weight': d['weight']} for u, v, d in M.edges(data=True)]).sort_values('weight', ascending=False)
    save_table(meta, f'05_{p}_community_meta_edges')
    sizes = {c: len(results[p]['parts'][c - 1]) for c in M.nodes()}
    draw_meta([(u, v, d['weight']) for u, v, d in M.edges(data=True)], sizes, {c: f'C{c}\n({sizes[c]})' for c in sizes}, f'05_{p}_community_meta_network',
              f'{p}: interaction between major communities (arrow width = weight; self-loops not drawn)', centres={c: centres[p][c] for c in sizes if c in centres[p]} if all(c in centres[p] for c in sizes) else None)
    export_gexf(W, f'{p}_largest_wcc_communities', {'community': {n: str(c) for n, c in mem.items()}})
"""),
("md", r"""
**What this shows:** most interaction weight stays inside communities (the self-loops not drawn carry the largest weights); the between-community flows that exist are concentrated on a few pairs, which notebook 08 tests against a null model and reads together with stance.
"""),
]
