# Sum gasUsed x baseFeePerGas over every block in [START, END]: the RBNT paid as base fees.
# Blocks name the zero address as fee recipient, so these fees leave circulation.
import json, sys
from concurrent.futures import ThreadPoolExecutor
from rpc import batch
START, END = int(sys.argv[1]), int(sys.argv[2])
def work(lo):
    bs = batch([("eth_getBlockByNumber", [hex(n), False]) for n in range(lo, min(lo + 99, END) + 1)])
    return sum(int(b["gasUsed"], 16) * int(b.get("baseFeePerGas", "0x0"), 16) for b in bs), {b["miner"] for b in bs}
tot, miners = 0, set()
with ThreadPoolExecutor(6) as ex:
    for f, m in ex.map(work, range(START, END + 1, 100)): tot += f; miners |= m
print(json.dumps({"start": START, "end": END, "base_fees_rbnt": tot / 1e18, "fee_recipients": sorted(miners)}))
