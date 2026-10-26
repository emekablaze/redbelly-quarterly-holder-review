# Fetch full transaction input for the given tx hashes and pull out every ABI-encoded address
# (32-byte words whose first 12 bytes are zero and the rest non-zero). Recipients of batch
# payouts appear this way even though they never send a transaction themselves.
import json, sys
from concurrent.futures import ThreadPoolExecutor
from rpc import batch
def words_to_addrs(data):
    out = set(); d = data[10:]
    for i in range(0, len(d) - 63, 64):
        w = d[i:i + 64]
        if w[:24] == "0" * 24 and w[24:].strip("0") and len(w[24:].lstrip("0")) >= 30:
            out.add("0x" + w[24:])
    return out
def work(hs):
    txs = batch([("eth_getTransactionByHash", [h]) for h in hs])
    s = set()
    for t in txs: s |= words_to_addrs(t["input"])
    return s
if __name__ == "__main__":
    hashes = json.load(open(sys.argv[1])); out = set()
    with ThreadPoolExecutor(6) as ex:
        for s in ex.map(work, [hashes[i:i + 50] for i in range(0, len(hashes), 50)]): out |= s
    json.dump(sorted(out), open(sys.argv[2], "w")); print("addresses found", len(out))
