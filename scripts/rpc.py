import json, time, urllib.request
class TooLarge(Exception): pass
RPC = "https://governors.mainnet.redbelly.network"
def batch(calls, tries=8):
    payload = [{"jsonrpc": "2.0", "id": i, "method": m, "params": p} for i, (m, p) in enumerate(calls)]
    data = json.dumps(payload).encode()
    for a in range(tries):
        try:
            req = urllib.request.Request(RPC, data=data, headers={"content-type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as r:
                res = json.load(r)
            res = sorted(res, key=lambda x: x["id"])
            errs = [x["error"] for x in res if "error" in x]
            if errs and "too large" in str(errs[0]["message"]):
                raise TooLarge(errs[0]["message"])   # not worth retrying: caller should split the request
            if errs:
                raise RuntimeError(str(errs[:1]))
            return [x["result"] for x in res]
        except TooLarge:
            raise
        except Exception as e:
            last = e; time.sleep(min(2 ** a, 30))
    raise last
def call(m, p): return batch([(m, p)])[0]
