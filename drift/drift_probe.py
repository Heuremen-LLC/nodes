#!/usr/bin/env python3
"""drift_probe.py: DRIFT SEAT per drift/PLAN.md. Runs on a GitHub runner. Stdlib only."""
import json, re, hashlib, time, datetime as D, urllib.request, urllib.error, os, sys
UA = {'User-Agent': 'heuremen-drift-seat/0.1 (+https://github.com/Heuremen-LLC/nodes)'}
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); T = json.load(open(os.path.join(HERE, 'targets.json')))
SITE = 'https://indahl.ai/'; RAW = 'https://raw.githubusercontent.com/Heuremen-LLC/indahl.ai/main/'
def get(u, n=3):
    for i in range(n):
        try: return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40).read()
        except urllib.error.HTTPError as e:
            if e.code in (404, 410): return None
            time.sleep(2 * (i + 1))
        except Exception: time.sleep(2 * (i + 1))
    return None
sha = lambda b: hashlib.sha256(b).hexdigest()
def stamp(d, now, path=None):
    # 30 Oct 2026 (site pass H-17, I-9): a feed whose top-level stamp is a one-time read names the stamp the live keeper writes (targets.json "stamps", e.g. "live.updated")
    if path:
        s = d
        for k in path.split('.'): s = s.get(k) if isinstance(s, dict) else None
    else: s = d.get('updated') or d.get('read')
    if not isinstance(s, str): return None
    m = re.match(r'(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})', s)
    if m: return D.datetime(*map(int, m.groups()), tzinfo=D.timezone.utc)
    m = re.match(r'(\d{1,2}) ([A-Za-z]{3}) (\d{2}):(\d{2})', s)
    if m:
        mo = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'].index(m.group(2).lower()) + 1
        t = D.datetime(now.year, mo, int(m.group(1)), int(m.group(3)), int(m.group(4)), tzinfo=D.timezone.utc)
        return t if t <= now + D.timedelta(hours=1) else t.replace(year=now.year - 1)
now = D.datetime.now(D.timezone.utc)
# known-good
front = get(SITE); front_raw = get(RAW + 'index.html'); missing = get(SITE + 'this-page-does-not-exist-heuremen-seat')
control = bool(front and front_raw and sha(front) == sha(front_raw) and missing is None)
row = dict(t=now.strftime('%Y-%m-%dT%H:%M:%SZ'), control='PASSED' if control else 'CONTROL_FAILED')
if control:
    pages = {}
    for p in T['pages']:
        a = get(SITE + p); b = get(RAW + ((p or 'index') + '.html'))
        pages[p or '/'] = 'UNREACHABLE' if a is None or b is None else ('MATCH' if sha(a) == sha(b) else 'DIFFER')
    feeds = {}
    for f, lim in T['feeds']:
        b = get(SITE + f)
        try: d = json.loads(b) if b else None
        except Exception: d = None
        t = stamp(d, now, T.get('stamps', {}).get(f)) if isinstance(d, dict) else None
        if t is None: feeds[f] = dict(state='UNREACHABLE')
        else:
            age = round((now - t).total_seconds() / 3600, 2); feeds[f] = dict(age_h=age, limit_h=lim, state='FRESH' if age <= lim else 'STALE')
    chain = get(RAW + 'code/archive/chain.jsonl'); ok = False; n = 0
    if chain:
        prev = '0' * 64; ok = True
        for l in chain.decode().splitlines():
            e = json.loads(l); m = get(RAW + 'code/archive/manifests/%s.json' % e['id']); ms = sha(m) if m else None
            d = hashlib.sha256((prev + (ms or '')).encode()).hexdigest()
            if ms != e['manifest_sha256'] or d != e['digest'] or e['prev'] != prev: ok = False
            prev = e['digest']; n += 1
    row.update(pages=pages, feeds=feeds, chain=dict(state='OK' if ok else 'BROKEN', entries=n))
os.makedirs(os.path.join(ROOT, 'data', 'drift'), exist_ok=True)
with open(os.path.join(ROOT, 'data', 'drift', 'history.jsonl'), 'a') as f: f.write(json.dumps(row) + '\n')
json.dump(row, open(os.path.join(ROOT, 'data', 'drift', 'latest.json'), 'w'), indent=1)
print(row['control'], {k: v for k, v in row.items() if k in ('chain',)}, sum(1 for v in row.get('pages', {}).values() if v != 'MATCH'), 'pages not matching', sum(1 for v in row.get('feeds', {}).values() if v['state'] != 'FRESH'), 'feeds not fresh')
