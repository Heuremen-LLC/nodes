#!/usr/bin/env python3
"""status_probe.py SEAT OUT.jsonl: one UPTIME round per PLAN.md. Reads every vendor's status page indicator (seat 'mac' only) and makes one plain HTTPS GET to each vendor endpoint from this seat. Stdlib only."""
import sys, json, time, urllib.request, urllib.error, threading
seat, out = sys.argv[1], sys.argv[2]; V = json.load(open(sys.argv[3] if len(sys.argv) > 3 else 'vendors.json')); UA = 'heuremen-uptime/0.1 (+https://indahl.ai/uptime)'
lock = threading.Lock(); f = open(out, 'a'); now = int(time.time())
def log(r):
    with lock: f.write(json.dumps(r) + '\n'); f.flush()
def probe(v):
    t = time.time(); code = None; err = None
    try: code = urllib.request.urlopen(urllib.request.Request(v['probe'], headers={'User-Agent': UA}), timeout=10).status
    except urllib.error.HTTPError as e: code = e.code
    except Exception as e: err = type(e).__name__
    ok = err is None and code is not None and code < 500
    row = dict(kind='probe', round=now, seat=seat, vendor=v['name'], ok=ok, code=code, err=err, ms=round((time.time() - t) * 1000)); 
    if v.get('status') and seat == 'mac':
        try:
            d = json.loads(urllib.request.urlopen(urllib.request.Request(v['status'] + '/api/v2/summary.json', headers={'User-Agent': UA}), timeout=15).read())
            log(dict(kind='status', round=now, vendor=v['name'], indicator=d['status']['indicator'], description=d['status']['description'], incidents=len(d.get('incidents', []))))
        except Exception as e: log(dict(kind='status', round=now, vendor=v['name'], indicator=None, err=type(e).__name__))
    log(row)
th = [threading.Thread(target=probe, args=(v,)) for v in V]; [t.start() for t in th]; [t.join() for t in th]; print('round', now, seat, len(V))
