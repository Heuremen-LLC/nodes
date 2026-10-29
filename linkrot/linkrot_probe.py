#!/usr/bin/env python3
"""linkrot_probe.py: the second seat for LINKROT (indahl.ai/linkrot). Reads data/linkrot/urls.txt (one URL per line, written by the first seat), runs the ten controls, requests each URL
the same way the first seat does and writes data/linkrot/results.jsonl: one line per URL with its status. If a control reads wrong the pass is discarded (no results file written).
Statuses: LIVE, GONE, DNS_FAIL, BLOCKED, TIMEOUT. One request at a time per host with a pause. usage: python3 linkrot/linkrot_probe.py"""
import sys, json, time, socket, threading, urllib.request, urllib.error, urllib.parse, collections as C
from concurrent.futures import ThreadPoolExecutor
UA = 'heuremen-linkrot/0.1 (+https://indahl.ai/linkrot) seat github-azure'
LIVE_CTL = ['https://github.com/torvalds/linux', 'https://www.python.org', 'https://arxiv.org/abs/1706.03762', 'https://example.com', 'https://zenodo.org']
DEAD_CTL = ['https://github.com/this-owner-does-not-exist-7q2/none', 'https://example.com/no-such-page-7q2', 'https://made-up-host-7q2.invalid', 'https://raw.githubusercontent.com/torvalds/linux/master/no-such-file-7q2', 'https://zenodo.org/records/99999999999']
locks = C.defaultdict(threading.Lock); lastreq = {}
def probe(u):
    host = urllib.parse.urlparse(u).netloc
    with locks[host]:
        wait = 1.2 - (time.time() - lastreq.get(host, 0))
        if wait > 0: time.sleep(wait)
        try:
            for method in ('HEAD', 'GET'):
                try:
                    r = urllib.request.urlopen(urllib.request.Request(u, method=method, headers={'User-Agent': UA}), timeout=20); code = r.status; break
                except urllib.error.HTTPError as e:
                    if method == 'HEAD' and e.code in (403, 405, 501): continue
                    code = e.code; break
            return 'LIVE' if 200 <= code < 300 else ('GONE' if code in (404, 410, 451) else 'BLOCKED')
        except urllib.error.URLError as e:
            r = getattr(e, 'reason', None)
            if isinstance(r, socket.gaierror): return 'DNS_FAIL'
            if isinstance(r, (socket.timeout, TimeoutError)) or 'timed out' in str(r): return 'TIMEOUT'
            return 'BLOCKED'
        except (socket.timeout, TimeoutError): return 'TIMEOUT'
        except Exception: return 'BLOCKED'
        finally: lastreq[host] = time.time()
ctl = {u: probe(u) for u in LIVE_CTL + DEAD_CTL}
ok = all(ctl[u] == 'LIVE' for u in LIVE_CTL) and all(ctl[u] in ('GONE', 'DNS_FAIL') for u in DEAD_CTL)
print('controls', 'passed' if ok else 'FAILED', ctl if not ok else '')
if not ok: sys.exit(1)
urls = [l.strip() for l in open('data/linkrot/urls.txt') if l.strip()]; now = time.time()
with ThreadPoolExecutor(8) as ex: res = list(ex.map(probe, urls))
with open('data/linkrot/results.jsonl', 'w') as o:
    for u, s in zip(urls, res): o.write(json.dumps(dict(url=u, status=s, t=now, seat='github-azure')) + '\n')
print(len(urls), 'urls', dict(C.Counter(res)))
