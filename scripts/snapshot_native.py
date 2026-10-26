# Native RBNT balance at both snapshot blocks for addresses not yet in snapshots.json.
# Used for the large set of early-chain addresses: stakers and WRBNT holders are already
# fully covered (their sums reconcile to the wei), so only plain RBNT needs reading here.
# Addresses with zero at both blocks are listed in zero_both.txt and left out of snapshots.json.
import json, sys
from concurrent.futures import ThreadPoolExecutor
from rpc import batch
S, E = 3025809, 3209414
snap = json.load(open("snapshots.json"))
todo = [a for a in json.load(open(sys.argv[1])) if a not in snap]
def work(chunk):
    r = iter(batch([c for a in chunk for c in (("eth_getBalance", [a, hex(S)]), ("eth_getBalance", [a, hex(E)]))]))
    return [(a, int(next(r), 16), int(next(r), 16)) for a in chunk]
chunks = [todo[i:i + 50] for i in range(0, len(todo), 50)]
zero = 0
with ThreadPoolExecutor(8) as ex, open("zero_both.txt", "w") as z:
    for i, res in enumerate(ex.map(work, chunks)):
        for a, s, e in res:
            if s == 0 and e == 0: z.write(a + "\n"); zero += 1; continue
            snap[a] = {"rbnt_start": str(s), "rbnt_end": str(e), "wrbnt_start": "0", "wrbnt_end": "0",
                       "nolock_start": "0", "nolock_end": "0", "lock365_start": "0", "lock365_end": "0"}
        if i % 1000 == 0: print(i, len(chunks), file=sys.stderr, flush=True)
json.dump(snap, open("snapshots.json", "w"))
print("checked", len(todo), "zero at both blocks", zero, "snapshots now", len(snap))
