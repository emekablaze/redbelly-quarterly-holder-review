# Page through Routescan's native-balance address list (largest first), saving every page,
# and stop once balances fall to the cutoff (default 10 RBNT). Backs off on HTTP 429.
import json, sys, time, urllib.request
base = "https://api.routescan.io"
path, out = sys.argv[1], sys.argv[2]
cutoff = int(float(sys.argv[3]) * 10**18) if len(sys.argv) > 3 else 10 * 10**18
items, url, n = [], base + path, 0
while url:
    for attempt in range(30):
        try:
            with urllib.request.urlopen(url, timeout=60) as r: d = json.load(r); break
        except Exception as e:
            print("retry", attempt, e, file=sys.stderr, flush=True); time.sleep(min(10 * (attempt + 1), 120))
    else:
        sys.exit("gave up")
    page = d.get("items", []); items += page; n += 1
    json.dump({"fetched_pages": n, "items": items}, open(out, "w"))
    if page and int(float(page[-1]["balance"])) <= cutoff: break
    nxt = d.get("link", {}).get("next"); url = base + nxt if nxt else None
    if n % 20 == 0: print(n, len(items), page[-1]["balance"], file=sys.stderr, flush=True)
    time.sleep(0.7)
print("pages", n, "items", len(items), "finished_at_utc", time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
