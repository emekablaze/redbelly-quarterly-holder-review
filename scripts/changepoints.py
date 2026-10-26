# For each named wallet, find every block in (S, E] where its native balance changes, by sampling
# then binary-searching each interval whose endpoints differ. Works for wallets with few changes.
import json, sys
from rpc import batch
S, E = 3025809, 3209414
addrs = json.loads(sys.argv[1])
def bals(a, blocks): return [int(x, 16) for x in batch([("eth_getBalance", [a, hex(b)]) for b in blocks])]
out = {}
for a in addrs:
    pts = list(range(S, E, 2000)) + [E]
    vs = bals(a, pts)
    changes = []
    for (lo, vlo), (hi, vhi) in zip(zip(pts, vs), zip(pts[1:], vs[1:])):
        stack = [(lo, vlo, hi, vhi)]
        while stack:
            l, vl, h, vh = stack.pop()
            if vl == vh: continue          # assumes no in-and-out round trip inside an interval
            if h - l == 1: changes.append((h, (vh - vl))); continue
            m = (l + h) // 2; vm = bals(a, [m])[0]
            stack += [(l, vl, m, vm), (m, vm, h, vh)]
    out[a] = sorted(changes)
    print(a, len(changes), sum(c for _, c in changes) / 1e18, flush=True)
json.dump(out, open(sys.argv[2], "w"))
