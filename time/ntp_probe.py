#!/usr/bin/env python3
"""ntp_probe.py SEAT OUT.jsonl ROUNDS [servers.txt]: read-only NTPv4 client queries per TIME_PLAN. 8 queries per server per round, 2.1 s apart per server, servers in parallel.
Stdlib only. Writes one JSON row per query: offset and delay from the four NTP timestamps, and the server's own stated stratum, reference id, root delay, root dispersion and leap indicator."""
import sys, socket, struct, time, json, threading, subprocess
seat, out, rounds = sys.argv[1], sys.argv[2], int(sys.argv[3]); servers = [l.strip() for l in open(sys.argv[4] if len(sys.argv) > 4 else 'servers.txt') if l.strip()]
E = 2208988800
def ntp(t): s = int(t); return struct.pack('!II', s + E, int((t - s) * 2**32) & 0xffffffff)
def unntp(b): s, f = struct.unpack('!II', b); return s - E + f / 2**32
lock = threading.Lock(); f = open(out, 'a'); RUN = int(time.time())
def log(r):
    with lock: f.write(json.dumps(r) + '\n'); f.flush()
def query(host, ip):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.settimeout(3)
    t1 = time.time(); pkt = struct.pack('!B', (0 << 6) | (4 << 3) | 3) + b'\0' * 39 + ntp(t1)
    try:
        s.sendto(pkt, (ip, 123)); d, _ = s.recvfrom(512); t4 = time.time()
    except Exception as e: return {'status': 'NOTHING_RETURNED', 'why': type(e).__name__}
    finally: s.close()
    if len(d) < 48: return {'status': 'REFUSED', 'why': 'short reply'}
    b0, st = d[0], d[1]; li = b0 >> 6
    if st == 0: return {'status': 'REFUSED', 'why': 'kiss ' + d[12:16].decode('ascii', 'replace')}
    t2, t3 = unntp(d[32:40]), unntp(d[40:48]); org = unntp(d[24:32])
    if abs(org - t1) > 1e-3: return {'status': 'HELD', 'why': 'origin mismatch'}
    rd, rp = struct.unpack('!II', d[4:12]); ref = d[12:16]
    refid = ref.decode('ascii', 'replace').strip('\0') if st == 1 else '.'.join(str(x) for x in ref)
    return {'status': 'COMMITTED', 'offset': ((t2 - t1) + (t3 - t4)) / 2, 'delay': (t4 - t1) - (t3 - t2), 'stratum': st, 'refid': refid, 'root_delay': rd / 65536, 'root_disp': rp / 65536, 'leap': li, 'version': (b0 >> 3) & 7}
def worker(host):
    try: ip = socket.getaddrinfo(host, 123, socket.AF_INET, socket.SOCK_DGRAM)[0][4][0]
    except Exception as e: log({'seat': seat, 'server': host, 'status': 'NOTHING_RETURNED', 'why': 'dns ' + type(e).__name__, 'at': time.time()}); return
    for rd in range(rounds):
        for q in range(8):
            r = query(host, ip); r.update(seat=seat, server=host, ip=ip, round=RUN + rd, q=q, at=time.time()); log(r); time.sleep(2.1)
ref = {}
if seat == 'pi':
    try:
        t = subprocess.run(['chronyc', 'tracking'], capture_output=True, text=True).stdout
        ref = {k.strip(): v.strip() for k, v in (l.split(':', 1) for l in t.splitlines() if ':' in l)}
    except Exception: pass
log({'seat': seat, 'reference': ref, 'at': time.time(), 'servers': len(servers), 'rounds': rounds})
th = [threading.Thread(target=worker, args=(h,)) for h in servers]; [t.start() for t in th]; [t.join() for t in th]; print('done', seat, out)
