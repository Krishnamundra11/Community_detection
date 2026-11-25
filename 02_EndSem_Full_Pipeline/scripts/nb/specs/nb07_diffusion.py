FILENAME = "07_Information_Diffusion"
TITLE = "07 - Information Diffusion Analysis"

CELLS = [
("md", r"""
# 07 · Information Diffusion

How the discussion spread: who joined when, how large conversation cascades became, which content (links, hashtags) travelled across communities,
and how much interaction crossed community lines over time. Cross-platform flow is measured directly through X links posted on Reddit.
"""),
("code", r"""
import sys; sys.path.insert(0, '.')
from csma_lib import *
setup_plots()
x = load_x_unified(); r = load_reddit_unified()
for c in ['is_bot', 'anonymous']:
    r[c] = r[c].astype(str).str.lower().eq('true')
r = r[~r.is_bot & ~r.anonymous]
x['is_bot'] = False; x['anonymous'] = False
items = pd.concat([x, r], ignore_index=True)
mem = {p: dict(zip(load_membership(p).node, load_membership(p).community)) for p in ['x', 'reddit']}
stance = {p: dict(zip(load_stance(p).post_id, load_stance(p).stance)) for p in ['x', 'reddit']}
ustance = {p: dict(zip(pd.read_csv(TABLES / f'06_{p}_user_stance.csv').author, pd.read_csv(TABLES / f'06_{p}_user_stance.csv').user_stance)) for p in ['x', 'reddit']}
items['community'] = [mem[p].get(a, np.nan) for p, a in zip(items.platform, items.author)]
items['stance'] = [stance[p].get(i, 'NEUTRAL') for p, i in zip(items.platform, items.post_id)]
"""),
("md", r"""
## 1. Who joined when — adoption curves
Cumulative share of all authors who posted their first item by each day, split by user stance.
"""),
("code", r"""
first = items.groupby(['platform', 'author']).timestamp.min().reset_index()
first['user_stance'] = [ustance[p].get(a, 'NEUTRAL') for p, a in zip(first.platform, first.author)]
fig, axes = plt.subplots(1, 2, figsize=(13, 4.5), sharey=True)
for ax, p in zip(axes, ['x', 'reddit']):
    f = first[first.platform == p]
    for st in ['PRO', 'ANTI', 'NEUTRAL']:
        g = f[f.user_stance == st].set_index('timestamp').sort_index()
        if len(g) == 0: continue
        cum = pd.Series(1, index=g.index).cumsum() / len(g)
        ax.step(cum.index, cum.values, where='post', color=PALETTE[st], label=f'{st} users (n={len(g)})')
    ax.set_title(f'{p}: cumulative share of users by date of first item'); ax.legend(); annotate_events(ax, every=2, ymax=1.0)
savefig('07_adoption_curves'); plt.show()
adopt = first.groupby(['platform', 'user_stance']).timestamp.agg(['count', 'median']).reset_index()
save_table(adopt, '07_adoption_by_stance'); adopt
"""),
("md", r"""
**What this shows:** on X, most ANTI users appear in the first protest week (6–7 June) and again around the Parliament march, whereas PRO users keep arriving through the hunger-strike period; on Reddit the bulk of all users arrive only in the final week around the resignation.
"""),
("md", r"""
## 2. Cascades
X: a cascade is a root post plus the replies/quotes to it that appear in the corpus. Reddit: a cascade is a submission with its comment tree (size, depth, duration).
"""),
("code", r"""
ex = load_edges('x'); er = load_edges('reddit')
# X cascades by thread_id (root = earliest post in the thread) and by quoted/replied target post
xt = x.groupby('thread_id').agg(size=('post_id', 'size'), authors=('author', 'nunique'), start=('timestamp', 'min'), end=('timestamp', 'max'), root_author=('author', 'first')).reset_index()
xt['duration_h'] = (xt.end - xt.start).dt.total_seconds() / 3600
xt['root_community'] = xt.root_author.map(mem['x'])
# Reddit cascades
rc = r[r.item_type == 'comment']
par = dict(zip(r.post_id, r.parent_id)); depth = {}
def dep(i, guard=0):
    if i in depth: return depth[i]
    p = par.get(i, ''); d = 0 if p == '' else (1 + dep(p, guard + 1) if guard < 300 else 1); depth[i] = d; return d
rc = rc.assign(depth=[dep(i) for i in rc.post_id])
rs = r[r.item_type == 'submission'].set_index('post_id')
rt = rc.groupby('thread_id').agg(comments=('post_id', 'size'), authors=('author', 'nunique'), max_depth=('depth', 'max'), start=('timestamp', 'min'), end=('timestamp', 'max')).reset_index()
rt['posted'] = rt.thread_id.map(rs.timestamp); rt['subreddit'] = rt.thread_id.map(rs.subreddit); rt['op'] = rt.thread_id.map(rs.author)
rt['duration_h'] = (rt.end - rt.posted).dt.total_seconds() / 3600
rt['share_first_24h'] = [float((rc[rc.thread_id == t].timestamp <= rt.loc[i, 'posted'] + pd.Timedelta(hours=24)).mean()) if pd.notna(rt.loc[i, 'posted']) else np.nan for i, t in zip(rt.index, rt.thread_id)]
rt['op_community'] = rt.op.map(mem['reddit'])
save_table(xt.sort_values('size', ascending=False), '07_x_cascades'); save_table(rt.sort_values('comments', ascending=False), '07_reddit_cascades')
fig, axes = plt.subplots(1, 3, figsize=(15, 4))
for ax, (vals, lab, col) in zip(axes, [(xt['size'], 'X thread size (posts in corpus)', PALETTE['x']), (rt['comments'], 'Reddit thread size (comments)', PALETTE['reddit']), (rt['max_depth'], 'Reddit max depth', PALETTE['reddit'])]):
    v = np.sort(vals.values); ccdf = 1 - np.arange(len(v)) / len(v)
    ax.loglog(v, ccdf, '.', color=col, ms=4); ax.set_xlabel(lab); ax.set_ylabel('P(X ≥ x)')
axes[0].set_title('Cascade size distributions (CCDF)')
savefig('07_cascade_sizes'); plt.show()
summary = pd.DataFrame({'X threads': xt['size'].describe(), 'Reddit threads (comments)': rt['comments'].describe(), 'Reddit max depth': rt['max_depth'].describe(), 'Reddit duration (h)': rt['duration_h'].describe()}).round(2)
save_table(summary.reset_index().rename(columns={'index': 'stat'}), '07_cascade_summary'); summary
"""),
("md", r"""
**What this shows:** X threads in the corpus are almost always single posts (search capture does not return reply chains), so X diffusion is better read through quotes and mentions of a few hub accounts. Reddit threads are heavy-tailed: a handful of megathreads hold hundreds of comments, most of them within the first day, with reply depth that shows real back-and-forth.
"""),
("md", r"""
## 3. Content that travelled: links, domains and hashtags across communities
"""),
("code", r"""
def explode_field(df, col):
    e = df.assign(v=df[col].str.split(',')).explode('v'); e = e[e.v.notna() & (e.v != '')]; return e
dom = explode_field(items, 'domains'); dom = dom[~dom.v.isin(['x.com', 'twitter.com', 't.co', 'reddit.com', 'redd.it', 'i.redd.it', 'v.redd.it', 'preview.redd.it'])]
spread = dom.groupby('v').agg(items=('post_id', 'size'), platforms=('platform', 'nunique'), x_items=('platform', lambda s: (s == 'x').sum()), reddit_items=('platform', lambda s: (s == 'reddit').sum()),
                              communities=('community', lambda s: s.dropna().nunique()), first_seen=('timestamp', 'min'),
                              pro_share=('stance', lambda s: round((s == 'PRO').mean(), 2)), anti_share=('stance', lambda s: round((s == 'ANTI').mean(), 2))).reset_index().rename(columns={'v': 'domain'})
spread = spread.sort_values('items', ascending=False)
save_table(spread, '07_domain_spread')
ht = explode_field(items[items.platform == 'x'], 'hashtags')
first_use = ht.groupby('v').timestamp.min()
lag = ht.dropna(subset=['community']).groupby(['v', 'community']).timestamp.min().reset_index()
lag['lag_h'] = (lag.timestamp - lag.v.map(first_use)).dt.total_seconds() / 3600
top_tags = ht.v.value_counts().head(15).index
tag_tab = ht[ht.v.isin(top_tags)].groupby('v').agg(posts=('post_id', 'size'), communities=('community', lambda s: s.dropna().nunique()), first_seen=('timestamp', 'min'),
                                                   pro_share=('stance', lambda s: round((s == 'PRO').mean(), 2)), anti_share=('stance', lambda s: round((s == 'ANTI').mean(), 2)),
                                                   median_adoption_lag_h=('v', lambda s: round(lag[lag.v == s.iloc[0]].lag_h.median(), 1))).reset_index().rename(columns={'v': 'hashtag'}).sort_values('posts', ascending=False)
save_table(tag_tab, '07_hashtag_adoption')
display(spread.head(15)); tag_tab
"""),
("md", r"""
**What this shows:** mainstream news domains are shared across many communities and both platforms (bridging content), while partisan outlets and the anti-CJP hashtags (#IndiaRejectsCJP, #CongAAPkeCockroach) stay inside the ANTI communities. Pro-protest hashtags are adopted by other communities within hours; counter-hashtags spread more slowly and less widely.
"""),
("md", r"""
## 4. Cross-platform diffusion: X posts shared on Reddit
"""),
("code", r"""
rr_ = items[items.platform == 'reddit']; xlinks = rr_[rr_.urls.str.contains(r'(?:x\.com|twitter\.com)/\w+/status/\d+', regex=True)].copy()
xlinks['x_status_id'] = xlinks.urls.str.extract(r'(?:x\.com|twitter\.com)/\w+/status/(\d+)')[0]
xlinks['x_handle'] = xlinks.urls.str.extract(r'(?:x\.com|twitter\.com)/(\w+)/status/')[0].str.lower().replace({'i': 'unknown (x.com/i/ link)'})
xlinks['in_x_corpus'] = xlinks.x_status_id.isin(set(x.post_id))
xlinks['x_handle_stance'] = xlinks.x_handle.map(ustance['x']).fillna('not in X corpus')
xa = pd.read_csv(X_PROC / 'x_authors.csv'); xlinks['x_handle_type'] = xlinks.x_handle.map(dict(zip(xa.author, xa.account_type))).fillna('not in X corpus')
cp = xlinks.groupby('x_handle').agg(reddit_items=('post_id', 'size'), subreddits=('subreddit', 'nunique'), x_type=('x_handle_type', 'first'), x_stance=('x_handle_stance', 'first'), reddit_pro=('stance', lambda s: (s == 'PRO').sum()), reddit_anti=('stance', lambda s: (s == 'ANTI').sum())).sort_values('reddit_items', ascending=False).reset_index()
save_table(cp, '07_cross_platform_x_handles'); save_table(xlinks[['post_id', 'thread_id', 'author', 'timestamp', 'subreddit', 'x_handle', 'x_status_id', 'in_x_corpus', 'stance']], '07_cross_platform_links')
print(f"Reddit items linking to X posts: {len(xlinks)} ({pct(len(xlinks), len(r))}% of Reddit items); X posts found in our X corpus: {int(xlinks.in_x_corpus.sum())}; distinct X handles: {xlinks.x_handle.nunique()}")
cp.head(15)
"""),
("md", r"""
**What this shows:** Reddit imports X content mainly from the CJP accounts, news handles and the anti-CJP aggregator accounts (MeghUpdates-type); the direction of flow is X → Reddit (screenshots and links), with no measurable flow back. The handles whose posts are imported are themselves the hubs of the X network.
"""),
("md", r"""
## 5. Cross-community interaction over time
Share of interactions whose source and target lie in different communities, per week, and who initiates them (by stance of the source).
"""),
("code", r"""
flows = []
for p, e in [('x', ex), ('reddit', er)]:
    e = e.copy(); e['sc'] = e.source.map(mem[p]); e['tc'] = e.target.map(mem[p]); e = e.dropna(subset=['sc', 'tc'])
    e['cross'] = e.sc != e.tc; e['week'] = e.timestamp.dt.to_period('W').dt.start_time
    e['src_stance'] = e.source.map(ustance[p]).fillna('NEUTRAL'); e['tgt_stance'] = e.target.map(ustance[p]).fillna('NEUTRAL')
    e['platform'] = p; flows.append(e)
flows = pd.concat(flows)
wk = flows.groupby(['platform', 'week']).agg(interactions=('cross', 'size'), cross_share=('cross', 'mean')).reset_index()
save_table(wk, '07_weekly_cross_community_share')
fig, axes = plt.subplots(1, 2, figsize=(13, 4))
for ax, p in zip(axes, ['x', 'reddit']):
    w = wk[wk.platform == p]; ax.bar(w.week, w.interactions, width=5, color=PALETTE[p], alpha=0.35, label='interactions'); ax2 = ax.twinx(); ax2.plot(w.week, 100 * w.cross_share, 'o-', color='#222', label='% cross-community'); ax2.set_ylim(0, 100); ax2.set_ylabel('% cross-community'); ax.set_title(f'{p}: weekly interactions and share across communities'); ax2.grid(False)
savefig('07_weekly_cross_community'); plt.show()
init = flows[flows.cross].groupby(['platform', 'src_stance', 'tgt_stance']).size().unstack(fill_value=0)
save_table(init.reset_index(), '07_cross_community_initiators'); init
"""),
("md", r"""
**What this shows:** cross-community interaction is a minority of all interactions on both platforms, but it is not constant: it rises in the weeks of confrontation (20 June, 18–25 July) when ANTI users address PRO hubs and PRO users address police and government accounts. Notebook 08 tests whether these levels are lower than chance and whether the cross-community contacts are agreements or attacks.
"""),
]
