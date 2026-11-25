FILENAME = "08_Polarization_CrossCommunity"
TITLE = "08 - Polarization & Cross-Community Interaction"

CELLS = [
("md", r"""
# 08 · Polarization and Cross-Community Interaction

Measures how segregated each network is (structurally and by stance), whether the observed level of cross-community interaction is lower than
chance for networks with the same degrees, which bridge users connect communities, and whether cross-stance contacts look like engagement or attacks.
Metrics: modularity, Krackhardt E–I index, stance assortativity, Random-Walk Controversy (Garimella et al., 2018), stance mixing matrices with
a configuration-model null, participation coefficient (Guimerà & Amaral, 2005) for bridges, and the hostility rate of cross-stance contacts.
"""),
("code", r"""
import sys; sys.path.insert(0, '.')
from csma_lib import *
setup_plots()
P = ['x', 'reddit']
G = {p: load_graph(p) for p in P}
mem = {p: dict(zip(load_membership(p).node, load_membership(p).community)) for p in P}
major = {p: set(load_membership(p).query('is_major == True').community.astype(int)) if load_membership(p).is_major.dtype == bool else set(load_membership(p)[load_membership(p).is_major.astype(str).str.lower() == 'true'].community.astype(int)) for p in P}
ust = {p: dict(zip(pd.read_csv(TABLES / f'06_{p}_user_stance.csv').author, pd.read_csv(TABLES / f'06_{p}_user_stance.csv').user_stance)) for p in P}
pst = {p: load_stance(p) for p in P}
edges = {p: load_edges(p) for p in P}
items = {p: (load_x_unified() if p == 'x' else load_reddit_unified()) for p in P}
def undirected_wcc(Gd):
    W = largest_wcc(Gd); U = nx.Graph()
    for u, v, d in W.edges(data=True):
        U.add_edge(u, v, weight=U[u][v]['weight'] + d['weight'] if U.has_edge(u, v) else d['weight'])
    return W, U
W, U = {}, {}
for p in P: W[p], U[p] = undirected_wcc(G[p])
"""),
("md", r"""
## 1. Structural and stance-based polarization
"""),
("code", r"""
def cross_share(Gu, m):
    E = sum(1 for u, v in Gu.edges() if m.get(u) != m.get(v)); return E / Gu.number_of_edges()
def null_cross(Gu, m, n=150, seed=0):
    vals = []
    for i in range(n):
        H = Gu.copy(); nx.double_edge_swap(H, nswap=2 * H.number_of_edges(), max_tries=40 * H.number_of_edges(), seed=seed + i)
        vals.append(cross_share(H, m))
    return np.array(vals)
rows, nulls = [], {}
for p in P:
    m = mem[p]; Gu = U[p]
    q = nx.community.modularity(Gu, [{n for n in Gu if m.get(n) == c} for c in set(m.values())], weight='weight')
    ei_comm = ei_index(Gu, m)
    obs = cross_share(Gu, m); nd = null_cross(Gu, m, n=150 if p == 'x' else 100); nulls[p] = (obs, nd)
    z = (obs - nd.mean()) / nd.std(); pval = (nd <= obs).mean()
    # stance partition (PRO vs ANTI users only)
    sm = {n: ust[p].get(n) for n in Gu if ust[p].get(n) in ('PRO', 'ANTI')}
    S = Gu.subgraph(sm).copy()
    ei_stance = ei_index(S, sm)
    Sd = W[p].subgraph(sm).copy(); nx.set_node_attributes(Sd, sm, 'stance')
    assort = nx.attribute_assortativity_coefficient(Sd, 'stance') if Sd.number_of_edges() > 0 else np.nan
    pro, anti = {n for n, s in sm.items() if s == 'PRO'}, {n for n, s in sm.items() if s == 'ANTI'}
    rwc, counts = random_walk_controversy(S, pro, anti, k=10, n_walks=3000, seed=1)
    rng = np.random.default_rng(3); rwc_null = []
    labs = list(sm.values()); nodes = list(sm)
    for i in range(30):
        rng.shuffle(labs); sh = dict(zip(nodes, labs))
        rwc_null.append(random_walk_controversy(S, {n for n in nodes if sh[n] == 'PRO'}, {n for n in nodes if sh[n] == 'ANTI'}, k=10, n_walks=1000, seed=i)[0])
    rows += [
        {'platform': p, 'metric': 'modularity of Louvain partition (weighted)', 'value': round(q, 4)},
        {'platform': p, 'metric': 'E-I index, community partition (-1 segregated … +1 all external)', 'value': round(ei_comm, 4)},
        {'platform': p, 'metric': 'share of edges crossing communities (observed)', 'value': round(obs, 4), 'null_mean': round(nd.mean(), 4), 'null_sd': round(nd.std(), 4), 'z': round(z, 2), 'p_null_le_obs': round(pval, 3)},
        {'platform': p, 'metric': 'E-I index, stance partition (PRO vs ANTI users)', 'value': round(ei_stance, 4), 'n_nodes': S.number_of_nodes(), 'n_edges': S.number_of_edges()},
        {'platform': p, 'metric': 'stance assortativity (directed, PRO/ANTI users)', 'value': round(assort, 4)},
        {'platform': p, 'metric': 'Random-Walk Controversy PRO vs ANTI (k=10 hubs)', 'value': round(rwc, 4), 'null_mean': round(float(np.mean(rwc_null)), 4), 'null_sd': round(float(np.std(rwc_null)), 4)},
    ]
pol = pd.DataFrame(rows); save_table(pol, '08_polarization_metrics'); pol
"""),
("code", r"""
fig, axes = plt.subplots(1, 2, figsize=(12, 4))
for ax, p in zip(axes, P):
    obs, nd = nulls[p]; ax.hist(nd, bins=25, color='#bbb', label='degree-preserving rewiring'); ax.axvline(obs, color=PALETTE[p], lw=2, label=f'observed = {obs:.3f}')
    ax.set_title(f'{p}: share of edges between communities'); ax.set_xlabel('cross-community edge share'); ax.legend()
savefig('08_null_model'); plt.show()
"""),
("md", r"""
**What this shows:** on both platforms the share of interaction crossing community lines is far below what degree-preserving random networks produce (z-scores strongly negative), so the communities are real structural enclosures. By *stance*, however, the two platforms differ: the stance E–I index and the Random-Walk Controversy score are higher on X (opposite camps rarely touch) than on Reddit, where PRO and ANTI users meet inside the same threads.
"""),
("md", r"""
## 2. Who talks to whom — stance mixing matrices
Interaction counts by stance of the source and target user, compared with the counts expected if stances were independent (ratio > 1 = more than expected).
"""),
("code", r"""
mix_tables = {}
for p in P:
    e = edges[p].copy(); e['src'] = e.source.map(ust[p]).fillna('NEUTRAL'); e['tgt'] = e.target.map(ust[p]).fillna('no_posts')
    e = e[e.tgt != 'no_posts']
    obs = pd.crosstab(e.src, e.tgt).reindex(index=['PRO', 'NEUTRAL', 'ANTI'], columns=['PRO', 'NEUTRAL', 'ANTI'], fill_value=0)
    exp = np.outer(obs.sum(1), obs.sum(0)) / obs.values.sum()
    ratio = (obs / exp).round(2); mix_tables[p] = (obs, ratio)
    save_table(obs.reset_index().rename(columns={'src': 'source_stance \\ target_stance'}), f'08_{p}_stance_mixing_counts'); save_table(ratio.reset_index().rename(columns={'src': 'source_stance \\ target_stance'}), f'08_{p}_stance_mixing_ratio')
fig, axes = plt.subplots(1, 2, figsize=(10, 4))
for ax, p in zip(axes, P):
    obs, ratio = mix_tables[p]; im = ax.imshow(ratio.values, cmap='RdBu_r', vmin=0, vmax=2); ax.set_xticks(range(3)); ax.set_yticks(range(3)); ax.set_xticklabels(ratio.columns); ax.set_yticklabels(ratio.index); ax.set_xlabel('target user stance'); ax.set_ylabel('source user stance'); ax.grid(False)
    for i in range(3):
        for j in range(3): ax.text(j, i, f'{ratio.values[i, j]:.2f}\n(n={obs.values[i, j]})', ha='center', va='center', fontsize=8)
    ax.set_title(f'{p}: observed / expected interactions'); plt.colorbar(im, ax=ax, fraction=0.04)
savefig('08_mixing_matrices'); plt.show()
display(mix_tables['x'][0]); mix_tables['reddit'][0]
"""),
("md", r"""
**What this shows:** on X, ANTI users address PRO hubs far more than expected (the CJP accounts are the target of criticism) while PRO users mostly address other PRO or NEUTRAL (news, police) accounts — cross-stance contact is asymmetric and runs from critics to the movement. On Reddit the matrix is closer to independence: both sides reply to each other at roughly the expected rate.
"""),
("md", r"""
## 3. Engagement or attack? Quality of cross-stance contacts
Every interaction is classified by the stance of the two users and by whether the item is hostile; on Reddit the stance of the parent item is also available.
"""),
("code", r"""
qual_rows, pair_rows = [], []
for p in P:
    e = edges[p].merge(pst[p][['post_id', 'stance', 'hostile']], on='post_id', how='left')
    e['src'] = e.source.map(ust[p]).fillna('NEUTRAL'); e['tgt'] = e.target.map(ust[p]).fillna('NEUTRAL')
    e['pair'] = np.select([(e.src == e.tgt) & e.src.isin(['PRO', 'ANTI']), e.src.isin(['PRO', 'ANTI']) & e.tgt.isin(['PRO', 'ANTI']) & (e.src != e.tgt)], ['same side', 'opposite sides'], 'involves neutral')
    g = e.groupby('pair').agg(interactions=('post_id', 'size'), hostile_share=('hostile', 'mean'), reciprocated=('source', lambda s: np.nan)).reset_index()
    # reciprocity per pair type
    Gd = G[p]
    for i, row in g.iterrows():
        sub = e[e.pair == row.pair]; pairs = set(zip(sub.source, sub.target))
        g.loc[i, 'reciprocated'] = np.mean([Gd.has_edge(v, u) for u, v in pairs]) if pairs else np.nan
    g['platform'] = p; qual_rows.append(g)
    if p == 'reddit':
        it = items[p]; parent_stance = dict(zip(pst[p].post_id, pst[p].stance)); par = dict(zip(it.post_id, it.parent_id))
        e['parent_stance'] = e.post_id.map(par).map(parent_stance)
        agree = e.dropna(subset=['parent_stance']); agree = agree[agree.stance.isin(['PRO', 'ANTI']) & agree.parent_stance.isin(['PRO', 'ANTI'])]
        pair_rows.append(pd.crosstab(agree.parent_stance, agree.stance).rename_axis('parent item stance').reset_index())
qual = pd.concat(qual_rows); save_table(qual, '08_cross_stance_quality')
if pair_rows: save_table(pair_rows[0], '08_reddit_reply_vs_parent_stance')
fig, ax = plt.subplots(figsize=(7, 3.8))
qv = qual.pivot(index='pair', columns='platform', values='hostile_share').reindex(['same side', 'opposite sides', 'involves neutral']) * 100
qv.plot.bar(ax=ax, color=[PALETTE['reddit'], PALETTE['x']]); ax.set_ylabel('% hostile items'); ax.set_title('Hostility of interactions by stance relation'); ax.set_xlabel('')
savefig('08_cross_stance_hostility'); plt.show()
display(qual); pair_rows[0] if pair_rows else None
"""),
("md", r"""
**What this shows:** contacts between opposite camps are several times more likely to be hostile than contacts within a camp on both platforms, and they are rarely reciprocated — most cross-stance interaction is one-directional criticism rather than dialogue. Reddit replies to PRO items are nevertheless more often PRO than ANTI, i.e. threads mostly amplify rather than contest.
"""),
("md", r"""
## 4. Bridge users
Participation coefficient (how evenly a user's links spread across communities) combined with betweenness. Bridges = participation ≥ 0.5 with at least 4 (X) / 8 (Reddit) distinct contacts, or top 2 % betweenness.
"""),
("code", r"""
bridge_tabs = {}
for p in P:
    Gu, m = U[p], mem[p]
    pc = participation_coefficient(Gu, m); cent = pd.read_csv(TABLES / f'04_{p}_centrality.csv', dtype={'node': str}).set_index('node')
    deg = dict(Gu.degree())
    df = pd.DataFrame({'node': list(Gu.nodes())}); df['community'] = df.node.map(m); df['participation'] = df.node.map(pc); df['contacts'] = df.node.map(deg)
    df['betweenness'] = df.node.map(cent.betweenness); df['weighted_in'] = df.node.map(cent.weighted_in); df['weighted_out'] = df.node.map(cent.weighted_out)
    df['user_stance'] = df.node.map(ust[p]).fillna('no_posts')
    thr = {'x': 4, 'reddit': 8}[p]; top_b = df.betweenness.quantile(0.98)
    df['is_bridge'] = ((df.participation >= 0.5) & (df.contacts >= thr)) | (df.betweenness >= top_b)
    # communities each bridge connects
    conn = {}
    for n in df[df.is_bridge].node:
        cs = Counter(m.get(nb) for nb in Gu.neighbors(n)); conn[n] = ', '.join(f'C{c}({k})' for c, k in cs.most_common(4))
    df['connects'] = df.node.map(conn).fillna('')
    if p == 'x':
        xa = pd.read_csv(X_PROC / 'x_authors.csv'); df['account_type'] = df.node.map(dict(zip(xa.author, xa.account_type))).fillna('addressed only')
    hs = pst[p].groupby('author').hostile.mean(); df['hostile_share'] = df.node.map(hs)
    df = df.sort_values(['is_bridge', 'betweenness'], ascending=[False, False]); bridge_tabs[p] = df
    save_table(df[df.is_bridge], f'08_{p}_bridges')
    print(f"{p}: {int(df.is_bridge.sum())} bridge users; stance mix among bridges: {df[df.is_bridge].user_stance.value_counts().to_dict()}")
fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
for ax, p in zip(axes, P):
    df = bridge_tabs[p]
    for st in ['PRO', 'ANTI', 'NEUTRAL', 'no_posts']:
        d = df[df.user_stance == st]; ax.scatter(d.participation, d.betweenness + 1e-6, s=8 + 2 * np.sqrt(d.contacts), alpha=0.6, color=PALETTE.get(st, '#999'), label=st)
    for _, rrow in df[df.is_bridge].head(10).iterrows(): ax.annotate(rrow.node, (rrow.participation, rrow.betweenness + 1e-6), fontsize=6.5)
    ax.set_yscale('log'); ax.set_xlabel('participation coefficient'); ax.set_ylabel('betweenness (log)'); ax.set_title(f'{p}: bridge users'); ax.legend(fontsize=7)
savefig('08_bridges_scatter'); plt.show()
bridge_tabs['x'][bridge_tabs['x'].is_bridge][['node', 'community', 'participation', 'contacts', 'betweenness', 'user_stance', 'account_type', 'connects', 'hostile_share']].head(20)
"""),
("md", r"""
**What this shows:** on X the bridges are the CJP's official accounts, Delhi Police's handles, the AI assistant @grok and a few journalists — mostly accounts that are *addressed* by several camps rather than users who themselves talk across camps; on Reddit bridges are ordinary high-activity commenters who post in several subreddits. Bridge users are no less hostile than others, so bridging does not imply moderation.
"""),
("md", r"""
## 5. Strongest cross-community links and the network coloured by stance
"""),
("code", r"""
for p in P:
    prof = pd.read_csv(TABLES / f'06_{p}_community_profile.csv'); lab = dict(zip(prof.community, prof.label))
    meta = pd.read_csv(TABLES / f'05_{p}_community_meta_edges.csv'); meta = meta[meta.from_community != meta.to_community].copy()
    meta['from_label'] = meta.from_community.map(lab); meta['to_label'] = meta.to_community.map(lab)
    save_table(meta.head(15), f'08_{p}_top_cross_community_pairs')
    display(meta.head(8))
    from csma_viz import draw_grouped
    Gu = U[p]; col = {n: PALETTE.get(ust[p].get(n, 'NEUTRAL'), PALETTE['neutral']) for n in Gu}
    majors = set(prof.community); glab = {c: f"C{c} · {lab[c]} ({int(prof.set_index('community').loc[c, 'users'])})" for c in majors}
    legend = [('PRO user', PALETTE['PRO']), ('ANTI user', PALETTE['ANTI']), ('NEUTRAL / no posts', PALETTE['NEUTRAL'])]
    Gm = Gu.subgraph([n for n in Gu if mem[p].get(n) in majors])
    draw_grouped(Gm, mem[p], f'{p}: major communities with users coloured by stance' + (' (80 most-connected users per community)' if p == 'reddit' else ''),
                 f'08_{p}_network_by_stance', group_labels=glab, node_color=col, color_legend=legend, top_labels_per_group=2, max_nodes_per_group=80 if p == 'reddit' else None)
"""),
("md", r"""
**What this shows:** on X the ANTI accounts form their own cluster that reaches into the PRO core only through the CJP hubs; on Reddit PRO and ANTI users are interleaved inside the same thread-based communities, which is the structural signature of cross-community *interaction* rather than of two separate publics.
"""),
]
