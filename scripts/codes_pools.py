# codes.json: for each address, the keccak hash of its code at the end block ("" = ordinary wallet).
# Identical code hashes let us group copies of a verified contract (e.g. the token vesting contract).
# pools.json: balances and totalStake() of both pools, and WRBNT supply/backing, at both snapshot blocks.
import json, sys
from Crypto.Hash import keccak
from rpc import batch
S, E = 3025809, 3209414
snap = json.load(open("snapshots.json"))
try: codes = json.load(open("codes.json"))
except Exception: codes = {}
todo = [a for a in snap if a not in codes]
for i in range(0, len(todo), 100):
    for a, c in zip(todo[i:i + 100], batch([("eth_getCode", [a, hex(E)]) for a in todo[i:i + 100]])):
        codes[a] = "" if c in ("0x", "0x0") else keccak.new(digest_bits=256, data=bytes.fromhex(c[2:])).hexdigest()
json.dump(codes, open("codes.json", "w"))
P = {"nolock": "0x43a1dc107bbb06df266278056055ae7fc5bd2817", "lock365": "0x5e8040e85d0e6363d798a43bea939c026449946d"}
W = "0x6ed1f491e2d31536d6561f6bdb2adc8f092a6076"
out = {}
for k, a in list(P.items()) + [("wrbnt", W)]:
    sel = "0x18160ddd" if k == "wrbnt" else "0x8b0e9f3f"   # totalSupply() / totalStake()
    key = "totalSupply" if k == "wrbnt" else "totalStake"
    r = batch([("eth_getBalance", [a, hex(S)]), ("eth_getBalance", [a, hex(E)]),
               ("eth_call", [{"to": a, "data": sel}, hex(S)]), ("eth_call", [{"to": a, "data": sel}, hex(E)])])
    r = [str(int(x, 16)) for x in r]
    out[k] = {"address": a, "balance_start": r[0], "balance_end": r[1], key + "_start": r[2], key + "_end": r[3]}
json.dump(out, open("pools.json", "w"), indent=1)
print(len(codes), sum(1 for v in codes.values() if v), "contracts")
