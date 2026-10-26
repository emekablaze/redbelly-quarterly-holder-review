# Read, for every address, at the two snapshot blocks:
#   native RBNT balance, WRBNT balance, and staked amount in each Reddex pool (userInfo(addr).amount).
# Usage: python3 snapshot.py addresses.json out.json   (adds to out.json if it already exists)
import json, sys
from concurrent.futures import ThreadPoolExecutor
from rpc import batch
S, E = 3025809, 3209414
WRBNT = "0x6ed1f491e2d31536d6561f6bdb2adc8f092a6076"
POOLS = {"nolock": "0x43a1dc107bbb06df266278056055ae7fc5bd2817", "lock365": "0x5e8040e85d0e6363d798a43bea939c026449946d"}
def arg(a): return a[2:].lower().rjust(64, "0")
def work(chunk):
    calls = []
    for a in chunk:
        for b in (S, E):
            calls.append(("eth_getBalance", [a, hex(b)]))
            calls.append(("eth_call", [{"to": WRBNT, "data": "0x70a08231" + arg(a)}, hex(b)]))
            for p in POOLS.values():
                calls.append(("eth_call", [{"to": p, "data": "0x1959a002" + arg(a)}, hex(b)]))
    res = iter(batch(calls)); out = {}
    for a in chunk:
        r = {}
        for tag in ("start", "end"):
            r["rbnt_" + tag] = str(int(next(res), 16))
            r["wrbnt_" + tag] = str(int(next(res), 16))
            for k in POOLS:
                v = next(res)
                r[k + "_" + tag] = str(int(v[2:66], 16)) if len(v) >= 66 else "0"
        out[a] = r
    return out
addrs = sorted({a.lower() for a in json.load(open(sys.argv[1]))})
try: snap = json.load(open(sys.argv[2]))
except Exception: snap = {}
todo = [a for a in addrs if a not in snap]
chunks = [todo[i:i + 12] for i in range(0, len(todo), 12)]
with ThreadPoolExecutor(6) as ex:
    for i, o in enumerate(ex.map(work, chunks)):
        snap.update(o)
        if i % 200 == 0: print(i, len(chunks), file=sys.stderr, flush=True)
json.dump(snap, open(sys.argv[2], "w"))
print("addresses", len(snap), "new", len(todo))
