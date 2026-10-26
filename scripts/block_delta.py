# For one block B: read every known address's balance at B-1 and B, and report who changed.
# Used to see where a block's transaction fee goes (burned, or credited to someone).
import json, sys
from concurrent.futures import ThreadPoolExecutor
from rpc import batch
B = int(sys.argv[1])
addrs = list(json.load(open("snapshots.json")))
def work(chunk):
    r = iter(batch([c for a in chunk for c in (("eth_getBalance", [a, hex(B - 1)]), ("eth_getBalance", [a, hex(B)]))]))
    return [(a, int(next(r), 16), int(next(r), 16)) for a in chunk]
ch = []
with ThreadPoolExecutor(8) as ex:
    for res in ex.map(work, [addrs[i:i + 50] for i in range(0, len(addrs), 50)]):
        ch += [(a, y - x) for a, x, y in res if x != y]
blk = batch([("eth_getBlockByNumber", [hex(B), True])])[0]
fee = int(blk["gasUsed"], 16) * int(blk["baseFeePerGas"], 16)
print(json.dumps({"block": B, "base_fee_rbnt": fee / 1e18, "net_change_rbnt": sum(d for _, d in ch) / 1e18,
                  "changes": [(a, d / 1e18) for a, d in ch], "txs": [(t["from"], t["to"], int(t["value"], 16) / 1e18) for t in blk["transactions"]]}, indent=1))
