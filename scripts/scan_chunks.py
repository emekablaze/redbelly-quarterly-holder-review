# Scan every block in [START, END] and write one file per 10,000 blocks (resumable).
# Each row: block, timestamp, tx hash, from, to, value (wei), 4-byte selector.
import json, os, sys
from concurrent.futures import ThreadPoolExecutor
from rpc import batch, TooLarge
START, END, DIR = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
os.makedirs(DIR, exist_ok=True)
def blocks(lo, hi):
    out = []
    try:
        res = batch([("eth_getBlockByNumber", [hex(n), True]) for n in range(lo, hi + 1)])
    except TooLarge:
        if lo == hi: raise
        mid = (lo + hi) // 2           # response too large: split the range in two
        return blocks(lo, mid) + blocks(mid + 1, hi)
    for b in res:
        for t in b["transactions"]:
            out.append([int(b["number"], 16), int(b["timestamp"], 16), t["hash"], t["from"].lower(), (t["to"] or "").lower(), str(int(t["value"], 16)), t["input"][:10]])
    return out
for c in range(START, END + 1, 10000):
    f = os.path.join(DIR, f"{c}.json")
    if os.path.exists(f): continue
    hi = min(c + 9999, END)
    with ThreadPoolExecutor(4) as ex:
        parts = list(ex.map(lambda lo: blocks(lo, min(lo + 99, hi)), range(c, hi + 1, 100)))
    json.dump([r for p in parts for r in p], open(f + ".tmp", "w")); os.replace(f + ".tmp", f)
    print("done", c, file=sys.stderr, flush=True)
