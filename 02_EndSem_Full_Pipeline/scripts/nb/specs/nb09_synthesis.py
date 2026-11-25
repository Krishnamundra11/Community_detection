FILENAME = "09_Interaction_vs_Polarization"
TITLE = "09 - Interaction vs Polarization: synthesis and X-Reddit comparison"

CELLS = [
("md", r"""
# 09 · Interaction vs Polarization — synthesis and X–Reddit comparison

Brings the results of notebooks 03–08 together: the final community tables, a side-by-side comparison of both platforms, and the answer to the
central question — does cross-community interaction around the CJP–government conflict look like **engagement** or like **polarization**?
"""),
("code", r"""
import sys; sys.path.insert(0, '.')
from csma_lib import *
setup_plots()
P = ['x', 'reddit']
T = lambda name: pd.read_csv(TABLES / f'{name}.csv')
"""),
("md", r"""
## 1. Final community tables
One row per major community: size, main theme, stance distribution, key characteristics and the assigned label (format of the planned output table).
"""),
("code", r"""
final = {}
for p in P:
    prof = T(f'06_{p}_community_profile'); summ = T(f'05_{p}_community_summary')
    t = prof.merge(summ[['community', 'density', 'internal_edges']], on='community', how='left')
    t['stance_summary'] = t.apply(lambda r: f"PRO {r['stance_PRO_%']:.0f}% / NEU {r['stance_NEUTRAL_%']:.0f}% / ANTI {r['stance_ANTI_%']:.0f}%", axis=1)
    out = t[['community', 'users', 'items', 'main_theme', 'stance_summary', 'hostile_%', 'top_hubs', 'composition', 'top_hashtags_or_subreddits', 'shared_sources', 'top_terms', 'label']]
    out = out.rename(columns={'community': 'Community', 'users': '# Users', 'items': '# Items', 'main_theme': 'Main theme', 'stance_summary': 'Stance of items', 'hostile_%': 'Hostile %', 'top_hubs': 'Key accounts', 'composition': 'Composition', 'top_hashtags_or_subreddits': 'Hashtags / subreddits', 'shared_sources': 'Shared sources', 'top_terms': 'Distinctive terms', 'label': 'Label'})
    final[p] = out; save_table(out, f'09_{p}_final_community_table')
    with pd.ExcelWriter(TABLES / f'09_{p}_final_community_table.xlsx') as xw: out.to_excel(xw, index=False, sheet_name='communities')
pd.set_option('display.max_colwidth', 70)
display(final['x'][['Community', '# Users', '# Items', 'Main theme', 'Stance of items', 'Key accounts', 'Label']])
final['reddit'][['Community', '# Users', '# Items', 'Main theme', 'Stance of items', 'Hashtags / subreddits', 'Label']]
"""),
("md", r"""
## 2. X versus Reddit — one comparison table
"""),
("code", r"""
ns = T('04_network_summary'); ns = ns[ns.network.str.startswith(('X (this study', 'Reddit'))].set_index('network')
pol = T('08_polarization_metrics'); rob = T('05_robustness'); qual = T('08_cross_stance_quality'); ov = T('02_platform_overview').set_index('platform')
def polv(p, key):
    s = pol[(pol.platform == p) & pol.metric.str.startswith(key)]; return s.value.iloc[0] if len(s) else np.nan
def polz(p, key):
    s = pol[(pol.platform == p) & pol.metric.str.startswith(key)]; return s.z.iloc[0] if len(s) and 'z' in s else np.nan
def qualv(p, pair, col):
    s = qual[(qual.platform == p) & (qual.pair == pair)]; return s[col].iloc[0] if len(s) else np.nan
us = {p: T(f'06_{p}_user_stance') for p in P}; ps = {p: T(f'06_{p}_post_stance') for p in P}
mix = {p: T(f'08_{p}_stance_mixing_counts').set_index('source_stance \\ target_stance') for p in P}
def cross_stance_share(p):
    m = mix[p].loc[['PRO', 'ANTI'], ['PRO', 'ANTI']].values; return (m[0, 1] + m[1, 0]) / m.sum() if m.sum() else np.nan
rows = []
for p, netname in [('x', ns.index[ns.index.str.startswith('X (this')][0]), ('reddit', ns.index[ns.index.str.startswith('Reddit')][0])]:
    rows.append({
        'platform': p, 'items': int(ov.loc[p, 'items']), 'authors': int(ov.loc[p, 'authors']), 'nodes': int(ns.loc[netname, 'nodes']), 'edges': int(ns.loc[netname, 'edges']),
        'density': ns.loc[netname, 'density'], 'reciprocity': ns.loc[netname, 'reciprocity'], 'largest_wcc_share': ns.loc[netname, 'largest_wcc_share'],
        'communities (major)': f"{len(T(f'05_{p}_community_summary'))} ({int(T(f'05_{p}_community_summary').is_major.sum())})",
        'modularity': polv(p, 'modularity'), 'partition stability (NMI)': rob[(rob.platform == p) & (rob.resolution == 1.0)].mean_pairwise_nmi.iloc[0],
        'cross-community edge share': polv(p, 'share of edges crossing'), 'z vs degree-preserving null': polz(p, 'share of edges crossing'),
        'E-I index (stance, PRO vs ANTI)': polv(p, 'E-I index, stance'), 'stance assortativity': polv(p, 'stance assortativity'), 'RWC (PRO vs ANTI)': polv(p, 'Random-Walk'),
        'items PRO / NEU / ANTI %': ' / '.join(f"{100*v:.0f}" for v in ps[p].stance.value_counts(normalize=True).reindex(['PRO', 'NEUTRAL', 'ANTI']).fillna(0)),
        'users PRO / NEU / ANTI %': ' / '.join(f"{100*v:.0f}" for v in us[p].user_stance.value_counts(normalize=True).reindex(['PRO', 'NEUTRAL', 'ANTI']).fillna(0)),
        'share of PRO-ANTI interactions that cross sides': round(cross_stance_share(p), 3),
        'hostile % same side': round(100 * qualv(p, 'same side', 'hostile_share'), 1), 'hostile % opposite sides': round(100 * qualv(p, 'opposite sides', 'hostile_share'), 1),
        'reciprocity opposite sides': round(qualv(p, 'opposite sides', 'reciprocated'), 3), 'bridge users': int(len(T(f'08_{p}_bridges'))),
    })
comp = pd.DataFrame(rows).set_index('platform').T
save_table(comp.reset_index().rename(columns={'index': 'measure'}), '09_x_vs_reddit_comparison'); comp
"""),
("md", r"""
## 3. Engagement or polarization? — the evidence, criterion by criterion
Each criterion is scored for both platforms; the verdict is the balance of the criteria, not a single number.
"""),
("code", r"""
def score(p):
    c = comp[p]
    rows = [
        ('Communities are structurally closed (cross-community edges far below the degree-preserving null)', c['z vs degree-preserving null'] < -3, f"z = {c['z vs degree-preserving null']}"),
        ('Camps are segregated by stance (stance E-I index below 0 / assortativity above 0.2)', (c['E-I index (stance, PRO vs ANTI)'] < 0) or (c['stance assortativity'] > 0.2), f"E-I = {c['E-I index (stance, PRO vs ANTI)']}, assortativity = {c['stance assortativity']}"),
        ('Random walks stay inside a camp (RWC above 0.2)', c['RWC (PRO vs ANTI)'] > 0.2, f"RWC = {c['RWC (PRO vs ANTI)']}"),
        ('Opposite camps do interact (at least 25 % of PRO/ANTI interactions cross sides)', c['share of PRO-ANTI interactions that cross sides'] >= 0.25, f"{100*c['share of PRO-ANTI interactions that cross sides']:.0f}% cross sides"),
        ('Cross-side contact is hostile (hostility at least twice the same-side rate)', c['hostile % opposite sides'] >= 2 * max(c['hostile % same side'], 1e-9), f"{c['hostile % opposite sides']}% vs {c['hostile % same side']}%"),
        ('Cross-side contact is one-way (reciprocity below 0.1)', c['reciprocity opposite sides'] < 0.1, f"reciprocity = {c['reciprocity opposite sides']}"),
    ]
    return pd.DataFrame(rows, columns=['criterion', 'met', 'evidence']).assign(platform=p)
crit = pd.concat([score(p) for p in P]); save_table(crit, '09_verdict_criteria')
verdicts = {}
for p in P:
    s = crit[crit.platform == p].set_index('criterion').met
    polar = int(s.iloc[0]) + int(s.iloc[1]) + int(s.iloc[2]) + int(s.iloc[4]) + int(s.iloc[5]); engage = int(s.iloc[3]) + int(not s.iloc[4]) + int(not s.iloc[5])
    hostile_flag = bool(s.iloc[4]); oneway_flag = bool(s.iloc[5])
    if polar >= 4:
        verdicts[p] = 'polarization: separated camps' + (' with hostile' if hostile_flag else ' with mostly non-hostile') + (', one-directional' if oneway_flag else ', partly reciprocated') + ' cross-community contact'
    elif engage >= 2 and polar <= 2:
        verdicts[p] = 'cross-community engagement'
    else:
        verdicts[p] = 'mixed: structurally separated communities with some genuine cross-community engagement'
    print(f"{p}: polarization criteria met {polar}/5, engagement criteria met {engage}/3  →  {verdicts[p]}")
save_table(pd.DataFrame([{'platform': p, 'verdict': v} for p, v in verdicts.items()]), '09_verdicts')
crit.pivot(index='criterion', columns='platform', values='evidence')
"""),
("md", r"""
**What this shows:** both platforms show closed communities, but X is polarized along stance — opposite camps rarely meet, and when they do it is mostly ANTI accounts attacking the CJP hubs with hostile, unreciprocated posts. On Reddit, communities are organised by subreddit rather than by stance; PRO and ANTI users share threads and reply to each other, and hostility is more evenly spread, which is closer to cross-community engagement (even if not civil).
"""),
("md", r"""
## 4. Summary figure
"""),
("code", r"""
fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))
metrics = [('modularity', 'modularity'), ('E-I index (stance, PRO vs ANTI)', 'stance E–I index'), ('RWC (PRO vs ANTI)', 'Random-Walk Controversy')]
vals = comp.loc[[m for m, _ in metrics]].astype(float)
vals.T.plot.bar(ax=axes[0], color=['#444', PALETTE['ANTI'], PALETTE['PRO']]); axes[0].set_title('Segregation measures'); axes[0].legend([l for _, l in metrics], fontsize=7); axes[0].set_xlabel('')
h = comp.loc[['hostile % same side', 'hostile % opposite sides']].astype(float); h.T.plot.bar(ax=axes[1], color=['#999', PALETTE['ANTI']]); axes[1].set_title('% hostile interactions'); axes[1].legend(['same side', 'opposite sides'], fontsize=7); axes[1].set_xlabel('')
ust = pd.DataFrame({p: us[p].user_stance.value_counts(normalize=True).reindex(['PRO', 'NEUTRAL', 'ANTI']).fillna(0) * 100 for p in P})
ust.T.plot.bar(ax=axes[2], stacked=True, color=[PALETTE['PRO'], PALETTE['NEUTRAL'], PALETTE['ANTI']]); axes[2].set_title('User stance mix (%)'); axes[2].legend(fontsize=7); axes[2].set_xlabel('')
savefig('09_summary'); plt.show()
"""),
("md", r"""
## 5. Supporting outputs
All tables are in `outputs/tables/` (prefixed by notebook number), figures in `outputs/figures/`, and Gephi files in `outputs/gexf/`:
network graph with communities (05), top keywords/hashtags and subreddits per community (06), top accounts per community (05/06), stance summary per community (06/09), representative posts (06), bridge users (08), diffusion tables (07).

## 6. Limitations
X data come from search-page capture (Zeeschuimer), which returns original posts far more often than reply chains, so the X network is thinner than the real conversation. Reddit archives miss posts removed quickly. Stance is predicted by a classifier trained on 636 hand-labelled items (accuracy and macro-F1 in table 06_classifier_evaluation); community-level percentages are robust to individual errors, individual user labels are not. No demographic information about users is available.
"""),
]
