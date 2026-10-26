# Sum the balance at block 0 (genesis) of every address found. If this is below the genesis supply,
# the genesis allocated RBNT to addresses that never appear in any transaction.
import json
from concurrent.futures import ThreadPoolExecutor
from rpc import batch
u = json.load(open("universe.json"))
def work(ch):
    r = batch([("eth_getBalance", [a, "0x0"]) for a in ch])
    return [(a, int(x, 16)) for a, x in zip(ch, r) if int(x, 16)]
nz = []
with ThreadPoolExecutor(8) as ex:
    for res in ex.map(work, [u[i:i + 100] for i in range(0, len(u), 100)]): nz += res
tot = sum(v for _, v in nz)
print("addresses funded at genesis (found):", len(nz), "sum", tot / 1e18)
for a, v in sorted(nz, key=lambda x: -x[1])[:15]: print(a, v / 1e18)
json.dump([(a, str(v)) for a, v in nz], open("genesis_found.json", "w"))
