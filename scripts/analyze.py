# Turn the raw snapshots into the report's tables (CSV + one JSON with every figure the report quotes).
#
# Inputs (all produced by the other scripts, all read from chain or explorer):
#   snapshots.json   per-address RBNT, WRBNT and staked amounts at the two snapshot blocks
#   codes.json       per-address "is this a smart contract" (eth_getCode)
#   contracts.json   verified contract names from Routescan
#   labels.json      public names shown in Routescan's address list
#   pools.json       pool balances and totalStake() at the two snapshot blocks
#   q3_txs.json      every transaction in the quarter
#   treasury_table.json  reserved wallets as listed on the DAO treasury page
import csv, json, math, os, collections

S_BLOCK, E_BLOCK = 3025809, 3209414
WEI = 10**18
OUT = "out"; os.makedirs(OUT, exist_ok=True)

snap = json.load(open("snapshots.json"))
codes = json.load(open("codes.json"))
cnames = json.load(open("contracts.json"))
labels = json.load(open("labels.json")) if os.path.exists("labels.json") else {}
pools = json.load(open("pools.json"))
treasury = json.load(open("treasury_table.json"))

WRBNT = "0x6ed1f491e2d31536d6561f6bdb2adc8f092a6076"
POOL = {"nolock": "0x43a1dc107bbb06df266278056055ae7fc5bd2817", "lock365": "0x5e8040e85d0e6363d798a43bea939c026449946d"}
POOL_NAME = {"nolock": "Reddex staking pool (no lock)", "lock365": "Reddex staking pool (365-day lock)"}
RESERVED = {r["address"].lower(): r["allocation"] for r in treasury}
# Contracts are grouped by code hash against verified reference contracts on Routescan:
#   vesting: TokenVestingManager (verified) at 0x5efecd7e24ec14a7cb970700001c7a3ac40a0282
#   bridge:  RBNTNativeOFTAdapter (verified) at 0x020940df9f5e77338a094d55b5b5914122a804a5
#   safe:    the multisig proxy used by the reserved wallets, e.g. TEAM (Locked)
CODE = {"vesting": codes["0x5efecd7e24ec14a7cb970700001c7a3ac40a0282"],
        "bridge": codes["0x020940df9f5e77338a094d55b5b5914122a804a5"],
        "safe": codes["0xbcee2defb7cf136480e3619cf93e8129059977af"]}

# ---- 1. classify every address -------------------------------------------------------------
def category(a):
    if a in RESERVED: return "Redbelly reserved wallets"
    if a == WRBNT: return "Wrapped RBNT contract"
    if a in POOL.values(): return "Reddex staking pools"
    if a == "0x0000000000000000000000000000000000000000": return "Zero address"
    lab = labels.get(a, "")
    if lab and any(w in lab.lower() for w in ("exchange", "binance", "mexc", "bitget", "gate", "kucoin", "bybit", "okx", "kraken", "coinbase", "htx", "bitmart", "lbank", "crypto.com", "swyftx", "coinspot", "btc markets", "independent reserve")):
        return "Labelled exchange wallets"
    h = codes.get(a, "")
    if h == CODE["bridge"]: return "Bridge (RBNT Native OFT Adapter)"
    if h == CODE["vesting"]: return "Token vesting contracts"
    if h == CODE["safe"]: return "Unnamed wallets"   # unnamed multisig wallets (same Safe proxy code as the reserved wallets)
    if h: return "Other smart contracts"
    return "Unnamed wallets"

def amt(a, tag):
    """Economic RBNT held by address a at tag ('start'/'end'), counting each token once:
    native RBNT + WRBNT + RBNT it has staked. The WRBNT contract's own RBNT is excluded (it is
    the backing of everyone's WRBNT) and each pool's RBNT is split into stakes (credited to the
    stakers) and the remainder (kept on the pool as reward funds)."""
    v = snap[a]
    if a == WRBNT: return 0
    if a in POOL.values():
        k = [k for k, p in POOL.items() if p == a][0]
        return int(pools[k]["balance_" + tag]) - int(pools[k]["totalStake_" + tag])
    return int(v["rbnt_" + tag]) + int(v["wrbnt_" + tag]) + int(v["nolock_" + tag]) + int(v["lock365_" + tag])

rows = []
for a in snap:
    rows.append({"address": a, "category": category(a), "start": amt(a, "start"), "end": amt(a, "end"),
                 "staked_start": int(snap[a]["nolock_start"]) + int(snap[a]["lock365_start"]),
                 "staked_end": int(snap[a]["nolock_end"]) + int(snap[a]["lock365_end"])})
by_addr = {r["address"]: r for r in rows}

F = {}  # every figure the report quotes
F["blocks"] = {"start": S_BLOCK, "end": E_BLOCK}

# ---- 2. reconciliation ---------------------------------------------------------------------
for tag in ("start", "end"):
    native_total = sum(int(v["rbnt_" + tag]) for v in snap.values())
    econ_total = sum(r[tag] for r in rows)
    F["native_total_" + tag] = native_total / WEI
    F["economic_total_" + tag] = econ_total / WEI
    F["wrbnt_supply_" + tag] = int(pools["wrbnt"]["totalSupply_" + tag]) / WEI
    F["wrbnt_backing_" + tag] = int(pools["wrbnt"]["balance_" + tag]) / WEI
    F["wrbnt_sum_holders_" + tag] = sum(int(v["wrbnt_" + tag]) for v in snap.values()) / WEI
    for k in POOL:
        F[f"{k}_userinfo_sum_{tag}"] = sum(int(v[k + "_" + tag]) for v in snap.values()) / WEI

# ---- 3. supply map by category -------------------------------------------------------------
cat_order = ["Redbelly reserved wallets", "Reddex staking pools", "Bridge (RBNT Native OFT Adapter)", "Token vesting contracts",
             "Other smart contracts", "Labelled exchange wallets", "Zero address", "Unnamed wallets"]
supply = []
for c in cat_order:
    s = sum(r["start"] for r in rows if r["category"] == c) / WEI
    e = sum(r["end"] for r in rows if r["category"] == c) / WEI
    n_s = sum(1 for r in rows if r["category"] == c and r["start"] > 0)
    n_e = sum(1 for r in rows if r["category"] == c and r["end"] > 0)
    supply.append({"category": c, "start": s, "end": e, "change": e - s, "addresses_start": n_s, "addresses_end": n_e})
# staked RBNT is held by stakers; show it as its own slice of the supply map
staked_s = sum(r["staked_start"] for r in rows) / WEI; staked_e = sum(r["staked_end"] for r in rows) / WEI
F["supply_map"] = supply
F["unnamed_staked_start"] = sum(r["staked_start"] for r in rows if r["category"] == "Unnamed wallets") / WEI
F["unnamed_staked_end"] = sum(r["staked_end"] for r in rows if r["category"] == "Unnamed wallets") / WEI
F["staked_by_category"] = {c: [sum(r["staked_start"] for r in rows if r["category"] == c) / WEI,
                               sum(r["staked_end"] for r in rows if r["category"] == c) / WEI] for c in cat_order}

# ---- 4. concentration among unnamed wallets ------------------------------------------------
HOLDER_MIN = 10 * WEI   # holder = more than 10 RBNT (see method note)
def holders(tag): return sorted((r[tag] for r in rows if r["category"] == "Unnamed wallets" and r[tag] > HOLDER_MIN), reverse=True)
def gini(xs):
    xs = sorted(xs); n = len(xs); t = sum(xs)
    return (2 * sum((i + 1) * x for i, x in enumerate(xs)) / (n * t)) - (n + 1) / n
conc = {}
for tag in ("start", "end"):
    h = holders(tag); tot = sum(h)
    conc[tag] = {"holders": len(h), "total": tot / WEI,
                 "top10_share": sum(h[:10]) / tot, "top50_share": sum(h[:50]) / tot, "top100_share": sum(h[:100]) / tot,
                 "top500_share": sum(h[:500]) / tot, "gini": gini(h),
                 "median": h[len(h) // 2] / WEI}
F["concentration"] = conc

bands = [(10, 1e3, "10 – 1K"), (1e3, 1e4, "1K – 10K"), (1e4, 1e5, "10K – 100K"), (1e5, 1e6, "100K – 1M"), (1e6, 1e7, "1M – 10M"), (1e7, 1e12, "10M +")]
band_rows = []
for lo, hi, lab in bands:
    r_ = {"band": lab}
    for tag in ("start", "end"):
        vals = [r[tag] / WEI for r in rows if r["category"] == "Unnamed wallets" and r[tag] > HOLDER_MIN and lo <= r[tag] / WEI < hi] if lo > 10 else \
               [r[tag] / WEI for r in rows if r["category"] == "Unnamed wallets" and r[tag] > HOLDER_MIN and r[tag] / WEI < hi]
        r_["wallets_" + tag] = len(vals); r_["rbnt_" + tag] = sum(vals)
    band_rows.append(r_)
F["bands"] = band_rows

# ---- 5. behaviour of the largest unnamed holders (cohort fixed at the start) ----------------
ranked = sorted((r for r in rows if r["category"] == "Unnamed wallets" and r["start"] > 0), key=lambda r: -r["start"])
tiers = [(0, 10, "Top 10"), (10, 50, "11 – 50"), (50, 100, "51 – 100"), (100, 500, "101 – 500"), (500, 1000, "501 – 1,000")]
tier_rows = []
for lo, hi, lab in tiers:
    grp = ranked[lo:hi]
    s = sum(r["start"] for r in grp) / WEI; e = sum(r["end"] for r in grp) / WEI
    up = sum(1 for r in grp if r["end"] > r["start"] * 1.01)
    down = sum(1 for r in grp if r["end"] < r["start"] * 0.99)
    out_ = sum(1 for r in grp if r["end"] < WEI)
    flat = len(grp) - up - down
    ss = sum(r["staked_start"] for r in grp) / WEI; se = sum(r["staked_end"] for r in grp) / WEI
    tier_rows.append({"tier": lab, "wallets": len(grp), "start": s, "end": e, "change": e - s, "change_pct": (e - s) / s if s else 0,
                      "grew": up, "shrank": down, "about_same": flat, "emptied": out_, "staked_start": ss, "staked_end": se})
F["tiers"] = tier_rows
top100_start = {r["address"] for r in ranked[:100]}
ranked_end = sorted((r for r in rows if r["category"] == "Unnamed wallets" and r["end"] > 0), key=lambda r: -r["end"])
top100_end = {r["address"] for r in ranked_end[:100]}
F["top100_turnover"] = {"stayed": len(top100_start & top100_end), "new_entrants": len(top100_end - top100_start)}

# ---- 6. staking ----------------------------------------------------------------------------
stk = {}
for k in POOL:
    p = pools[k]
    stk[k] = {"name": POOL_NAME[k],
              "balance_start": int(p["balance_start"]) / WEI, "balance_end": int(p["balance_end"]) / WEI,
              "staked_start": int(p["totalStake_start"]) / WEI, "staked_end": int(p["totalStake_end"]) / WEI,
              "stakers_start": sum(1 for v in snap.values() if int(v[k + "_start"]) > 0),
              "stakers_end": sum(1 for v in snap.values() if int(v[k + "_end"]) > 0)}
    stk[k]["reward_funds_start"] = stk[k]["balance_start"] - stk[k]["staked_start"]
    stk[k]["reward_funds_end"] = stk[k]["balance_end"] - stk[k]["staked_end"]
F["staking"] = stk
F["stakers_any_start"] = sum(1 for v in snap.values() if int(v["nolock_start"]) + int(v["lock365_start"]) > 0)
F["stakers_any_end"] = sum(1 for v in snap.values() if int(v["nolock_end"]) + int(v["lock365_end"]) > 0)

# ---- 7. named wallets: reserved wallets, bridge -------------------------------------------
# Reserved wallets are multisig contracts, so their transfers happen inside the multisig's own
# execution and appear as balance changes, not as transactions they send. changes_locked.json holds
# every block in the quarter where one of them changed balance (found by binary search on balance).
changes = json.load(open("changes_locked.json"))
tx = json.load(open("q3_txs.json"))
named = []
for a, alloc in RESERVED.items():
    v = snap[a]
    s = int(v["rbnt_start"]) + int(v["wrbnt_start"]); e = int(v["rbnt_end"]) + int(v["wrbnt_end"])
    named.append({"wallet": alloc, "address": a, "start": s / WEI, "end": e / WEI, "change": (e - s) / WEI,
                  "native_moves": [{"block": b, "amount": d / WEI} for b, d in changes.get(a, [])],
                  "txs_sent": sum(1 for t in tx if t[3] == a)})
F["reserved"] = named

# Ecosystem (Unlocked) is an ordinary wallet that sends its own transactions: break its outflows
# down by destination group. WRBNT movements come from the Transfer events in its receipts.
ECO = "0x415cad8fc89f75a63c5b830e06460eecde083c9f"
rc = {r["transactionHash"]: r for r in json.load(open("receipts_eco_unlocked.json"))}
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
def group(a):
    if a == WRBNT: return "Wrapped into WRBNT"
    if a in POOL.values(): return "Reddex staking pools (reward funds)"
    if a in RESERVED: return "Other reserved wallets"
    c = category(a) if a in snap else ("Other smart contracts" if codes.get(a) else "Unnamed wallets")
    return c
eco_out = collections.defaultdict(lambda: {"rbnt": 0, "txs": 0, "addresses": set()})
gas = 0
for t in tx:
    if t[3] != ECO: continue
    r = rc[t[2]]
    gas += int(r["gasUsed"], 16) * int(r.get("effectiveGasPrice", "0x0"), 16)
    if r["status"] == "0x1" and t[5] != "0":
        g = eco_out[group(t[4])]; g["rbnt"] += int(t[5]); g["txs"] += 1; g["addresses"].add(t[4])
wr_out = collections.defaultdict(lambda: {"wrbnt": 0, "addresses": set()}); wr_in = collections.defaultdict(lambda: {"wrbnt": 0, "addresses": set()})
for r in rc.values():
    for l in r["logs"]:
        if l["address"] == WRBNT and l["topics"][0] == TRANSFER and len(l["topics"]) == 3:
            fr, to = "0x" + l["topics"][1][26:], "0x" + l["topics"][2][26:]
            if fr == ECO: d = wr_out[group(to)]; d["wrbnt"] += int(l["data"], 16); d["addresses"].add(to)
            elif to == ECO: d = wr_in[group(fr)]; d["wrbnt"] += int(l["data"], 16); d["addresses"].add(fr)
F["eco_unlocked"] = {
    "rbnt_out": [{"to": k, "rbnt": v["rbnt"] / WEI, "txs": v["txs"], "addresses": len(v["addresses"])} for k, v in sorted(eco_out.items(), key=lambda x: -x[1]["rbnt"])],
    "wrbnt_out": [{"to": k, "wrbnt": v["wrbnt"] / WEI, "addresses": len(v["addresses"])} for k, v in wr_out.items()],
    "wrbnt_in": [{"from": k, "wrbnt": v["wrbnt"] / WEI, "addresses": len(v["addresses"])} for k, v in wr_in.items()],
    "gas_fees": gas / WEI, "txs_sent": sum(1 for t in tx if t[3] == ECO)}
BR = "0x020940df9f5e77338a094d55b5b5914122a804a5"
F["bridge"] = {"start": int(snap[BR]["rbnt_start"]) / WEI, "end": int(snap[BR]["rbnt_end"]) / WEI,
               "txs_in": sum(1 for t in tx if t[4] == BR), "senders": len({t[3] for t in tx if t[4] == BR})}
F["pool_flows"] = json.load(open("pool_flows.json"))
F["exchange_labels_found"] = sorted({labels[a] for a in labels if category(a) == "Labelled exchange wallets"})

# ---- 8. write outputs ----------------------------------------------------------------------
def wcsv(name, recs, cols):
    with open(os.path.join(OUT, name), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader()
        for r in recs: w.writerow({k: (round(v, 6) if isinstance(v, float) else v) for k, v in r.items()})
wcsv("supply_by_category.csv", supply, ["category", "start", "end", "change", "addresses_start", "addresses_end"])
wcsv("holder_size_bands.csv", band_rows, ["band", "wallets_start", "wallets_end", "rbnt_start", "rbnt_end"])
wcsv("largest_holder_tiers.csv", tier_rows, ["tier", "wallets", "start", "end", "change", "change_pct", "grew", "shrank", "about_same", "emptied", "staked_start", "staked_end"])
conc_rows = [{"measure": k, "start": C_["start"][k], "end": C_["end"][k]} for C_ in [F["concentration"]] for k in F["concentration"]["start"]]
wcsv("concentration.csv", conc_rows, ["measure", "start", "end"])
pool_rows = []
for k in POOL:
    d = dict(F["staking"][k]); d.update({kk: vv for kk, vv in F["pool_flows"][k].items() if kk != "selectors"}); d["address"] = POOL[k]; d["pool"] = d.pop("name")
    pool_rows.append(d)
wcsv("staking_pools.csv", pool_rows, ["pool", "address", "balance_start", "staked_start", "reward_funds_start", "balance_end", "staked_end", "reward_funds_end",
                                      "stakers_start", "stakers_end", "stake_txs", "stakers_who_staked", "staked_gross", "unstaked_gross", "unstake_txs", "claim_txs",
                                      "reward_funding", "reward_funding_from_reserved", "rewards_paid_est"])
wcsv("reserved_wallets.csv", [dict(r, moves="; ".join(f"block {m['block']}: {m['amount']:+,.0f}" for m in r["native_moves"])) for r in named],
     ["wallet", "address", "start", "end", "change", "txs_sent", "moves"])
eco_rows = [{"direction": "out", "asset": "RBNT", "group": r["to"], "amount": r["rbnt"], "txs": r["txs"], "addresses": r["addresses"]} for r in F["eco_unlocked"]["rbnt_out"]] + \
           [{"direction": "out", "asset": "WRBNT", "group": r["to"], "amount": r["wrbnt"], "addresses": r["addresses"]} for r in F["eco_unlocked"]["wrbnt_out"]] + \
           [{"direction": "in", "asset": "WRBNT", "group": r["from"], "amount": r["wrbnt"], "addresses": r["addresses"]} for r in F["eco_unlocked"]["wrbnt_in"]] + \
           [{"direction": "out", "asset": "RBNT", "group": "Transaction fees", "amount": F["eco_unlocked"]["gas_fees"], "txs": F["eco_unlocked"]["txs_sent"]}]
wcsv("eco_unlocked_flows.csv", eco_rows, ["direction", "asset", "group", "amount", "txs", "addresses"])
# per-address file: unnamed wallets appear only as anonymous rank rows (no addresses)
named_set = set(RESERVED) | {WRBNT} | set(POOL.values())
with open(os.path.join(OUT, "holders_ranked_anonymous.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["rank_on_1_jul", "holdings_1_jul", "holdings_30_sep", "staked_1_jul", "staked_30_sep"])
    for i, r in enumerate(ranked[:1000]): w.writerow([i + 1, round(r["start"] / WEI, 6), round(r["end"] / WEI, 6), round(r["staked_start"] / WEI, 6), round(r["staked_end"] / WEI, 6)])

# ---- 9. checks -----------------------------------------------------------------------------
fees = json.load(open("fees_q3.json"))
F["fees_q3"] = fees["base_fees_rbnt"]
F["universe_size"] = len(json.load(open("universe_c.json"))) if os.path.exists("universe_c.json") else len(snap)
F["addresses_nonzero"] = sum(1 for v in snap.values() if any(int(x) for x in v.values()))
def ok(b): return "PASS" if b else "FAIL"
checks = []
for tag, blk in (("start", S_BLOCK), ("end", E_BLOCK)):
    checks.append([f"WRBNT contract RBNT = WRBNT totalSupply (block {blk})", ok(pools["wrbnt"]["balance_" + tag] == pools["wrbnt"]["totalSupply_" + tag]),
                   f'{int(pools["wrbnt"]["balance_" + tag]) / WEI:,.6f} = {int(pools["wrbnt"]["totalSupply_" + tag]) / WEI:,.6f}'])
    s_wr = sum(int(v["wrbnt_" + tag]) for v in snap.values())
    checks.append([f"Sum of WRBNT balances read = totalSupply (block {blk})", ok(str(s_wr) == pools["wrbnt"]["totalSupply_" + tag]), f"{s_wr / WEI:,.6f}"])
    for k in POOL:
        s_p = sum(int(v[k + "_" + tag]) for v in snap.values())
        checks.append([f"Sum of stakers' userInfo = {POOL_NAME[k]} totalStake() (block {blk})", ok(str(s_p) == pools[k]["totalStake_" + tag]), f"{s_p / WEI:,.6f}"])
    checks.append([f"Holdings counted once: sum of holdings = sum of native RBNT balances (block {blk})",
                   ok(sum(r[tag] for r in rows) == sum(int(v["rbnt_" + tag]) for v in snap.values())), f'{sum(r[tag] for r in rows) / WEI:,.6f}'])
eco_s = int(snap[ECO]["rbnt_start"]); eco_e = int(snap[ECO]["rbnt_end"])
eco_net = sum(int(t[5]) for t in tx if t[3] == ECO and rc[t[2]]["status"] == "0x1")
eco_in_top = sum(int(t[5]) for t in tx if t[4] == ECO)
checks.append(["Ecosystem (Unlocked): start − sent − fees + received = end (RBNT)", ok(eco_s - eco_net - gas + eco_in_top == eco_e),
               f"{eco_s / WEI:,.6f} − {eco_net / WEI:,.6f} − {gas / WEI:,.6f} + {eco_in_top / WEI:,.6f} = {eco_e / WEI:,.6f}"])
d_total = F["economic_total_start"] - F["economic_total_end"]
F["unattributed_q3"] = F["fees_q3"] - d_total
checks.append(["Fall in RBNT read over the quarter vs base fees burned in the quarter", "INFO",
               f"fall {d_total:,.2f}; fees burned {F['fees_q3']:,.2f}; difference {F['unattributed_q3']:,.2f} RBNT moved in from addresses this method does not reach"])
if os.path.exists("fees_to_start.json"):
    burned = json.load(open("fees_to_start.json"))["base_fees_rbnt"]
    expected = 10_000_000_000 - burned
    F["burned_to_start"] = burned; F["expected_supply_start"] = expected
    F["coverage_start"] = F["native_total_start"] / expected
    checks.append(["RBNT read at block 3025809 vs 10,000,000,000 allocated minus all base fees burned since launch", "INFO",
                   f"read {F['native_total_start']:,.2f}; expected {expected:,.2f} (burned {burned:,.2f}); coverage {100 * F['coverage_start']:.3f}%"])
F["checks_rows"] = [[c[0], f"<b>{c[1]}</b> · <span class=mono>{c[2]}</span>"] for c in checks]
with open(os.path.join(OUT, "checks.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["check", "result", "detail"]); w.writerows(checks)
json.dump(F, open(os.path.join(OUT, "figures.json"), "w"), indent=1)
print(json.dumps({k: F[k] for k in F if k not in ("supply_map", "bands", "tiers")}, indent=1)[:4000])
for s in supply: print(s)
for t in tier_rows: print(t)
for b in band_rows: print(b)
