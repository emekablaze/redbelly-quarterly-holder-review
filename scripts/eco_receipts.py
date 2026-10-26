# Receipts for every transaction Ecosystem (Unlocked) sent in the quarter (for gas, status and WRBNT Transfer events).
import json
from rpc import batch
ECO = "0x415cad8fc89f75a63c5b830e06460eecde083c9f"
hs = [t[2] for t in json.load(open("q3_txs.json")) if t[3] == ECO]
rc = []
for i in range(0, len(hs), 50): rc += batch([("eth_getTransactionReceipt", [h]) for h in hs[i:i + 50]])
json.dump(rc, open("receipts_eco_unlocked.json", "w"))
print("receipts", len(rc))
