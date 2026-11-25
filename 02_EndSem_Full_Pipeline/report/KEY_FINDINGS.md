# Key findings — CJP / Jantar Mantar protests on X and Reddit (1 Jun – 31 Jul 2026)

Generated from the final notebook outputs (19 Oct 2026). Use with the figures listed at the end.

## 1. Data
- X: 1,727 posts, 651 accounts (Zeeschuimer capture, groups A–C).
- Reddit: 172,910 submissions + comments, 49,478 users (PullPush + Arctic Shift archives, groups A–D + CJP subreddits), still being extended by the collectors.

## 2. Networks and communities
- X network: 466 nodes, 600 edges, reciprocity 0.037; midsem network (466/600) reproduced exactly.
- Reddit network: 42,976 nodes, 103,670 edges, reciprocity 0.31.
- Louvain: X 21 (14) communities (modularity 0.62, seed-stability NMI 0.91); Reddit 79 (15) (modularity 0.67, NMI 0.73). Numbers in brackets = communities characterised.
- Cross-community edge share vs degree-preserving null: X 0.27 (z = -47), Reddit 0.41 (z = -981) → communities are real enclosures on both platforms.

## 3. Stance classification
- 883 hand-labelled items (376 X, 507 Reddit). X model macro-F1 0.72; Reddit model 0.52; keyword baseline ≈ 0.45. Reddit class shares calibrated to the random labelled sample.
- Items PRO / NEUTRAL / ANTI: X 21 / 45 / 35 %, Reddit 34 / 49 / 18 %. Users: X 20 / 41 / 40 %, Reddit 29 / 62 / 8 %.

## 4. The five X communities that matter most
- C1 (57 accounts): Pro-protest · media coverage; PRO 49% / ANTI 17% / NEU 34%; hubs: cockroachisback, wangchuk66, sauravdassss.
- C2 (53 accounts): Anti-CJP / pro-government · minister accountability; PRO 27% / ANTI 44% / NEU 29%; hubs: abhijeet_dipke, newsarenaindia, elvishyadav.
- C3 (37 accounts): Mixed / contested · opposition politics; PRO 30% / ANTI 38% / NEU 32%; hubs: ani, arvindkejriwal, aamaadmiparty.
- C4 (35 accounts): Anti-CJP / pro-government · police repression; PRO 10% / ANTI 57% / NEU 32%; hubs: delhipolice, narendramodi, cpdelhi.
- C5 (24 accounts): Mixed / contested · conspiracy funding; PRO 9% / ANTI 24% / NEU 67%; hubs: ians_india, ddnewslive, dtptraffic.

## 5. Cross-community interaction and polarization
- X: 43% of PRO–ANTI interactions cross sides; hostile 16% (opposite sides) vs 9% (same side); reciprocity of cross-side contact 0.00; stance E–I -0.13, RWC 0.36; bridge users 31.
- REDDIT: 3% of PRO–ANTI interactions cross sides; hostile 21% (opposite sides) vs 22% (same side); reciprocity of cross-side contact 0.24; stance E–I -0.94, RWC 0.64; bridge users 2891.
- Verdict X: **polarization: separated camps with mostly non-hostile, one-directional cross-community contact**.
- Verdict Reddit: **mixed: structurally separated communities with some genuine cross-community engagement**.

## 6. Information flow
- Shared sources that travel across communities and platforms: youtube.com, instagram.com, timesofindia.indiatimes.com, youtu.be, thehindu.com, indianexpress.com.
- X → Reddit: 427 Reddit items link to X posts; most-imported handles: unknown (x.com/i/ link), savantvirtuoso, dcpnewdelhi, cockroachisback, ani.
- Top X bridge accounts: cockroachisback, sauravdassss, abhijeet_dipke, delhipolice, grok, cjpcomms (participation coefficient + betweenness).

## 7. Figures to show
- `outputs/figures/03_daily_volume.png` — daily volume with protest events
- `outputs/figures/05_x_communities.png` — X communities
- `outputs/figures/05_reddit_communities.png` — Reddit communities (2-core)
- `outputs/figures/06_community_stance.png` — stance per community
- `outputs/figures/06_theme_heatmap.png` — themes per community
- `outputs/figures/07_weekly_cross_community.png` — weekly cross-community share
- `outputs/figures/08_mixing_matrices.png` — who talks to whom by stance
- `outputs/figures/08_null_model.png` — cross-community share vs null
- `outputs/figures/08_bridges_scatter.png` — bridge users
- `outputs/figures/08_x_network_by_stance.png` — X network by stance
- `outputs/figures/09_summary.png` — summary panel

## 8. Limitations to state
- X capture returns original posts far more than reply chains (thin X network); Reddit archives miss quickly removed posts; stance is model-predicted (community shares more reliable than individual labels); hostility is a lexicon + model indicator; Group D returned too few X posts (covered on Reddit only); no demographics.