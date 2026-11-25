FILENAME = "03_Exploratory_Data_Analysis"
TITLE = "03 - Exploratory Data Analysis"

CELLS = [
("md", r"""
# 03 · Exploratory Data Analysis

Volume and engagement of the discussion on both platforms before any network is built: when people posted, in which keyword groups,
in which language, which sources they shared and who the most active accounts were.
"""),
("code", r"""
import sys; sys.path.insert(0, '.')
from csma_lib import *
setup_plots()
x = load_x_unified(); r = load_reddit_unified()
x['is_bot'] = False; x['anonymous'] = False
for c in ['is_bot', 'anonymous', 'is_reply', 'removed']:
    r[c] = r[c].astype(str).str.lower().eq('true')
r = r[~r.is_bot]
both = pd.concat([x, r], ignore_index=True)
print({p: len(d) for p, d in both.groupby('platform')})
"""),
("md", r"""
## 1. Volume over time
Daily items per platform with the main protest events marked.
"""),
("code", r"""
daily = both.groupby([both.timestamp.dt.floor('D'), 'platform']).size().unstack(fill_value=0).reindex(pd.date_range(WINDOW_START.floor('D'), WINDOW_END.floor('D')), fill_value=0)
fig, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
for ax, p, lab in zip(axes, ['x', 'reddit'], ['X posts', 'Reddit submissions + comments']):
    ax.bar(daily.index, daily.get(p, 0), color=PALETTE[p], width=0.8)
    ax.set_ylabel(lab); annotate_events(ax)
axes[0].set_title('Daily volume of the CJP / Jantar Mantar discussion, 1 Jun – 31 Jul 2026')
savefig('03_daily_volume'); plt.show()
save_table(daily.reset_index().rename(columns={'index': 'date'}), '03_daily_volume')
ev = pd.DataFrame([{'event_date': d, 'event': e, **{f'{p}_items_±1day': int(daily.loc[pd.Timestamp(d) - pd.Timedelta(days=1): pd.Timestamp(d) + pd.Timedelta(days=1), p].sum()) for p in daily.columns}} for d, e in EVENTS])
save_table(ev, '03_event_volumes'); ev
"""),
("md", r"""
**What this shows:** both platforms spike on the same days (6 June first protest, 20 June sit-in, 18–25 July removal of Wangchuk, Parliament march and Pradhan's resignation) — the Reddit curve is dominated by the last week of July, X by the first protest.
"""),
("md", r"""
## 2. Keyword groups, item types and language
"""),
("code", r"""
g = both.assign(g=lambda d: d.groups.replace('', 'none').str.split('|')).explode('g')
gc = pd.crosstab(g.g, g.platform)
fig, axes = plt.subplots(1, 3, figsize=(14, 4))
gc.plot.bar(ax=axes[0], color=[PALETTE['reddit'], PALETTE['x']]); axes[0].set_title('items per keyword group (A entity, B exam, C government, D unions, K keyword-comment)'); axes[0].set_xlabel('')
it = pd.crosstab(both.item_type, both.platform); it.plot.bar(ax=axes[1], color=[PALETTE['reddit'], PALETTE['x']]); axes[1].set_title('item types'); axes[1].set_xlabel('')
sc = pd.crosstab(both.platform, both.script, normalize='index') * 100; sc.plot.bar(ax=axes[2], stacked=True); axes[2].set_title('script of the text (%)'); axes[2].set_ylabel('%'); axes[2].set_xlabel('')
savefig('03_groups_types_language'); plt.show()
save_table(gc.reset_index(), '03_keyword_groups'); save_table(sc.round(1).reset_index(), '03_script_mix')
sc.round(1)
"""),
("md", r"""
**What this shows:** X is a mixed Hindi/English space (about one post in five uses Devanagari), Reddit is almost entirely Latin script (English and romanised Hindi). On X most items are original posts; on Reddit most items are comments inside threads.
"""),
("md", r"""
## 3. Engagement
"""),
("code", r"""
fig, axes = plt.subplots(1, 3, figsize=(14, 4))
for ax, col, lab in zip(axes[:2], ['likes', 'reposts'], ['likes', 'reposts']):
    v = x[col].astype(float); ax.hist(np.log10(v + 1), bins=40, color=PALETTE['x']); ax.set_title(f'X: log10({lab}+1)'); ax.set_xlabel(f'log10({lab}+1)')
rs = r[r.item_type == 'submission']
axes[2].hist(np.log10(rs['replies'].astype(float) + 1), bins=40, color=PALETTE['reddit']); axes[2].set_title('Reddit submissions: log10(comments+1)'); axes[2].set_xlabel('log10(comments+1)')
savefig('03_engagement'); plt.show()
eng = pd.DataFrame({
    'X likes': x.likes.astype(float).describe(), 'X reposts': x.reposts.astype(float).describe(), 'X replies': x.replies.astype(float).describe(),
    'Reddit submission score': rs.likes.astype(float).describe(), 'Reddit submission comments': rs.replies.astype(float).describe(),
    'Reddit comment score': r[r.item_type == 'comment'].likes.astype(float).describe()}).round(1)
save_table(eng.reset_index().rename(columns={'index': 'stat'}), '03_engagement_summary'); eng
"""),
("md", r"""
## 4. Hashtags, subreddits and shared sources
"""),
("code", r"""
ht = x.hashtags.str.split(',').explode(); ht = ht[ht != ''].value_counts().head(20)
subs = r.groupby('subreddit').agg(items=('post_id', 'size'), authors=('author', 'nunique')).sort_values('items', ascending=False).head(20)
fig, axes = plt.subplots(1, 2, figsize=(13, 6))
axes[0].barh(ht.index[::-1], ht.values[::-1], color=PALETTE['x']); axes[0].set_title('X: top hashtags')
axes[1].barh(subs.index[::-1], subs['items'][::-1], color=PALETTE['reddit']); axes[1].set_title('Reddit: top subreddits (items)')
savefig('03_hashtags_subreddits'); plt.show()
save_table(ht.rename_axis('hashtag').reset_index(name='posts'), '03_x_top_hashtags'); save_table(subs.reset_index(), '03_reddit_top_subreddits')
"""),
("code", r"""
def top_domains(df, n=15):
    d = df.domains.str.split(',').explode(); d = d[(d != '') & ~d.isin(['x.com', 'twitter.com', 't.co', 'reddit.com', 'redd.it', 'i.redd.it', 'v.redd.it', 'preview.redd.it'])]
    return d.value_counts().head(n)
dx, dr = top_domains(x), top_domains(r)
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
axes[0].barh(dx.index[::-1], dx.values[::-1], color=PALETTE['x']); axes[0].set_title('X: domains shared (excluding x.com)')
axes[1].barh(dr.index[::-1], dr.values[::-1], color=PALETTE['reddit']); axes[1].set_title('Reddit: domains shared (excluding reddit media)')
savefig('03_shared_domains'); plt.show()
save_table(pd.concat([dx.rename('x'), dr.rename('reddit')], axis=1).fillna(0).astype(int).rename_axis('domain').reset_index(), '03_shared_domains')
"""),
("md", r"""
**What this shows:** the same mainstream outlets (The Hindu, Hindustan Times, Indian Express, The Wire, Scroll …) circulate on both platforms; YouTube and Instagram links are the most common non-news sources. This feeds the "shared information sources" criterion of the community characterisation.
"""),
("md", r"""
## 5. Most active accounts
"""),
("code", r"""
xa = pd.read_csv(X_PROC / 'x_authors.csv')
top_x = x.groupby('author').agg(posts=('post_id', 'size'), likes=('likes', lambda s: s.astype(float).sum()), reposts=('reposts', lambda s: s.astype(float).sum())).merge(xa[['author', 'account_type', 'followers']], on='author', how='left')
top_x_posts = top_x.sort_values('posts', ascending=False).head(15); top_x_likes = top_x.sort_values('likes', ascending=False).head(15)
top_r = r[~r.anonymous].groupby('author').agg(items=('post_id', 'size'), score=('likes', lambda s: s.astype(float).sum()), subreddits=('subreddit', 'nunique')).sort_values('items', ascending=False).head(15)
save_table(top_x_posts, '03_x_top_authors_by_posts'); save_table(top_x_likes, '03_x_top_authors_by_likes'); save_table(top_r.reset_index(), '03_reddit_top_authors')
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
axes[0].barh(top_x_posts.author[::-1], top_x_posts.posts[::-1], color=PALETTE['x']); axes[0].set_title('X: most posts')
axes[1].barh(top_x_likes.author[::-1], top_x_likes.likes[::-1], color=PALETTE['x']); axes[1].set_title('X: most likes received')
axes[2].barh(top_r.index[::-1], top_r['items'][::-1], color=PALETTE['reddit']); axes[2].set_title('Reddit: most items')
savefig('03_top_authors'); plt.show()
print(pd.crosstab(top_x.account_type, columns='authors'))
"""),
("md", r"""
**What this shows:** on X the highest-volume posters are news handles and a few partisan accounts (for and against the CJP), while the most-liked posts come from the CJP's own accounts and national politicians; Reddit activity is spread over many ordinary users with no single dominant poster.
"""),
("md", r"""
## 6. Conversation structure before the network
X exports are mostly original posts captured by search (threads rarely contain several authors), whereas Reddit threads contain long reply chains. This asymmetry is what makes the X network sparse and the Reddit network thread-shaped.
"""),
("code", r"""
th_x = x.groupby('thread_id').author.nunique(); th_r = r.groupby('thread_id').author.nunique()
# Reddit comment depth via parent chain
par = dict(zip(r.post_id, r.parent_id)); depth = {}
def dep(i, guard=0):
    if i in depth: return depth[i]
    p = par.get(i, '')
    d = 0 if p == '' else (1 + dep(p, guard + 1) if guard < 200 else 1)
    depth[i] = d; return d
r['depth'] = [dep(i) for i in r.post_id]
summary = pd.DataFrame({
    'X': {'threads': len(th_x), 'threads with 2+ authors': int((th_x >= 2).sum()), 'max authors in a thread': int(th_x.max()), 'median depth': 0},
    'Reddit': {'threads': len(th_r), 'threads with 2+ authors': int((th_r >= 2).sum()), 'max authors in a thread': int(th_r.max()), 'median depth': float(r.loc[r.item_type == 'comment', 'depth'].median())}})
save_table(summary.reset_index().rename(columns={'index': 'measure'}), '03_conversation_structure')
fig, ax = plt.subplots(figsize=(7, 3.5)); r.loc[r.item_type == 'comment', 'depth'].clip(upper=12).value_counts().sort_index().plot.bar(ax=ax, color=PALETTE['reddit']); ax.set_title('Reddit: comment depth (0 = top-level reply to the post)'); ax.set_xlabel('depth')
savefig('03_reddit_comment_depth'); plt.show()
summary
"""),
]
