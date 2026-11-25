FILENAME = "02_Data_Cleaning_Preprocessing"
TITLE = "02 - Data Cleaning & Preprocessing"

CELLS = [
("md", r"""
# 02 · Data Cleaning & Preprocessing

Turns the raw X exports and the raw Reddit archive files into two clean tables with **one shared schema**
(`platform, post_id, thread_id, parent_id, timestamp, author, text, …`) so that every later notebook can treat both platforms the same way.
Steps: window filter → relevance filter → de-duplication → standardised fields → author tables.
"""),
("code", r"""
import sys; sys.path.insert(0, '.')
from csma_lib import *
setup_plots()
"""),
("md", r"""
## 1. X — audit of the master dataset

The X master was produced by the team's `Preprocessing.ipynb` (window 1 Jun–31 Jul 2026, topic-relevance rules, cross-file de-duplication).
The audit below re-reads the raw exports so the funnel can be checked, then loads the master.
"""),
("code", r"""
log = pd.read_csv(X_PROC / 'preprocessing_log.csv', encoding='utf-8-sig')
funnel = log.groupby('group')[['raw_rows', 'outside_study_window', 'off_topic_or_generic_excluded', 'duplicate_ids_removed_within_file', 'relevant_rows_kept']].sum()
funnel.loc['total'] = funnel.sum()
save_table(funnel.reset_index(), '02_x_preprocessing_funnel')
x = load_x_master()
print(f"master: {len(x)} unique posts, {x.author.nunique()} authors, {x.timestamp.min()} → {x.timestamp.max()}")
print("posts that matched more than one keyword group:", int(x['groups'].str.contains('|', regex=False).sum()),
      "(the team's earlier network used the 1,823-row version in which these posts were counted once per group)")
funnel
"""),
("md", r"""
**What this shows:** 3,840 raw rows → 1,891 relevant in-window rows → **1,727 unique posts** (164 posts were found by more than one keyword group).
"""),
("code", r"""
# Unified X table
def split_list(s):
    return [t for t in re.split(r'[;,\s]+', str(s).strip().lower()) if t]
def domains_of(urls):
    out = []
    for u in urls:
        m = re.match(r'https?://([^/]+)', u)
        if m: out.append(m.group(1).lower().replace('www.', ''))
    return out
x['mentions_list'] = x['mentions'].map(split_list)
x['hashtags_list'] = x['hashtags'].map(split_list)
x['urls_list'] = x['urls'].map(lambda s: [u for u in re.split(r'[;,\s]+', str(s)) if u.startswith('http')])
x['domains_list'] = x['urls_list'].map(domains_of)
x['script'] = x['text'].map(script_of)
x['themes_list'] = (x['text'] + ' ' + x['hashtags'] + ' ' + x['quote_body'].map(clean_text)).map(themes_of)
x_u = pd.DataFrame({
    'platform': 'x', 'post_id': x['id'], 'thread_id': x['thread_id'], 'parent_id': '',
    'timestamp': x['timestamp'], 'author': x['author'], 'author_id': x['author_id'], 'author_name': x['author_fullname'],
    'author_followers': x['author_followers'], 'verified': x['verified'], 'subreddit': '',
    'text': x['text'], 'lang': x['language_guess'], 'script': x['script'],
    'item_type': np.where(x['is_reply'], 'reply', np.where(x['is_quote_tweet'], 'quote', 'post')),
    'is_reply': x['is_reply'], 'reply_to_author': x['replied_author'].str.lower().str.lstrip('@'),
    'is_quote': x['is_quote_tweet'], 'quote_author': x['quote_author'].str.lower().str.lstrip('@'), 'quote_text': x['quote_body'].map(clean_text),
    'mentions': x['mentions_list'].map(','.join), 'hashtags': x['hashtags_list'].map(','.join),
    'urls': x['urls_list'].map(' '.join), 'domains': x['domains_list'].map(','.join),
    'likes': x['like_count'], 'replies': x['reply_count'], 'reposts': x['retweet_count'], 'quotes': x['quote_count'], 'impressions': x['impression_count'],
    'groups': x['groups'], 'themes': x['themes_list'].map(','.join), 'removed': False,
})
x_u = x_u[(x_u.timestamp >= WINDOW_START) & (x_u.timestamp <= WINDOW_END)].sort_values('timestamp').reset_index(drop=True)
x_u.to_csv(X_PROC / 'x_posts_unified.csv', index=False)
print(x_u.shape, '→', (X_PROC / 'x_posts_unified.csv').relative_to(ROOT))
x_u[['post_id', 'timestamp', 'author', 'item_type', 'script', 'groups', 'themes']].head()
"""),
("md", r"""
## 2. X — author table and account type

Account type is a *factor* used later to characterise communities. It is assigned from a short list of known handles (CJP organisation, police/government, politicians, AI assistant) and from the display name and bio
(news media outlets and journalists, office holders, public figures, citizens whose bio declares a party or ideology = `partisan_citizen`), everything else is `citizen_other`.
"""),
("code", r"""
KNOWN = {
 'cjp_org': ['cockroachisback', 'abhijeet_dipke', 'cjp_2029', 'cjp_for_india', 'sauravdassss', 'ashutoshranka', 'cjp_is_back', 'cjp_united', 'vijetadahiya'],
 'police_gov': ['delhipolice', 'dcpnewdelhi', 'cpdelhi', 'pmoindia', 'hmoindia', 'eduminofindia', 'mygovindia', 'dpradhanbjp', 'jpnadda', 'narendramodi', 'amitshah', 'kirenrijiju', 'meaindia', 'nta_exams', 'ddnewslive', 'ddnational'],
 'politician_party': ['rahulgandhi', 'arvindkejriwal', 'msisodia', 'asadowaisi', 'mahuamoitra', 'udhaystalin', 'saketgokhale', 'aamaadmiparty', 'incindia', 'bjp4india', 'cpimspeak', 'tejyadav14', 'sanjayazadsln', 'kharge', 'yadavakhilesh', 'mamataofficial', 'priyankagandhi', 'officeofut', 'shashitharoor', 'derekobrienmp', 'anishgawande', 'nsui', 'abvpvoice', 'aisa_official_', 'sfi_cec', 'iyc', 'pbhushan1', '_yogendrayadav', 'wangchuk66', 'jairam_ramesh', 'supriya_sule', 'tejashwiyadav', 'dmkitwing', 'ncpspeaks', 'sitaramyechury'],
 'ai_bot': ['grok'],
}
MEDIA_RE = re.compile(r'\bnews\b|journalist|editor|reporter|correspondent|anchor|\btv\b|times of india|hindustan times|indian express|the hindu|ndtv|\bdna\b|\bpti\b|\bani\b|\bbbc\b|\bcnn\b|zee|aaj ?tak|lallantop|newslaundry|the wire|theprint|the print|quint|scroll\.in|livemint|\bmint\b|opindia|swarajya|republic|jagran|bhaskar|amar ?ujala|india today|firstpost|\bians\b|tribune|telegraph|outlook|bureau|broadcast|channel|network|media house|publication|magazine|\bdaily\b|समाचार|न्यूज़|पत्रकार', re.I)
OFFICE_RE = re.compile(r'\b(?:mp|mla|mlc|minister|spokesperson|national (?:secretary|president|convenor)|state president|general secretary|councillor|former (?:mp|mla|minister)|official (?:account|handle) of|party)\b|सांसद|विधायक|मंत्री|प्रवक्ता', re.I)
FIGURE_RE = re.compile(r'activist|lawyer|advocate|professor|academic|author|writer|founder|influencer|youtuber|creator|comedian|actor|film|analyst|columnist|psephologist|speaker|poet|singer|artist', re.I)
PARTISAN_RE = re.compile(r'\bbjp\b|congress|\baap\b|modi|sanghi|hindutva|nationalist|bhakt|liberal|leftist|commie|samajwadi|\btmc\b|\brss\b|proud hindu|sanatan|secular|ambedkarite|jai bhim|anti-?national|right wing|left wing', re.I)
def account_type(handle, name, bio):
    for t, hs in KNOWN.items():
        if handle in hs: return t
    text = f"{name} {bio}"
    if MEDIA_RE.search(str(name)) or MEDIA_RE.search(str(bio)): return 'news_media'
    if OFFICE_RE.search(str(bio)): return 'politician_party'
    if FIGURE_RE.search(str(bio)): return 'public_figure'
    if PARTISAN_RE.search(text): return 'partisan_citizen'
    return 'citizen_other'
auth = x.groupby('author').agg(author_name=('author_fullname', 'first'), bio=('author_bio', 'first'), followers=('author_followers', 'max'),
                               verified=('verified', 'max'), n_posts=('id', 'size'), first_post=('timestamp', 'min'), groups=('groups', lambda s: '|'.join(sorted(set('|'.join(s).split('|')))))).reset_index()
auth['account_type'] = [account_type(h, n, b) for h, n, b in zip(auth.author, auth.author_name, auth.bio)]
auth.to_csv(X_PROC / 'x_authors.csv', index=False)
save_table(auth.account_type.value_counts().rename_axis('account_type').reset_index(name='authors'), '02_x_account_types')
auth.account_type.value_counts()
"""),
("md", r"""
## 3. Reddit — load raw archive files

Submissions (keyword search, tagged with the matching query groups), full comment threads (Arctic Shift + PullPush) and keyword-matched comments.
"""),
("code", r"""
subs = {d['id']: d for d in jsonl_iter(R_RAW / 'submissions.jsonl')}
qindex = json.load(open(R_RAW / 'submission_queries.json'))
comments = {}
for fname in ['comments_threads_as.jsonl', 'comments_threads.jsonl', 'comments_keyword.jsonl']:
    p = R_RAW / fname
    if p.exists():
        n0 = len(comments)
        for c in jsonl_iter(p):
            if c['id'] not in comments:
                c['_from'] = fname; comments[c['id']] = c
            elif fname == 'comments_keyword.jsonl':
                comments[c['id']].setdefault('_matched_term', c.get('_matched_term'))
        print(f"{fname:28s} +{len(comments)-n0:6d} new comments")
print(f"submissions: {len(subs)}   comments: {len(comments)}")
"""),
("md", r"""
## 4. Reddit — window, relevance and de-duplication

Same logic as for X: keep items inside the window, keep submissions that (a) mention a core term (CJP / Dipke / Jantar Mantar / Pradhan / Wangchuk …),
(b) were posted in a CJP subreddit, or (c) combine at least two context signals (exam + protest + police …); everything else is set aside with its reason.
Comments of a relevant submission are kept as part of that thread. Deleted/removed authors stay in the text corpus but cannot be network nodes.
"""),
("code", r"""
BOT_RE = re.compile(r'automoderator|bot$|_bot|-bot|^\[deleted\]$|^\[removed\]$', re.I)
def rel_reason(d):
    text = f"{d.get('title','')} {d.get('selftext','')}"
    if re.search(r'cjp|cockroach', d.get('subreddit', ''), re.I): return 'cjp_subreddit'
    if CORE_RE.search(text): return 'core_term'
    sig = set(m.group(0).lower() for m in CONTEXT_RE.finditer(text))
    if len(sig) >= 2 and re.search(r'india|delhi|neet|pradhan|protest', text, re.I): return 'context_terms'
    return ''
rows, excluded = [], []
for pid, d in subs.items():
    ts = pd.Timestamp(d['created_utc'], unit='s')
    reason = rel_reason(d)
    if not (WINDOW_START <= ts <= WINDOW_END): excluded.append({'post_id': pid, 'reason': 'outside_window'}); continue
    if not reason: excluded.append({'post_id': pid, 'reason': 'generic_or_off_topic', 'title': d.get('title', '')[:120], 'subreddit': d.get('subreddit')}); continue
    rows.append((pid, d, reason, ts))
rel_ids = {r[0] for r in rows}
groups_of = {pid: '|'.join(sorted({q.split('|')[0] for q in qindex.get(pid, [])})) for pid in subs}
print(f"submissions in window & relevant: {len(rows)}  | excluded: {pd.Series([e['reason'] for e in excluded]).value_counts().to_dict()}")
pd.DataFrame(excluded).to_csv(R_PROC / 'reddit_excluded_submissions.csv', index=False)
"""),
("code", r"""
# Build the unified Reddit table (submissions + comments of relevant threads + keyword comments)
def text_urls(t):
    return re.findall(r'https?://[^\s\)\]]+', str(t))
def domains_of(urls):
    out = []
    for u in urls:
        m = re.match(r'https?://([^/]+)', u)
        if m: out.append(m.group(1).lower().replace('www.', ''))
    return out
rec = []
sub_author = {}
for pid, d, reason, ts in rows:
    urls = ([d['url']] if d.get('url') and not d.get('is_self') and 'reddit.com' not in d.get('url', '') else []) + text_urls(d.get('selftext', ''))
    text = clean_text(f"{d.get('title','')}. {d.get('selftext','')}" if d.get('selftext') and d['selftext'] not in ('[removed]', '[deleted]') else d.get('title', ''))
    author = str(d.get('author', '')).lower()
    sub_author[pid] = author
    rec.append({'platform': 'reddit', 'post_id': pid, 'thread_id': pid, 'parent_id': '', 'timestamp': ts, 'author': author, 'author_id': d.get('author_fullname') or '',
                'author_name': '', 'author_followers': 0, 'verified': False, 'subreddit': d.get('subreddit', ''), 'text': text, 'lang': '', 'script': script_of(text),
                'item_type': 'submission', 'is_reply': False, 'reply_to_author': '', 'is_quote': False, 'quote_author': '', 'quote_text': '',
                'mentions': '', 'hashtags': '', 'urls': ' '.join(urls), 'domains': ','.join(domains_of(urls)),
                'likes': d.get('score') or 0, 'replies': d.get('num_comments') or 0, 'reposts': d.get('num_crossposts') or 0, 'quotes': 0, 'impressions': 0,
                'groups': groups_of.get(pid, ''), 'themes': ','.join(themes_of(text)), 'removed': bool(d.get('removed_by_category')) or d.get('selftext') in ('[removed]', '[deleted]'),
                'relevance_reason': reason, 'upvote_ratio': d.get('upvote_ratio'), 'flair': d.get('link_flair_text') or ''})
c_author = {cid: str(c.get('author', '')).lower() for cid, c in comments.items()}
n_out = 0
for cid, c in comments.items():
    tid = str(c.get('link_id', '')).replace('t3_', '')
    in_corpus = tid in rel_ids
    if not in_corpus and not c.get('_matched_term'): continue
    ts = pd.Timestamp(c['created_utc'], unit='s')
    if not (WINDOW_START <= ts <= WINDOW_END): n_out += 1; continue
    par = str(c.get('parent_id', ''))
    if par.startswith('t1_'):
        parent_id = par[3:]; parent_author = c_author.get(parent_id, '')
    else:
        parent_id = par[3:] if par.startswith('t3_') else ''; parent_author = sub_author.get(parent_id, '') if in_corpus else (subs.get(parent_id, {}).get('author', '') or '').lower()
    body = c.get('body', '')
    text = clean_text(body)
    urls = text_urls(body)
    rec.append({'platform': 'reddit', 'post_id': cid, 'thread_id': tid, 'parent_id': parent_id, 'timestamp': ts, 'author': c_author[cid], 'author_id': c.get('author_fullname') or '',
                'author_name': '', 'author_followers': 0, 'verified': False, 'subreddit': c.get('subreddit', ''), 'text': text, 'lang': '', 'script': script_of(text),
                'item_type': 'comment', 'is_reply': True, 'reply_to_author': parent_author, 'is_quote': False, 'quote_author': '', 'quote_text': '',
                'mentions': '', 'hashtags': '', 'urls': ' '.join(urls), 'domains': ','.join(domains_of(urls)),
                'likes': c.get('score') or 0, 'replies': 0, 'reposts': 0, 'quotes': 0, 'impressions': 0,
                'groups': groups_of.get(tid, '') if in_corpus else 'K', 'themes': ','.join(themes_of(text)), 'removed': body in ('[removed]', '[deleted]'),
                'relevance_reason': 'thread_in_corpus' if in_corpus else 'keyword_comment', 'upvote_ratio': None, 'flair': ''})
r_u = pd.DataFrame(rec).drop_duplicates('post_id').sort_values('timestamp').reset_index(drop=True)
r_u['is_bot'] = r_u['author'].str.contains(BOT_RE)
r_u['anonymous'] = r_u['author'].isin(['[deleted]', '[removed]', ''])
r_u.to_csv(R_PROC / 'reddit_items_unified.csv', index=False)
print(f"comments outside window dropped: {n_out}")
print(r_u.item_type.value_counts().to_dict(), '| bots:', int(r_u.is_bot.sum()), '| anonymous authors:', int(r_u.anonymous.sum()), '| removed text:', int(r_u.removed.sum()))
print('→', (R_PROC / 'reddit_items_unified.csv').relative_to(ROOT))
"""),
("code", r"""
# Reddit funnel + per-group counts, and the Reddit author table
r_funnel = pd.DataFrame([
    {'step': 'submissions matched by any query', 'count': len(subs)},
    {'step': 'outside window', 'count': sum(e['reason'] == 'outside_window' for e in excluded)},
    {'step': 'generic / off-topic (excluded)', 'count': sum(e['reason'] == 'generic_or_off_topic' for e in excluded)},
    {'step': 'relevant submissions kept', 'count': len(rows)},
    {'step': 'comments in relevant threads (in window)', 'count': int((r_u.relevance_reason == 'thread_in_corpus').sum())},
    {'step': 'keyword comments in other threads (in window)', 'count': int((r_u.relevance_reason == 'keyword_comment').sum())},
    {'step': 'unique Reddit authors (non-bot, non-deleted)', 'count': int(r_u.loc[~r_u.is_bot & ~r_u.anonymous, 'author'].nunique())},
])
save_table(r_funnel, '02_reddit_preprocessing_funnel')
rel_sub = r_u[r_u.item_type == 'submission']
save_table(rel_sub.relevance_reason.value_counts().rename_axis('relevance_reason').reset_index(name='submissions'), '02_reddit_relevance_reasons')
ra = r_u[~r_u.is_bot & ~r_u.anonymous].groupby('author').agg(n_items=('post_id', 'size'), n_submissions=('item_type', lambda s: (s == 'submission').sum()),
        n_comments=('item_type', lambda s: (s == 'comment').sum()), subreddits=('subreddit', lambda s: ','.join(sorted(set(s))[:6])), score_sum=('likes', 'sum'),
        first_item=('timestamp', 'min')).reset_index()
ra['account_type'] = np.where(ra.author.str.contains(r'news|media|times|journal|press', regex=True), 'news_media', 'citizen_other')
ra.to_csv(R_PROC / 'reddit_authors.csv', index=False)
display(r_funnel)
"""),
("code", r"""
# Side-by-side description of both clean tables
both = pd.concat([x_u.assign(platform='x'), r_u], ignore_index=True)
desc = both.groupby('platform').agg(items=('post_id', 'size'), authors=('author', 'nunique'), threads=('thread_id', 'nunique'),
                                    first=('timestamp', 'min'), last=('timestamp', 'max'),
                                    replies=('is_reply', 'sum'), with_urls=('urls', lambda s: (s != '').sum()),
                                    devanagari_or_mixed=('script', lambda s: s.isin(['devanagari', 'mixed']).sum())).reset_index()
save_table(desc, '02_platform_overview')
gcount = pd.concat([x_u.assign(platform='x'), r_u[r_u.item_type == 'submission']]).assign(g=lambda d: d.groups.str.split('|')).explode('g')
gc = pd.crosstab(gcount.g.replace('', 'none'), gcount.platform).rename_axis('keyword_group').reset_index()
save_table(gc, '02_keyword_group_counts')
display(desc); gc
"""),
("md", r"""
**What this shows:** both platforms now sit in one schema. X contributes original posts (few threads with more than one author), Reddit contributes whole conversation threads, which is why the Reddit reply column is much larger. Keyword groups A/B/C/D are kept on both platforms so later comparisons can be made group by group.
"""),
]
