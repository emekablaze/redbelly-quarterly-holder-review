# Scan every block in [START, END] and collect every address a transaction touches or names:
#   - sender and recipient
#   - every ABI-encoded address argument in the calldata (32-byte word = 12 zero bytes + address)
#     e.g. the account-permission registry, batch payouts, vesting grants, bridge messages
#   - addresses passed as `bytes` (length 20, left-aligned) or as text ("0x…"), as bridges do
#   - recipients packed inside Safe MultiSend batches (multiSend(bytes), selector 0x8d80ff0a)
# Writes one file of unique addresses per 10,000 blocks to DIR (resumable).
import json, os, re, sys
from concurrent.futures import ThreadPoolExecutor
from rpc import batch, TooLarge

START, END, DIR = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
os.makedirs(DIR, exist_ok=True)
MULTISEND = "8d80ff0a"

def abi_addrs(hexdata):
    out = set()
    for i in range(0, len(hexdata) - 63, 64):
        w = hexdata[i:i + 64]
        if w.startswith("0" * 24):
            a = w[24:]
            if len(a.lstrip("0")) >= 30:          # skip small integers that look like padded words
                out.add("0x" + a)
    return out

def bytes20_addrs(hexdata):
    """Addresses passed as `bytes` (common in bridge messages): a length word of 20 (0x14) followed by
    the 20 address bytes left-aligned in the next word."""
    out = set()
    for i in range(0, len(hexdata) - 127, 64):
        if hexdata[i:i + 64] == LEN20:
            w = hexdata[i + 64:i + 128]
            if w[40:] == "0" * 24 and len(w[:40].lstrip("0")) >= 30:
                out.add("0x" + w[:40])
    return out
LEN20 = "0" * 62 + "14"

def ascii_addrs(hexdata):
    """Addresses passed as text, e.g. the string "0x740a…" (hex of ASCII '0x' + 40 hex characters)."""
    out = set()
    for m in ASCII.findall(hexdata):
        try: out.add("0x" + bytes.fromhex(m).decode().lower())
        except ValueError: pass
    return out
ASCII = re.compile(r"3078((?:3[0-9]|4[1-6]|6[1-6]){40})")

def multisend_addrs(hexdata):
    """Decode packed MultiSend payloads: op(1) to(20) value(32) len(32) data(len)."""
    out = set(); k = hexdata.find(MULTISEND)
    while k != -1:
        try:
            p = k + 8 + 64                                   # skip selector and bytes offset
            n = int(hexdata[p:p + 64], 16) * 2; p += 64      # payload length in hex chars
            end = p + n
            while p < end:
                out.add("0x" + hexdata[p + 2:p + 42])
                ln = int(hexdata[p + 106:p + 170], 16) * 2
                p += 170 + ln
        except ValueError:
            pass
        k = hexdata.find(MULTISEND, k + 8)
    return out

def blocks(lo, hi):
    try:
        res = batch([("eth_getBlockByNumber", [hex(n), True]) for n in range(lo, hi + 1)])
    except TooLarge:
        if lo == hi: raise
        mid = (lo + hi) // 2
        return blocks(lo, mid) | blocks(mid + 1, hi)
    out = set()
    for b in res:
        for t in b["transactions"]:
            out.add(t["from"].lower())
            if t["to"]: out.add(t["to"].lower())
            data = t["input"][10:].lower()
            if data:
                out |= abi_addrs(data)
                if LEN20 in data: out |= bytes20_addrs(data)
                if "3078" in data: out |= ascii_addrs(data)
                if MULTISEND in data: out |= multisend_addrs(data)
    return out

for c in range(START, END + 1, 10000):
    f = os.path.join(DIR, f"{c}.json")
    if os.path.exists(f): continue
    hi = min(c + 9999, END)
    with ThreadPoolExecutor(4) as ex:
        parts = list(ex.map(lambda lo: blocks(lo, min(lo + 99, hi)), range(c, hi + 1, 100)))
    s = set().union(*parts); s.discard("0x" + "0" * 40)
    json.dump(sorted(s), open(f + ".tmp", "w")); os.replace(f + ".tmp", f)
    print("done", c, len(s), file=sys.stderr, flush=True)
