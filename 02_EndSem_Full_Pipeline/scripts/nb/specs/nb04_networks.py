FILENAME = "04_Interaction_Networks"
TITLE = "04 - Interaction Networks"

CELLS = [
("md", r"""
# 04 · Interaction Networks

Directed, weighted, homogeneous user networks for each platform. Nodes are accounts; an edge A→B means A replied to, quoted or mentioned B (X) or A replied to B's post or comment (Reddit).
Edge weight = number of posts in which A addressed B (a post that replies to and mentions the same account counts once; the team's earlier network counted it twice, both versions are reported).
"""),
("code", r"""
import sys; sys.path.insert(0, '.')
from csma_lib import *
setup_plots()
x = load_x_unified(); r = load_reddit_unified()
for c in ['is_bot', 'anonymous', 'is_reply', 'is_quote']:
    if c in r: r[c] = r[c].astype(str).str.lower().eq('true')
for c in ['is_reply', 'is_quote']:
    x[c] = x[c].astype(str).str.lower().eq('true')
"""),
("md", r"""
## 1. Edge lists
"""),
("code", r"""
def x_edges(df, dedupe_within_post=True):
    rows = []
    for p in df.itertuples(index=False):
        src = p.author; seen = set()
        cands = []
        if p.is_reply and p.reply_to_author: cands.append((p.reply_to_author, 'reply'))
        if p.is_quote and p.quote_author: cands.append((p.quote_author, 'quote'))
        for m in str(p.mentions).split(','):
            if m: cands.append((m, 'mention'))
        for tgt, et in cands:
            if not tgt or tgt == src: continue
            if dedupe_within_post and tgt in seen: continue
            seen.add(tgt)
            rows.append({'source': src, 'target': tgt, 'edge_type': et, 'post_id': p.post_id, 'thread_id': p.thread_id, 'timestamp': p.timestamp, 'groups': p.groups})
    return pd.DataFrame(rows)
ex = x_edges(x); ex_team = x_edges(x, dedupe_within_post=False)
ok = r[~r.is_bot & ~r.anonymous]
rr = ok[(ok.item_type == 'comment') & (ok.reply_to_author != '') & (ok.reply_to_author != ok.author) & ~ok.reply_to_author.isin(['[deleted]', '[removed]', 'automoderator'])]
er = pd.DataFrame({'source': rr.author, 'target': rr.reply_to_author, 'edge_type': 'reply', 'post_id': rr.post_id, 'thread_id': rr.thread_id, 'timestamp': rr.timestamp, 'groups': rr.groups})
ment = ok[ok.text.str.contains(r'\bu/\w+', regex=True)]
mrows = []
for p in ment.itertuples(index=False):
    for m in set(re.findall(r'\bu/(\w+)', p.text)):
        if m.lower() != p.author: mrows.append({'source': p.author, 'target': m.lower(), 'edge_type': 'mention', 'post_id': p.post_id, 'thread_id': p.thread_id, 'timestamp': p.timestamp, 'groups': p.groups})
er = pd.concat([er, pd.DataFrame(mrows)], ignore_index=True)
save_table(ex, '04_x_edges_raw'); save_table(er, '04_reddit_edges_raw')
print('X interactions:', ex.edge_type.value_counts().to_dict(), '| Reddit interactions:', er.edge_type.value_counts().to_dict())
"""),
("code", r"""
Gx, Gr, Gx_team = build_digraph(ex), build_digraph(er), build_digraph(ex_team)
# the team's midsem network was built on the 1,823-row concatenation of the three group files (posts counted once per group)
team_rows = pd.concat([pd.read_csv(X_PROC / f'Group_{g}_clean.csv', dtype=str, keep_default_na=False, encoding='utf-8-sig') for g in 'ABC'])
team_rows.columns = [c.lstrip('﻿') for c in team_rows.columns]
tr = pd.DataFrame({'author': team_rows.author.str.strip().str.lstrip('@').str.lower(), 'post_id': team_rows.id, 'thread_id': team_rows.thread_id, 'timestamp': pd.to_datetime(team_rows.timestamp, errors='coerce'),
                   'is_reply': team_rows.is_reply.str.lower().eq('true'), 'reply_to_author': team_rows.replied_author.str.strip().str.lstrip('@').str.lower(),
                   'is_quote': team_rows.is_quote_tweet.str.lower().eq('true'), 'quote_author': team_rows.quote_author.str.strip().str.lstrip('@').str.lower(),
                   'mentions': team_rows.mentions.str.lower().str.replace(r'[;\s]+', ',', regex=True), 'groups': team_rows.group})
G_team = build_digraph(x_edges(tr, dedupe_within_post=False))
summ = pd.DataFrame([network_summary(Gx, 'X (this study: 1,727 unique posts, one interaction per post-target)'),
                     network_summary(Gx_team, 'X (unique posts, reply+mention+quote counted separately)'),
                     network_summary(G_team, 'X (midsem replication: 1,823 rows incl. cross-group duplicates)'),
                     network_summary(Gr, 'Reddit (replies in relevant threads + u/ mentions)')])
save_table(summ, '04_network_summary'); summ.T
"""),
("md", r"""
**What this shows:** the midsem numbers (466 nodes, 600 edges, weight 900) are reproduced exactly from the 1,823-row file; removing the 96 cross-group duplicate posts and counting one interaction per post gives the leaner X network used from here on. The Reddit network is an order of magnitude larger and much better connected because whole threads were collected.
"""),
("md", r"""
## 2. Degree distributions and centrality
Betweenness is computed on the largest weakly connected component (exact for X, sampled with k=800 pivots for Reddit).
"""),
("code", r"""
def centrality_table(G, name, k=None):
    W = largest_wcc(G)
    ind, outd = dict(G.in_degree()), dict(G.out_degree())
    wind, woutd = dict(G.in_degree(weight='weight')), dict(G.out_degree(weight='weight'))
    bet = nx.betweenness_centrality(W, k=min(k, W.number_of_nodes()) if k else None, seed=1, normalized=True)
    clo = nx.closeness_centrality(W)
    pr = nx.pagerank(G, weight='weight', alpha=0.85)
    df = pd.DataFrame({'node': list(G.nodes()), 'in_degree': [ind[n] for n in G], 'out_degree': [outd[n] for n in G],
                       'weighted_in': [wind[n] for n in G], 'weighted_out': [woutd[n] for n in G],
                       'betweenness': [bet.get(n, 0.0) for n in G], 'closeness': [clo.get(n, 0.0) for n in G], 'pagerank': [pr[n] for n in G],
                       'in_largest_wcc': [n in W for n in G]})
    df['total_degree'] = df.in_degree + df.out_degree
    save_table(df.sort_values('weighted_in', ascending=False), f'04_{name}_centrality')
    return df
cx = centrality_table(Gx, 'x'); cr = centrality_table(Gr, 'reddit', k=800)
xa = pd.read_csv(X_PROC / 'x_authors.csv'); cx = cx.merge(xa[['author', 'account_type', 'followers']].rename(columns={'author': 'node'}), on='node', how='left')
cx['account_type'] = cx.account_type.fillna('not_in_corpus (only addressed)')
top = pd.concat([cx.sort_values('weighted_in', ascending=False).head(12).assign(platform='x', rank_by='weighted in-degree'),
                 cx.sort_values('betweenness', ascending=False).head(12).assign(platform='x', rank_by='betweenness'),
                 cr.sort_values('weighted_in', ascending=False).head(12).assign(platform='reddit', rank_by='weighted in-degree'),
                 cr.sort_values('betweenness', ascending=False).head(12).assign(platform='reddit', rank_by='betweenness')])
save_table(top, '04_top_actors')
top[['platform', 'rank_by', 'node', 'in_degree', 'out_degree', 'weighted_in', 'weighted_out', 'betweenness', 'pagerank']].head(24)
"""),
("code", r"""
fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
for ax, (G, lab, col) in zip(axes, [(Gx, 'X', PALETTE['x']), (Gr, 'Reddit', PALETTE['reddit'])]):
    for deg, m in [(dict(G.in_degree()), 'o'), (dict(G.out_degree()), 's')]:
        vc = pd.Series(list(deg.values())).value_counts().sort_index(); vc = vc[vc.index > 0]
        ax.loglog(vc.index, vc.values / vc.sum(), m, ms=4, alpha=0.7, color=col if m == 'o' else '#444', label='in-degree' if m == 'o' else 'out-degree')
    ax.set_title(f'{lab}: degree distribution'); ax.set_xlabel('degree'); ax.set_ylabel('fraction of nodes'); ax.legend()
savefig('04_degree_distributions'); plt.show()
"""),
("md", r"""
**What this shows:** both networks are heavy-tailed. On X a handful of accounts (the CJP founder and official account, Wangchuk, Delhi Police, news handles) receive most interactions while most accounts only send; on Reddit the in-degree tail is flatter because replies are spread across many commenters.
"""),
("md", r"""
## 3. Visualisation and Gephi export
"""),
("code", r"""
Wx, Wr = largest_wcc(Gx), largest_wcc(Gr)
from csma_viz import draw_grouped
acct = dict(zip(xa.author, xa.account_type))
gx = {n: acct.get(n, 'addressed only (never posted)') for n in Wx}
draw_grouped(Wx, gx, f'X interaction network — largest component ({Wx.number_of_nodes()} accounts), grouped by account type', '04_x_largest_wcc',
             group_labels={g: f"{g} ({sum(1 for v in gx.values() if v == g)})" for g in set(gx.values())}, top_labels_per_group=3)
# Reddit: group by the user's main subreddit (12 most common in the component, rest = other), 100 most-connected users per group
subr = r[~r.is_bot & ~r.anonymous].groupby('author').subreddit.agg(lambda s: s.value_counts().index[0])
ms = pd.Series({n: subr.get(n, 'other') for n in Wr}); top_subs = ms.value_counts().head(12).index
gr = {n: (f'r/{v}' if v in top_subs else 'other subreddits') for n, v in ms.items()}
draw_grouped(Wr, gr, f'Reddit interaction network — largest component ({Wr.number_of_nodes():,} users; 100 most-connected users per group shown), grouped by main subreddit',
             '04_reddit_largest_wcc_core', group_labels={g: f"{g} ({sum(1 for v in gr.values() if v == g)})" for g in set(gr.values())}, max_nodes_per_group=100, top_labels_per_group=2)
npost_x = x.groupby('author').size().to_dict(); npost_r = r.groupby('author').size().to_dict()
export_gexf(Gx, 'x_interaction_network', {'account_type': acct, 'n_posts': npost_x, 'followers': dict(zip(xa.author, xa.followers))})
export_gexf(Gr, 'reddit_interaction_network', {'main_subreddit': subr.to_dict(), 'n_items': npost_r})
"""),
("md", r"""
**What this shows:** the X component is a star-like structure around the CJP accounts with secondary hubs (police, news, opposition politicians); the Reddit core is a web of mutual replies with no single centre. Both GEXF files open directly in Gephi for the team's own layouts.
"""),
]
