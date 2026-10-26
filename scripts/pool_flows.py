# Gross staking flows per pool in the quarter, from every transaction sent to the pool and its receipt.
#   stake()                -> RBNT staked (msg.value)
#   plain transfer (no data) -> RBNT added to the pool's reward funds (receive())
#   unstaked = staked - change in totalStake;  rewards paid = funding - change in reward funds
import json, collections
from rpc import batch
POOL = {"nolock": "0x43a1dc107bbb06df266278056055ae7fc5bd2817", "lock365": "0x5e8040e85d0e6363d798a43bea939c026449946d"}
RESERVED = {r["address"].lower(): r["allocation"] for r in json.load(open("treasury_table.json"))}
tx = json.load(open("q3_txs.json")); pools = json.load(open("pools.json"))
out = {}
for k, p in POOL.items():
    mine = [t for t in tx if t[4] == p]
    rc = []
    for i in range(0, len(mine), 50): rc += batch([("eth_getTransactionReceipt", [t[2]]) for t in mine[i:i + 50]])
    ok = {r["transactionHash"]: r["status"] == "0x1" for r in rc}
    st = [t for t in mine if t[6] == "0x3a4b66f1" and ok[t[2]] and t[5] != "0"]
    fund = [t for t in mine if t[6] == "0x" and ok[t[2]] and t[5] != "0"]
    by_sel = collections.Counter(t[6] for t in mine if ok[t[2]])
    staked = sum(int(t[5]) for t in st) / 1e18
    funding = sum(int(t[5]) for t in fund) / 1e18
    d_total = (int(pools[k]["totalStake_end"]) - int(pools[k]["totalStake_start"])) / 1e18
    d_funds = ((int(pools[k]["balance_end"]) - int(pools[k]["totalStake_end"])) - (int(pools[k]["balance_start"]) - int(pools[k]["totalStake_start"]))) / 1e18
    out[k] = {"stake_txs": len(st), "stakers_who_staked": len({t[3] for t in st}), "staked_gross": staked,
              "unstaked_gross": staked - d_total, "unstake_txs": by_sel.get("0xc2a672e0", 0), "claim_txs": by_sel.get("0xb88a802f", 0),
              "reward_funding": funding, "reward_funding_from_reserved": sum(int(t[5]) for t in fund if t[3] in RESERVED) / 1e18,
              "reward_funding_txs": len(fund), "rewards_paid_est": funding - d_funds, "failed_txs": sum(1 for v in ok.values() if not v),
              "selectors": dict(by_sel)}
json.dump(out, open("pool_flows.json", "w"), indent=1)
print(json.dumps(out, indent=1))
