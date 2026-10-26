# Build the address list (universe.json) and the quarter's transactions (q3_txs.json).
# Address list = every sender/recipient (chunks/*.json from scan_chunks.py)
#              + every address named in transaction data (addr_chunks/*.json from scan_addrs.py)
#              + WRBNT holders (Routescan) + the named addresses.
import glob, json, os
S, E = 3025809, 3209414
u, q3 = set(), []
for f in sorted(glob.glob("chunks/*.json")):
    for t in json.load(open(f)):
        u.add(t[3]); u.add(t[4])
        if S < t[0] <= E: q3.append(t)
for f in glob.glob("addr_chunks/*.json"):
    u |= set(json.load(open(f)))
q3.sort(key=lambda t: t[0])
json.dump(q3, open("q3_txs.json", "w"))
if os.path.exists("wrbnt_holders_now.json"):
    u |= {h["address"].lower() for h in json.load(open("wrbnt_holders_now.json"))}
u |= {r["address"].lower() for r in json.load(open("treasury_table.json"))}
u |= {"0x6ed1f491e2d31536d6561f6bdb2adc8f092a6076", "0x43a1dc107bbb06df266278056055ae7fc5bd2817",
      "0x5e8040e85d0e6363d798a43bea939c026449946d", "0x020940df9f5e77338a094d55b5b5914122a804a5"}
u.discard("")
json.dump(sorted(u), open("universe.json", "w"))
print("quarter txs", len(q3), "addresses", len(u))
