# Daily series through the quarter, read from the chain at the last block before each midnight UTC
# (1 Jul 2026 00:00 to 1 Oct 2026 00:00): stakes and balances of both Reddex pools, WRBNT supply,
# RBNT locked in the bridge adapter, RBNT held by the token vesting contracts (WRBNT, as a group)
# and by the nine reserved wallets.
import json, datetime
from concurrent.futures import ThreadPoolExecutor
from rpc import batch

S, E = 3025809, 3209414
T0 = 1782864000                       # 2026-07-01 00:00:00 UTC
DAYS = 93                             # boundaries 1 Jul .. 1 Oct
POOL = {"nolock": "0x43a1dc107bbb06df266278056055ae7fc5bd2817", "lock365": "0x5e8040e85d0e6363d798a43bea939c026449946d"}
WRBNT = "0x6ed1f491e2d31536d6561f6bdb2adc8f092a6076"
BRIDGE = "0x020940df9f5e77338a094d55b5b5914122a804a5"
codes = json.load(open("codes.json"))
VEST = sorted(a for a, h in codes.items() if h and h == codes["0x5efecd7e24ec14a7cb970700001c7a3ac40a0282"])
RESERVED = [r["address"].lower() for r in json.load(open("treasury_table.json"))]

def ts(n): return int(batch([("eth_getBlockByNumber", [hex(n), False])])[0]["timestamp"], 16)
def last_before(t):
    lo, hi = S - 200000, E + 20000                  # ts(lo) < t <= ts(hi); E + 20000 is before the chain head
    while hi - lo > 1:
        m = (lo + hi) // 2
        if ts(m) < t: lo = m
        else: hi = m
    return lo
bounds = [T0 + 86400 * d for d in range(DAYS)]
with ThreadPoolExecutor(8) as ex: blocks = list(ex.map(last_before, bounds))
assert blocks[0] == S and blocks[-1] == E, (blocks[0], blocks[-1])

def arg(a): return a[2:].rjust(64, "0")
def read(b):
    calls = [("eth_call", [{"to": POOL["nolock"], "data": "0x8b0e9f3f"}, hex(b)]),
             ("eth_call", [{"to": POOL["lock365"], "data": "0x8b0e9f3f"}, hex(b)]),
             ("eth_getBalance", [POOL["nolock"], hex(b)]), ("eth_getBalance", [POOL["lock365"], hex(b)]),
             ("eth_call", [{"to": WRBNT, "data": "0x18160ddd"}, hex(b)]), ("eth_getBalance", [BRIDGE, hex(b)])]
    calls += [("eth_call", [{"to": WRBNT, "data": "0x70a08231" + arg(v)}, hex(b)]) for v in VEST]
    calls += [("eth_getBalance", [r, hex(b)]) for r in RESERVED]
    calls += [("eth_call", [{"to": WRBNT, "data": "0x70a08231" + arg(r)}, hex(b)]) for r in RESERVED]
    v = [int(x, 16) / 1e18 for x in batch(calls)]
    k = 6 + len(VEST)
    return {"block": b, "staked_nolock": v[0], "staked_lock365": v[1], "balance_nolock": v[2], "balance_lock365": v[3],
            "wrbnt_supply": v[4], "bridge": v[5], "vesting": sum(v[6:k]), "reserved": sum(v[k:])}
with ThreadPoolExecutor(6) as ex: rows = list(ex.map(read, blocks))
for d, r in zip(bounds, rows):
    r["date"] = (datetime.datetime.fromtimestamp(d, datetime.UTC) - datetime.timedelta(seconds=1)).strftime("%Y-%m-%d")
    r["as_of_utc"] = datetime.datetime.fromtimestamp(d, datetime.UTC).strftime("%Y-%m-%d 00:00")
json.dump({"vesting_contracts": len(VEST), "rows": rows}, open("daily.json", "w"), indent=1)
print(len(rows), "days; vesting contracts", len(VEST))
for r in rows[:2] + rows[-2:]: print(r)
