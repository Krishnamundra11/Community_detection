#!/usr/bin/env python3
"""Arctic Shift thread fetcher: runs beside collect_reddit.py and pulls full comment threads for the
submissions that the PullPush collector has found (priority: core-relevant, then largest threads).
Resumable; state in state_as.json; output comments_threads_as.jsonl."""
import json, os, sys, time, urllib.request, urllib.parse, datetime, re, shutil

OUT = sys.argv[1] if len(sys.argv) > 1 else "/Users/CSMA/Project/data/reddit_raw"
API = "https://arctic-shift.photon-reddit.com/api/comments/search"
UA = "csma-research-bmu/0.1 (academic project; contact anmol.chaturvedi.23cse@bmu.edu.in)"
PACE = 3.2
AFTER = 1780272000 - 1
SUBREDDITS = {"cockroachjantaparty", "cockroachjantaparty09", "cjp_protest_"}
CORE_RE = re.compile(r"cockroach|\bcjp\b|dipke|jantar\s*mantar|pradhan|\bneet\b|paper\s*leak|wangchuk|chalo\s*sansad|"
                     r"lathi|tear\s*gas|hunger\s*strike|aisa|\bsfi\b|nsui|abvp|aisf|protest", re.I)
LOG = open(os.path.join(OUT, "collector_as.log"), "a", buffering=1)
def log(m):
    line = f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {m}"; print(line, flush=True); LOG.write(line + "\n")
STATE = os.path.join(OUT, "state_as.json")
state = json.load(open(STATE)) if os.path.exists(STATE) else {"threads_done": {}, "requests": 0}
def save_state():
    json.dump(state, open(STATE + ".tmp", "w")); os.replace(STATE + ".tmp", STATE)
def pullpush_done():
    p = os.path.join(OUT, "state.json")
    return set(json.load(open(p)).get("threads_done", {})) if os.path.exists(p) else set()
def pullpush_stage1_complete():
    p = os.path.join(OUT, "state.json")
    return os.path.exists(p) and len(json.load(open(p)).get("queries_done", {})) >= 52

def get(params, tries=7):
    url = API + "?" + urllib.parse.urlencode(params)
    for t in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as r:
                state["requests"] += 1; time.sleep(PACE)
                return json.loads(r.read().decode("utf8")).get("data") or []
        except urllib.error.HTTPError as e:
            wait = 20 * (2 ** t); log(f"  HTTP {e.code} {params.get('link_id')} -> sleep {wait}s"); time.sleep(wait)
        except Exception as e:
            log(f"  {type(e).__name__}: {str(e)[:80]} -> sleep {15*(t+1)}s"); time.sleep(15 * (t + 1))
    log(f"  GIVING UP {params}"); return None

def fetch_thread(pid):
    got = {}; after = AFTER; pages = 0
    while pages < 150:
        data = get({"link_id": f"t3_{pid}", "limit": 100, "sort": "asc", "after": after})
        if data is None: return None
        new = [c for c in data if c["id"] not in got]
        for c in new: c["_source"] = "arctic_shift"; got[c["id"]] = c
        pages += 1
        if len(data) < 100 or not new: break
        after = max(c["created_utc"] for c in data)
    return list(got.values())

def load_subs():
    subs = {}
    p = os.path.join(OUT, "submissions.jsonl")
    if os.path.exists(p):
        with open(p) as fh:
            for line in fh:
                try: d = json.loads(line)
                except Exception: continue
                subs[d["id"]] = d
    return subs

TH = os.path.join(OUT, "comments_threads_as.jsonl")
log(f"=== Arctic Shift thread worker start; done so far {len(state['threads_done'])}")
idle = 0
while True:
    subs = load_subs(); pp_done = pullpush_done()
    todo = [d for d in subs.values() if (d.get("num_comments") or 0) > 0 and d["id"] not in state["threads_done"] and d["id"] not in pp_done]
    def prio(d):
        core = bool(CORE_RE.search(f"{d.get('title','')} {d.get('selftext','')}")) or d.get("subreddit", "").lower() in SUBREDDITS
        return (0 if core else 1, -(d.get("num_comments") or 0))
    todo.sort(key=prio)
    if not todo:
        if pullpush_stage1_complete():
            idle += 1
            if idle > 3: break
        log("nothing to do yet; waiting 120 s"); time.sleep(120); continue
    idle = 0
    total_c = sum(d.get("num_comments") or 0 for d in todo); done_c = 0; t0 = time.time()
    log(f"batch: {len(todo)} threads, ~{total_c} comments")
    for i, d in enumerate(todo[:400], 1):          # re-scan the submission list every 400 threads
        if d["id"] in pullpush_done(): continue
        cs = fetch_thread(d["id"])
        if cs is None: continue
        with open(TH, "a") as fh:
            for c in cs: fh.write(json.dumps(c, ensure_ascii=False) + "\n")
        state["threads_done"][d["id"]] = len(cs); done_c += d.get("num_comments") or 0
        if i % 10 == 0:
            save_state(); el = time.time() - t0; rate = done_c / max(el, 1); eta = (total_c - done_c) / max(rate, 1e-6) / 60
            log(f"AS {i}/{len(todo)} threads | {done_c}/{total_c} expected comments ({100*done_c/max(total_c,1):.0f}%) | ETA {eta:.0f} min | req {state['requests']} | done total {len(state['threads_done'])}")
            if shutil.disk_usage('/').free / 1e9 < 2: log("LOW DISK - stop"); sys.exit(2)
    save_state()
log(f"=== Arctic Shift worker finished; threads {len(state['threads_done'])}; requests {state['requests']}")
