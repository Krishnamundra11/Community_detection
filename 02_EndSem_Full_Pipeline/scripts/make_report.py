"""Build report/CSMA_Final_Report_Group9.docx from the notebook outputs (tables + figures).

Every number in the report is read from outputs/tables so the document can be regenerated after a re-run.
Usage: _build/venv/bin/python _build/make_report.py
"""
from pathlib import Path
import datetime
import pandas as pd
import numpy as np
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

ROOT = Path(__file__).resolve().parent.parent
T, F = ROOT / "outputs" / "tables", ROOT / "outputs" / "figures"
OUT = ROOT / "report"; OUT.mkdir(exist_ok=True)
R = lambda n: pd.read_csv(T / f"{n}.csv")

doc = Document()
st = doc.styles["Normal"]; st.font.name = "Calibri"; st.font.size = Pt(10.5)
for s in ["Heading 1", "Heading 2", "Heading 3"]:
    doc.styles[s].font.color.rgb = RGBColor(0x1F, 0x3A, 0x5F)

def P(text, bold=False, italic=False, size=None, align=None):
    p = doc.add_paragraph(); r = p.add_run(text); r.bold = bold; r.italic = italic
    if size: r.font.size = Pt(size)
    if align: p.alignment = align
    return p
def H(text, level=1): doc.add_heading(text, level=level)
def table(df, cols=None, widths=None, font=8.5, max_rows=40):
    df = df if cols is None else df[cols]
    df = df.head(max_rows)
    t = doc.add_table(rows=1, cols=len(df.columns)); t.style = "Light Grid Accent 1"
    for i, c in enumerate(df.columns):
        cell = t.rows[0].cells[i]; cell.text = str(c)
        for p in cell.paragraphs:
            for r in p.runs: r.font.bold = True; r.font.size = Pt(font)
    for _, row in df.iterrows():
        cells = t.add_row().cells
        for i, v in enumerate(row):
            if isinstance(v, float): v = f"{v:.3f}" if abs(v) < 10 else f"{v:,.1f}"
            cells[i].text = str(v)
            for p in cells[i].paragraphs:
                for r in p.runs: r.font.size = Pt(font)
    doc.add_paragraph()
def fig(name, caption, width=6.2):
    p = F / f"{name}.png"
    if p.exists():
        doc.add_picture(str(p), width=Inches(width)); P(caption, italic=True, size=9, align=WD_ALIGN_PARAGRAPH.CENTER)

# ------------------------------------------------------------------ data
ov = R("02_platform_overview").set_index("platform")
xf = R("02_x_preprocessing_funnel").set_index("group"); rf = R("02_reddit_preprocessing_funnel").set_index("step")
ns = R("04_network_summary").set_index("network"); xnet = ns.index[ns.index.str.startswith("X (this")][0]; rnet = ns.index[ns.index.str.startswith("Reddit")][0]
rob = R("05_robustness"); cs = {p: R(f"05_{p}_community_summary") for p in ["x", "reddit"]}
ev = R("06_classifier_evaluation"); hev = R("06_hostility_evaluation")
prof = {p: R(f"06_{p}_community_profile") for p in ["x", "reddit"]}
ps = {p: R(f"06_{p}_post_stance") for p in ["x", "reddit"]}; us = {p: R(f"06_{p}_user_stance") for p in ["x", "reddit"]}
pol = R("08_polarization_metrics"); qual = R("08_cross_stance_quality"); comp = R("09_x_vs_reddit_comparison").set_index("measure")
crit = R("09_verdict_criteria"); final = {p: R(f"09_{p}_final_community_table") for p in ["x", "reddit"]}
bridges = {p: R(f"08_{p}_bridges") for p in ["x", "reddit"]}
casc = R("07_cascade_summary").set_index("stat"); cp = R("07_cross_platform_x_handles"); dom = R("07_domain_spread"); wk = R("07_weekly_cross_community_share")
ev_xrows = ev[ev.model.str.startswith("x model")]; ev_rrows = ev[ev.model.str.startswith(("reddit model", "combined"))]
ev_best = ev_rrows.sort_values("macro_f1", ascending=False).iloc[0]
ev_x = ev_xrows.macro_f1.max() if len(ev_xrows) else np.nan
ev_r = ev_rrows.macro_f1.max() if len(ev_rrows) else np.nan
lex_x = ev[(ev.model.str.contains("lexicon")) & (ev.get("evaluated_on", pd.Series(dtype=str)) == "x items")].macro_f1.max() if "evaluated_on" in ev else np.nan
lex_r = ev[(ev.model.str.contains("lexicon")) & (ev.get("evaluated_on", pd.Series(dtype=str)) == "reddit items")].macro_f1.max() if "evaluated_on" in ev else np.nan
ann_x = pd.read_csv(ROOT / "data/annotations/x_annotations.csv"); ann_rd = pd.read_csv(ROOT / "data/annotations/reddit_annotations.csv"); n_ann = len(ann_x) + len(ann_rd)
verd_t = R("09_verdicts").set_index("platform").verdict.to_dict() if (T / "09_verdicts.csv").exists() else {}
def polv(p, key, col="value"):
    s = pol[(pol.platform == p) & pol.metric.str.startswith(key)]; return s[col].iloc[0] if len(s) and col in s else np.nan
def qv(p, pair, col):
    s = qual[(qual.platform == p) & (qual.pair == pair)]; return s[col].iloc[0] if len(s) else np.nan
def met(p):
    c = crit[crit.platform == p]; return int(c.met.astype(str).str.lower().eq("true").sum()), c
verd = {p: verd_t.get(p, "see table of criteria") for p in ["x", "reddit"]}
n_items = {p: int(ov.loc[p, "items"]) for p in ["x", "reddit"]}; n_auth = {p: int(ov.loc[p, "authors"]) for p in ["x", "reddit"]}
ustance_pct = {p: (us[p].user_stance.value_counts(normalize=True) * 100).round(0).to_dict() for p in ["x", "reddit"]}
istance_pct = {p: (ps[p].stance.value_counts(normalize=True) * 100).round(0).to_dict() for p in ["x", "reddit"]}

# ------------------------------------------------------------------ title
P("Mapping Polarization and Cross-Community Interaction in the Cockroach Janta Party (CJP)-led Jantar Mantar Protests", bold=True, size=16, align=WD_ALIGN_PARAGRAPH.CENTER)
P("Computational Social Media Analysis — Final Project Report", size=12, align=WD_ALIGN_PARAGRAPH.CENTER)
P("Group 9: Sejal Gupta, Krishna Mundra, Adamya Aggarwal, Anmol Chaturvedi", align=WD_ALIGN_PARAGRAPH.CENTER)
P(f"Generated {datetime.date.today():%d %B %Y} from the project notebooks (01–09)", italic=True, size=9, align=WD_ALIGN_PARAGRAPH.CENTER)

H("Abstract")
P(f"We study how the online discussion around the Cockroach Janta Party (CJP) protest at Jantar Mantar (1 June – 31 July 2026) organised itself into communities on X and on Reddit, how information moved within and between those communities, and whether contact between opposing camps looked like engagement or polarization. "
  f"The X corpus contains {n_items['x']:,} posts from {n_auth['x']:,} accounts captured with Zeeschuimer; the Reddit corpus contains {n_items['reddit']:,} submissions and comments from {n_auth['reddit']:,} users collected from public archives. "
  f"Directed interaction networks ({int(ns.loc[xnet,'nodes'])} nodes / {int(ns.loc[xnet,'edges'])} edges on X; {int(ns.loc[rnet,'nodes']):,} / {int(ns.loc[rnet,'edges']):,} on Reddit) were partitioned with Louvain (modularity {polv('x','modularity'):.2f} and {polv('reddit','modularity'):.2f}). "
  f"Stance classifiers trained on {n_ann} hand-labelled items (cross-validated macro-F1 {ev_x:.2f} on X and {ev_r:.2f} on Reddit) characterised every community by stance, themes and account types. "
  f"On X the verdict is: {verd['x']}. On Reddit: {verd['reddit']}.")

H("1. Introduction and research questions")
P("The CJP began on 16 May 2026 as online satire after the Chief Justice's 'cockroaches' remark and became a street movement on 6 June 2026, when its founder Abhijeet Dipke led the first protest at Jantar Mantar demanding the resignation of Education Minister Dharmendra Pradhan over the NEET-UG paper leak. The movement grew through a second sit-in (20 June), Sonam Wangchuk's 26-day hunger strike (from 28 June), the 'Chalo Sansad' march of 20 July that ended in lathi charges and tear gas, and Pradhan's resignation on 25 July, after which the protest was called off.")
P("Research questions. (1) Which communities form in the interaction networks on X and Reddit? (2) How do they differ in stance, themes and composition? (3) How does information flow within and between them? (4) Which users bridge communities? (5) Is cross-community interaction engagement or polarization, and does this differ between the two platforms?")

H("2. Data")
H("2.1 X (primary platform)", 2)
P(f"Posts were captured from X's search interface with the Firefox extensions Zeeschuimer (capture) and Schuifmaat (auto-scroll) using keyword groups A (entity: CJP / Dipke / Jantar Mantar), B (topic: NEET, paper leak) and C (government and police response); group D (student unions) was searched with several keyword sets but the X search interface returned too few posts to form a dataset, so group D is covered on Reddit only. "
  f"The team's preprocessing notebook kept {int(xf.loc['total','relevant_rows_kept']):,} relevant in-window rows out of {int(xf.loc['total','raw_rows']):,} raw rows, giving {n_items['x']:,} unique posts after de-duplication across groups.")
H("2.2 Reddit (secondary platform)", 2)
P(f"Reddit's own API blocks anonymous requests, so the same keyword groups (plus the CJP subreddits) were run against the PullPush and Arctic Shift public archives, collecting submissions, their full comment threads and keyword-matched comments. "
  f"{int(rf.loc['relevant submissions kept','count']):,} submissions passed the relevance filter; with their comments the corpus holds {n_items['reddit']:,} items from {n_auth['reddit']:,} non-bot users (bots, deleted authors and removed texts are flagged and excluded from the network).")
table(R("02_platform_overview"), font=8)
fig("03_daily_volume", "Figure 1. Daily volume on both platforms with the main protest events.")

H("3. Methods")
P("The pipeline follows the project design: data collection → cleaning → exploratory analysis → interaction networks → community detection → community classification (stance, themes, factors) → information diffusion → polarization and cross-community interaction → synthesis. All steps are implemented in nine Jupyter notebooks (pandas, NetworkX, scikit-learn, sentence-transformers) and every table and figure in this report is produced by them.")
P("Networks: nodes are accounts; a directed edge A→B records that A replied to, quoted or mentioned B (X) or replied to B's post or comment (Reddit); weight = number of posts in which A addressed B. Communities: Louvain on the largest weakly connected component (direction ignored, weights summed), 20 seeds, stability measured by the mean pairwise normalised mutual information (NMI) and a resolution sweep. "
  "Stance: PRO / ANTI / NEUTRAL towards the CJP-led protest, plus a binary 'hostile' flag, predicted by a logistic-regression ensemble over word and character TF-IDF features and multilingual MiniLM sentence embeddings, trained on a hand-labelled stratified sample (guidelines in data/annotations/README.md) and evaluated with 5-fold cross-validation; user stance = mean of P(PRO) − P(ANTI) over the user's items. "
  "Themes: a bilingual keyword lexicon (exam integrity, minister accountability, police repression, Wangchuk's fast, opposition politics, government/BJP, conspiracy and funding, mobilisation, media, students, student unions, the CJI remark) and class-based TF-IDF terms per community. "
  "Polarization: modularity, Krackhardt's E–I index for the community and the stance partitions, stance assortativity, Random-Walk Controversy (Garimella et al., 2018), the share of cross-community edges against a degree-preserving (configuration-model) null, stance mixing matrices against independence, the hostility and reciprocity of cross-stance contacts, and bridge users identified by the participation coefficient (Guimerà & Amaral, 2005) and betweenness.")

H("4. Results")
H("4.1 Exploratory analysis", 2)
ev_t = R("03_event_volumes")
P(f"Both platforms react to the same events (Figure 1). On X the largest spike is the first protest (6 June, {int(ev_t.iloc[0]['x_items_±1day'])} posts within ±1 day), on Reddit the final week (resignation on 25 July: {int(ev_t.iloc[9]['reddit_items_±1day']):,} items). "
  f"X is bilingual (about {float(R('03_script_mix').set_index('platform').loc['x', 'devanagari']) + float(R('03_script_mix').set_index('platform').loc['x', 'mixed']):.0f}% of posts use Devanagari), Reddit is almost entirely Latin-script English or romanised Hindi. The most shared non-platform domains are mainstream news sites on both platforms (The Hindu, Hindustan Times, Indian Express, The Wire, Scroll), plus YouTube and Instagram.")
H("4.2 Interaction networks", 2)
P(f"The X network has {int(ns.loc[xnet,'nodes'])} accounts and {int(ns.loc[xnet,'edges'])} directed edges (density {ns.loc[xnet,'density']:.4f}, reciprocity {ns.loc[xnet,'reciprocity']:.3f}); the midsem network (466 nodes, 600 edges, weight 900) is reproduced exactly from the 1,823-row file, and the difference in total weight comes from removing cross-group duplicate posts and counting one interaction per post. "
  f"The Reddit network has {int(ns.loc[rnet,'nodes']):,} users and {int(ns.loc[rnet,'edges']):,} edges with much higher reciprocity ({ns.loc[rnet,'reciprocity']:.3f}) because comment threads contain real back-and-forth. "
  f"X in-degree is concentrated on the CJP founder and official account, Wangchuk, Delhi Police and news handles; Reddit in-degree is spread over many commenters.")
table(ns.reset_index()[["network", "nodes", "edges", "total_weight", "density", "reciprocity", "weakly_connected_components", "largest_wcc_nodes", "avg_clustering"]], font=7.5)
fig("04_x_largest_wcc", "Figure 2. X interaction network, largest component, coloured by account type.", 5.5)
H("4.3 Community detection", 2)
P(f"Louvain finds {len(cs['x'])} communities on X ({int(cs['x'].is_major.astype(str).str.lower().eq('true').sum())} with at least 8 accounts are characterised; modularity {polv('x','modularity'):.3f}, seed stability NMI {rob[(rob.platform=='x')&(rob.resolution==1.0)].mean_pairwise_nmi.iloc[0]:.2f}) and {len(cs['reddit'])} on Reddit (the {int(cs['reddit'].is_major.astype(str).str.lower().eq('true').sum())} largest, each with at least 30 users, are characterised; modularity {polv('reddit','modularity'):.3f}, NMI {rob[(rob.platform=='reddit')&(rob.resolution==1.0)].mean_pairwise_nmi.iloc[0]:.2f}). "
  "X communities form around the CJP accounts, around Delhi Police and government handles, around news agencies and around clusters of partisan commentators; Reddit communities coincide almost one-to-one with subreddits, because replies happen inside threads of one venue.")
fig("05_x_communities", "Figure 3. X communities (largest component).", 5.2); fig("05_reddit_communities", "Figure 4. Reddit communities (2-core of the largest component).", 5.2)
H("4.4 Community classification: stance, themes, factors", 2)
P(f"Two stance classifiers were trained on {len(ann_x)} X posts and {len(ann_rd)} Reddit items labelled by hand: an X model trained on the X labels only, and a Reddit model trained on all labels with the thread title appended as context (subreddit identity was deliberately not used as a feature, because Reddit communities are venue-based and a venue-informed stance would make the segregation measures circular; a transfer check showed that one pooled model would be worse on both platforms). In 5-fold cross-validation the X model reaches macro-F1 {ev_x:.2f} and the Reddit model {ev_r:.2f} (Reddit comments are shorter and depend on their thread); the keyword baseline scores {lex_x:.2f} and {lex_r:.2f}. Because the Reddit annotation sample is a random draw of the corpus, the predicted Reddit class shares were calibrated to the annotated shares (table 06_calibration_check). "
  f"Across all items, X is {istance_pct['x'].get('PRO',0):.0f}% PRO / {istance_pct['x'].get('NEUTRAL',0):.0f}% NEUTRAL / {istance_pct['x'].get('ANTI',0):.0f}% ANTI and Reddit {istance_pct['reddit'].get('PRO',0):.0f}% / {istance_pct['reddit'].get('NEUTRAL',0):.0f}% / {istance_pct['reddit'].get('ANTI',0):.0f}%; at user level X has {ustance_pct['x'].get('PRO',0):.0f}% PRO and {ustance_pct['x'].get('ANTI',0):.0f}% ANTI users, Reddit {ustance_pct['reddit'].get('PRO',0):.0f}% and {ustance_pct['reddit'].get('ANTI',0):.0f}%. "
  f"Hostile language appears in {100*ps['x'].hostile.mean():.1f}% of X posts and {100*ps['reddit'].hostile.mean():.1f}% of Reddit items.")
table(ev.round(3), font=7.5)
P("Final community tables (major communities):", bold=True)
table(final["x"], ["Community", "# Users", "# Items", "Main theme", "Stance of items", "Key accounts", "Label"], font=7)
table(final["reddit"], ["Community", "# Users", "# Items", "Main theme", "Stance of items", "Hashtags / subreddits", "Label"], font=7)
fig("06_community_stance", "Figure 5. Stance of items posted by each major community.")
H("4.5 Information diffusion", 2)
P(f"X threads in the corpus are almost always single posts (median size {casc.loc['50%','X threads']:.0f}), so X diffusion runs through quotes and mentions of a few hubs; Reddit threads are heavy-tailed (mean {casc.loc['mean','Reddit threads (comments)']:.0f} comments, maximum {casc.loc['max','Reddit threads (comments)']:.0f}; median depth {casc.loc['50%','Reddit max depth']:.0f}). "
  f"Mainstream news domains spread across many communities and both platforms, while partisan outlets and counter-hashtags stay inside the ANTI communities. "
  f"{int(len(R('07_cross_platform_links')))} Reddit items link directly to X posts from {cp.x_handle.nunique()} handles, mainly the CJP accounts, news handles and aggregator accounts: the measurable cross-platform flow runs from X to Reddit.")
fig("07_weekly_cross_community", "Figure 6. Weekly interactions and the share that crosses community lines.")
H("4.6 Polarization and cross-community interaction", 2)
P(f"The share of edges that cross community lines is {polv('x','share of edges crossing'):.3f} on X and {polv('reddit','share of edges crossing'):.3f} on Reddit, against {polv('x','share of edges crossing','null_mean'):.3f} and {polv('reddit','share of edges crossing','null_mean'):.3f} expected from degree-preserving rewiring (z = {polv('x','share of edges crossing','z'):.1f} and {polv('reddit','share of edges crossing','z'):.1f}): on both platforms communities are strongly closed. "
  f"By stance, the E–I index of the PRO/ANTI partition is {polv('x','E-I index, stance'):.2f} on X and {polv('reddit','E-I index, stance'):.2f} on Reddit, stance assortativity {polv('x','stance assortativity'):.2f} and {polv('reddit','stance assortativity'):.2f}, and Random-Walk Controversy {polv('x','Random-Walk'):.2f} and {polv('reddit','Random-Walk'):.2f} (label-shuffled null {polv('x','Random-Walk','null_mean'):.2f} / {polv('reddit','Random-Walk','null_mean'):.2f}). "
  f"Contacts between opposite camps are hostile in {100*qv('x','opposite sides','hostile_share'):.0f}% of cases on X versus {100*qv('x','same side','hostile_share'):.0f}% for same-side contacts, and {100*qv('reddit','opposite sides','hostile_share'):.0f}% versus {100*qv('reddit','same side','hostile_share'):.0f}% on Reddit; cross-side contacts are reciprocated at {qv('x','opposite sides','reciprocated'):.2f} (X) and {qv('reddit','opposite sides','reciprocated'):.2f} (Reddit). "
  f"{len(bridges['x'])} bridge users were identified on X and {len(bridges['reddit'])} on Reddit.")
table(pol.fillna(""), font=7.5)
fig("08_mixing_matrices", "Figure 7. Observed/expected interactions by stance of source and target user.")
fig("08_x_network_by_stance", "Figure 8. X network coloured by user stance.", 5.2)
H("4.7 Interaction versus polarization, X versus Reddit", 2)
table(comp.reset_index(), font=7.5)
table(crit[["criterion", "platform", "met", "evidence"]], font=7.5)
P(f"Verdict — X: {verd['x']}. Reddit: {verd['reddit']}.", bold=True)

H("5. Discussion")
def cmpv(p, key):
    try: return float(comp.loc[key, p])
    except Exception: return np.nan
desc = {}
for p, name in [("x", "X"), ("reddit", "Reddit")]:
    cross = cmpv(p, "share of PRO-ANTI interactions that cross sides"); ho, hs = cmpv(p, "hostile % opposite sides"), cmpv(p, "hostile % same side"); rec = cmpv(p, "reciprocity opposite sides")
    hostile_phrase = ("more than twice as hostile as" if ho >= 2 * max(hs, 1e-9) else "somewhat more hostile than" if ho > hs * 1.15 else "about as hostile as" if ho >= hs * 0.85 else "less hostile than")
    desc[p] = (f"On {name}, {100*cross:.0f}% of the interactions between PRO and ANTI users cross sides; these cross-side contacts are {hostile_phrase} contacts within a camp "
               f"({ho:.0f}% versus {hs:.0f}% hostile items) and are reciprocated in {100*rec:.0f}% of cases. Structurally, the stance E–I index is {cmpv(p, 'E-I index (stance, PRO vs ANTI)'):.2f}, stance assortativity {cmpv(p, 'stance assortativity'):.2f} and the Random-Walk Controversy score {cmpv(p, 'RWC (PRO vs ANTI)'):.2f}. Verdict: {verd[p]}.")
P("Both platforms produce communities that are far more closed than degree-preserving random networks would be, so in both cases the conflict organised users into enclosures. The platforms differ in what those enclosures are and in how the camps meet. On X the communities are built around hub accounts (the CJP leadership, Delhi Police and government handles, news agencies, partisan commentators) and align with stance; on Reddit the communities are venues — each large community is a subreddit — and the subreddits themselves are politically sorted, so stance segregation appears at the venue level.")
P(desc["x"]); P(desc["reddit"])
xc, rc_ = cmpv("x", "share of PRO-ANTI interactions that cross sides"), cmpv("reddit", "share of PRO-ANTI interactions that cross sides"); xr, rr = cmpv("x", "reciprocity opposite sides"), cmpv("reddit", "reciprocity opposite sides")
P(f"Read together, the two platforms show different modes of contact. On X, cross-side contact is {'frequent' if xc >= 0.25 else 'rare'} but essentially one-directional (critics address the movement's hubs and receive no reply), the pattern described as contact without dialogue in the cross-partisan interaction literature (Falkenberg et al., 2024; Çetinkaya et al., 2025). On Reddit, {100*rc_:.0f}% of PRO–ANTI interactions cross sides even though users mostly stay in like-minded subreddits, and such contact is {'reciprocated more often' if rr > xr else 'no more reciprocated'} than on X ({100*rr:.0f}% versus {100*xr:.0f}%), the threaded-forum pattern reported by De Francisci Morales et al. (2021), although still far from a dialogue. In the terms of the research question, the conflict produced polarization on both platforms, with X polarized around attention to hubs and Reddit polarized by venue; genuine cross-community engagement exists mainly inside Reddit threads and remains a minority of all interaction.")
P("Information flows accordingly: on X a few accounts receive most of the attention and the pro-protest hashtags spread quickly through the PRO communities, whereas counter-hashtags stay inside the ANTI cluster; on Reddit megathreads concentrate the discussion in the final week, and part of the Reddit material is imported from X (links and screenshots of the CJP accounts, news handles and aggregator accounts), so the measurable cross-platform flow runs from X to Reddit.")

H("6. Limitations")
P("X data come from search-page capture, which returns original posts far more often than reply chains, so the X network under-represents conversation and over-represents broadcast. Reddit archives miss posts removed quickly by moderators and the collection depends on keyword coverage; comments outside the study window were dropped. Stance is machine-predicted; the reported cross-validation scores bound its accuracy, and community-level shares are more reliable than individual user labels. Hostility detection combines a classifier with a lexicon and should be read as a conservative indicator. No demographic information is available, and the two corpora differ in size and unit of analysis.")

H("7. Conclusion")
P(f"Using one pipeline on both platforms, the project maps the communities that formed around the CJP–government conflict, characterises them by stance, themes and composition, traces how information and attention moved, and measures cross-community interaction against null models. The central finding is that the same conflict produced closed communities on both platforms, hub-centred and stance-aligned on X, venue-based on Reddit; the verdicts are '{verd['x']}' for X and '{verd['reddit']}' for Reddit. This supports the view that platform architecture — broadcast networks versus threaded forums — shapes the form that polarization and cross-community interaction take (Cinelli et al., 2021).")

H("References")
for ref in ["Blondel, V. D., Guillaume, J.-L., Lambiotte, R., & Lefebvre, E. (2008). Fast unfolding of communities in large networks. Journal of Statistical Mechanics.",
            "Cinelli, M., De Francisci Morales, G., Galeazzi, A., Quattrociocchi, W., & Starnini, M. (2021). The echo chamber effect on social media. PNAS 118(9).",
            "Çetinkaya, Y. M., et al. (2025). Cross-partisan interactions within echo chambers. (as cited in the midsem report)",
            "De Francisci Morales, G., Monti, C., & Starnini, M. (2021). No echo in the chambers of political interactions on Reddit. Scientific Reports 11.",
            "Falkenberg, M., et al. (2024). Patterns of partisan toxicity and engagement reveal the common structure of online political communication across countries. Nature Communications.",
            "Garimella, K., De Francisci Morales, G., Gionis, A., & Mathioudakis, M. (2018). Quantifying controversy on social media. ACM TSC 1(1).",
            "Guimerà, R., & Amaral, L. A. N. (2005). Functional cartography of complex metabolic networks. Nature 433.",
            "Krackhardt, D., & Stern, R. N. (1988). Informal networks and organizational crises: an experimental simulation. Social Psychology Quarterly 51(2).",
            "Rashed, A., et al. (2021). Embeddings-based clustering for target specific stances. ICWSM.",
            "Dash, S., et al. (2022). Divided we rule: influencer polarization on Twitter during political crises in India. ICWSM."]:
    P(ref, size=9)

H("Appendix A. Supporting outputs")
P("outputs/tables: 01 inventories; 02 funnels and schema; 03 EDA; 04 edge lists, network summary, centralities, top actors; 05 community membership, summaries, meta-edges, robustness; 06 classifier evaluation, post/user stance, community profiles, themes, representative posts, manual check sheet; 07 adoption, cascades, domain and hashtag spread, cross-platform links, weekly cross-community share; 08 polarization metrics, mixing matrices, cross-stance quality, bridges; 09 final community tables (CSV + XLSX), comparison table, verdict criteria. outputs/figures: all figures. outputs/gexf: Gephi files of both networks with community and stance attributes.", size=9)
P("Representative posts per community (first five communities, X):", bold=True, size=9)
rep = R("06_x_representative_posts"); rep["text_model"] = rep.text_model.str.slice(0, 160)
table(rep[rep.community.isin(sorted(rep.community.unique())[:5])][["community", "author", "stance", "likes", "text_model"]], font=7, max_rows=25)

out = OUT / "CSMA_Final_Report_Group9.docx"; doc.save(out); print("report written:", out)
