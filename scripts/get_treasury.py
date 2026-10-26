# Read the reserved-wallet table from the DAO treasury page.
# The page is a static Next.js export: the table is embedded as JSON in the treasury page's JS chunk.
import json, re, urllib.request
BASE = "https://redbellydao.network"
html = urllib.request.urlopen(BASE + "/treasury/").read().decode()
chunk = re.search(r'src="(/_next/static/chunks/pages/treasury-[^"]+\.js)"', html).group(1)
js = urllib.request.urlopen(BASE + chunk).read().decode()
start = js.index("JSON.parse('") + len("JSON.parse('")
table = json.loads(js[start:js.index("')", start)])
json.dump(table, open("treasury_table.json", "w"), indent=1)
for r in table: print(f'{r["allocation"]:26s} {r["address"]}  original allocation {r["qty"]}')
