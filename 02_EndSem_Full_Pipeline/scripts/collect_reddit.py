#!/usr/bin/env python3
"""Resumable Reddit collector for the CJP / Jantar Mantar study (PullPush archive API).

Stages (each checkpointed; safe to kill and restart):
  1  submissions matching keyword groups A-D and the CJP subreddits, 1 Jun - 31 Jul 2026 (UTC)
  2a full comment threads for core-relevant submissions (priority 1)
  1b keyword comment search for core terms (capped pages per term)
  2b full comment threads for the remaining submissions with comments (priority 2)
"""
import json, os, sys, time, urllib.request, urllib.parse, datetime, re, shutil

OUT = sys.argv[1] if len(sys.argv) > 1 else "/Users/CSMA/Project/data/reddit_raw"
os.makedirs(OUT, exist_ok=True)
BASE = "https://api.pullpush.io/reddit/search"
UA = "csma-research-bmu/0.1 (academic project; contact anmol.chaturvedi.23cse@bmu.edu.in)"
AFTER, BEFORE = 1780272000, 1785542399          # 2026-06-01 00:00:00 .. 2026-07-31 23:59:59 UTC
PACE = 6.0                                      # seconds between requests (PullPush returns 429 above ~15 per minute)
MAX_PAGES_SUBMISSION = 400                      # 40,000 posts per query cap
MAX_PAGES_COMMENT_KEYWORD = 40                  # 12,000 comments per term cap
MIN_FREE_GB = 2.0
PAGE = 50                                       # PullPush throttles size=100 requests much harder

QUERIES = {
  "A": ['"Cockroach Janta Party"', 'CJP', '"Abhijeet Dipke"', 'Dipke', '"cockroach party"', 'cockroachjantaparty',
        '"Saurav Das"', '"Ashutosh Ranka"', '"Vijeta Dahiya"', '"Cockroach is Back"', '"cockroach janta"'],
  "B": ['NEET protest', '"paper leak"', '"Dharmendra Pradhan"', '"Pradhan resign"', '"education minister"',
        '"NEET-UG"', 'NTA protest', 'NEET scam', '"exam manifesto"', 'NEET "Jantar Mantar"'],
  "C": ['"Jantar Mantar"', '"Delhi Police" protest', '"Sonam Wangchuk"', 'Wangchuk', '"lathi charge"', '"Chalo Sansad"',
        '"Parliament march"', '"tear gas" Delhi', '"B-team"', '"foreign funding"', 'Nadda CJP', '"hunger strike" Delhi',
        '"Pradhan Go Back"', '"Delhi Metro" protest', 'Kejriwal "Jantar Mantar"'],
  "D": ['AISA protest', 'SFI protest', 'NSUI protest', 'ABVP protest', 'AISF', '"Cockroach Students"', '"student union" protest',
        '"JNU students"', '"Neha Bora"', '"Aishe Ghosh"', '"students protest" Delhi', '"Gen Z" protest India', 'KYS protest'],
}
SUBREDDITS = ["cockroachjantaparty", "CockroachJantaParty09", "CJP_Protest_"]
COMMENT_TERMS = ['"Cockroach Janta"', 'CJP', 'Dipke', '"Jantar Mantar"', '"Dharmendra Pradhan"', 'Wangchuk', '"paper leak"',
                 '"cockroach party"', 'Pradhan resign']
CORE_RE = re.compile(r"cockroach|\bcjp\b|dipke|jantar\s*mantar|pradhan|\bneet\b|paper\s*leak|wangchuk|chalo\s*sansad|"
                     r"lathi|tear\s*gas|hunger\s*strike|aisa|\bsfi\b|nsui|abvp|aisf|protest", re.I)

LOG = open(os.path.join(OUT, "collector.log"), "a", buffering=1)
def log(msg):
    line = f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {msg}"
    print(line, flush=True); LOG.write(line + "\n")

STATE_PATH = os.path.join(OUT, "state.json")
state = json.load(open(STATE_PATH)) if os.path.exists(STATE_PATH) else {"queries_done": {}, "subs_done": {}, "threads_done": {}, "comment_terms_done": {}, "requests": 0}
def save_state():
    tmp = STATE_PATH + ".tmp"; json.dump(state, open(tmp, "w")); os.replace(tmp, STATE_PATH)

def free_gb(path="/"):
    s = shutil.disk_usage(path); return s.free / 1e9

n_req = 0; t_start = time.time()
class RateLimited(Exception):
    pass

def get(url, tries=8):
    """GET with backoff. 429/422 (rate limit or temporary ban) never gives up: it waits 5, 10, ... up to 30 minutes."""
    global n_req
    t = 0
    while True:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=90) as r:
                n_req += 1; state["requests"] = state.get("requests", 0) + 1
                time.sleep(PACE)
                return json.loads(r.read().decode("utf8"))
        except urllib.error.HTTPError as e:
            if e.code in (429, 422):
                if t >= 1: raise RateLimited(url[:120])
                log(f"  HTTP {e.code} (rate limit) -> sleep 2 min"); time.sleep(120); t += 1; continue
            t += 1
            if t >= tries: break
            log(f"  HTTP {e.code} on {url[:110]} -> sleep {8*t}s"); time.sleep(8 * t)
        except Exception as e:
            t += 1
            if t >= tries: break
            log(f"  {type(e).__name__}: {str(e)[:80]} -> sleep {10*t}s"); time.sleep(10 * t)
    raise RuntimeError(f"archive unavailable: {url[:120]}")

def append_jsonl(path, rows):
    with open(path, "a") as fh:
        for r in rows: fh.write(json.dumps(r, ensure_ascii=False) + "\n")

def paginate(kind, params, max_pages, stop_key=None):
    """Yield pages of results newest-first inside the window using a moving 'before' cursor."""
    before = BEFORE; pages = 0; seen = set()
    while pages < max_pages:
        q = dict(params); q.update({"after": AFTER, "before": before, "size": PAGE, "sort": "desc", "sort_type": "created_utc"})
        url = f"{BASE}/{kind}/?" + urllib.parse.urlencode(q, quote_via=urllib.parse.quote)
        js = get(url)
        data = [d for d in js.get("data", []) if d.get("id") not in seen]
        if not data: break
        seen.update(d["id"] for d in data); pages += 1
        yield data
        before = min(d["created_utc"] for d in data) - 1
        if len(js.get("data", [])) < PAGE: break
    if pages >= max_pages: log(f"  CAP reached ({max_pages} pages) for {params}")

# ---------------------------------------------------------------- stage 1: submissions
SUB_PATH = os.path.join(OUT, "submissions.jsonl")
sub_index = {}   # id -> set(queries)
IDX_PATH = os.path.join(OUT, "submission_queries.json")
if os.path.exists(IDX_PATH): sub_index = {k: set(v) for k, v in json.load(open(IDX_PATH)).items()}
def save_index(): json.dump({k: sorted(v) for k, v in sub_index.items()}, open(IDX_PATH + ".tmp", "w")); os.replace(IDX_PATH + ".tmp", IDX_PATH)

jobs = [(g, q, {"q": q}) for g, qs in QUERIES.items() for q in qs if q != "CJP"] + [("A", f"subreddit:{s}", {"subreddit": s}) for s in SUBREDDITS] + [("A", "CJP", {"q": "CJP"})]
log(f"=== STAGE 1: {len(jobs)} submission jobs; already done {len(state['queries_done'])}; free disk {free_gb():.1f} GB")
queue = [j for j in jobs if f"{j[0]}|{j[1]}" not in state["queries_done"]]
fails_in_row = 0
while queue:
    g, label, params = queue.pop(0)
    key = f"{g}|{label}"
    if True:
        try:
            n_new = n_tot = 0
            for page in paginate("submission", params, MAX_PAGES_SUBMISSION):
                fresh = []
                for d in page:
                    n_tot += 1
                    if d["id"] not in sub_index:
                        sub_index[d["id"]] = set(); fresh.append(d); n_new += 1
                    sub_index[d["id"]].add(key)
                if fresh: append_jsonl(SUB_PATH, fresh)
                save_index()
            fails_in_row = 0
        except (RuntimeError, RateLimited) as e:
            fails_in_row += 1; queue.append((g, label, params))
            log(f"  rate-limited on {key}; deferred to the end of the queue ({len(queue)} left)")
            if fails_in_row >= len(queue): log("  every remaining job is throttled -> sleep 15 min"); time.sleep(900); fails_in_row = 0
            continue
    state["queries_done"][key] = {"matched": n_tot, "new": n_new, "ts": time.time()}; save_state()
    log(f"stage1 {key:45s} matched {n_tot:6d} new {n_new:6d} | total unique {len(sub_index):6d} | req {state['requests']} | {(time.time()-t_start)/60:.1f} min")
    if free_gb() < MIN_FREE_GB: log("LOW DISK - stopping"); sys.exit(2)

# ---------------------------------------------------------------- stage 2: threads
subs = {}
with open(SUB_PATH) as fh:
    for line in fh:
        d = json.loads(line); subs[d["id"]] = d
def priority(d):
    text = f"{d.get('title','')} {d.get('selftext','')}"
    core = bool(CORE_RE.search(text)) or d.get("subreddit", "").lower() in [s.lower() for s in SUBREDDITS]
    return 1 if core else 2
TH_PATH = os.path.join(OUT, "comments_threads.jsonl")
AS_STATE = os.path.join(OUT, "state_as.json")
def as_done():
    return set(json.load(open(AS_STATE)).get("threads_done", {})) if os.path.exists(AS_STATE) else set()
def fetch_threads(prio):
    done_elsewhere = as_done()
    todo = [d for d in subs.values() if (d.get("num_comments") or 0) > 0 and priority(d) == prio and d["id"] not in state["threads_done"] and d["id"] not in done_elsewhere]
    todo.sort(key=lambda d: (d.get("num_comments") or 0))   # smallest first: the Arctic Shift worker takes the largest
    total_c = sum(d.get("num_comments") or 0 for d in todo)
    log(f"=== STAGE 2 (priority {prio}): {len(todo)} threads to fetch, ~{total_c} comments expected; already done {len(state['threads_done'])}")
    t0 = time.time(); done_c = 0
    for i, d in enumerate(todo, 1):
        if i % 25 == 0: done_elsewhere = as_done()
        if d["id"] in done_elsewhere: continue
        got = {}
        while True:
            try:
                for page in paginate("comment", {"link_id": d["id"]}, 200):
                    for c in page: got[c["id"]] = c
                break
            except (RuntimeError, RateLimited) as e:
                log(f"  {e}; retrying thread {d['id']} in 10 min"); time.sleep(600); got = {}
        append_jsonl(TH_PATH, list(got.values()))
        state["threads_done"][d["id"]] = len(got); done_c += d.get("num_comments") or 0
        if i % 10 == 0 or i == len(todo):
            save_state(); el = time.time() - t0; rate = done_c / max(el, 1)
            eta = (total_c - done_c) / max(rate, 1e-6) / 60
            log(f"stage2 p{prio} {i}/{len(todo)} threads | {done_c}/{total_c} expected comments ({100*done_c/max(total_c,1):.0f}%) | ETA {eta:.0f} min | req {state['requests']} | free {free_gb():.1f} GB")
            if free_gb() < MIN_FREE_GB: log("LOW DISK - stopping"); sys.exit(2)
    save_state()

# ---------------------------------------------------------------- stage 1b: keyword comments
CK_PATH = os.path.join(OUT, "comments_keyword.jsonl")
log(f"=== STAGE 1b: {len(COMMENT_TERMS)} comment keyword jobs")
for term in COMMENT_TERMS:
    if term in state["comment_terms_done"]: continue
    while True:
        try:
            n = 0
            for page in paginate("comment", {"q": term}, MAX_PAGES_COMMENT_KEYWORD):
                for c in page: c["_matched_term"] = term
                append_jsonl(CK_PATH, page); n += len(page)
            break
        except (RuntimeError, RateLimited) as e:
            log(f"  {e}; retrying term {term} in 10 min"); time.sleep(600)
    state["comment_terms_done"][term] = n; save_state()
    log(f"stage1b {term:28s} comments {n:6d} | req {state['requests']} | {(time.time()-t_start)/60:.1f} min")

fetch_threads(1)
fetch_threads(2)
log(f"=== ALL STAGES COMPLETE in {(time.time()-t_start)/60:.1f} min; requests {state['requests']}; submissions {len(sub_index)}; threads {len(state['threads_done'])}")
