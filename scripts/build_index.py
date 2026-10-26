# Landing page (index.html) for the repository root, so a static host such as Vercel has a homepage.
# Numbers are read from out/figures.json.
import base64, json, os
F = json.load(open("out/figures.json"))
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
LOGO = base64.b64encode(open(os.path.join(ASSETS, "dao-logo-on-dark.png"), "rb").read()).decode()
st = F["staking"]; cs, ce = F["concentration"]["start"], F["concentration"]["end"]
sup = {r["category"]: r for r in F["supply_map"]}; t = F["tiers"][:3]
ss = st["nolock"]["staked_start"] + st["lock365"]["staked_start"]; se = st["nolock"]["staked_end"] + st["lock365"]["staked_end"]
tiles = [("Staked in Reddex pools", f"{se/1e6:,.1f}M", f"from {ss/1e6:,.1f}M on 1 Jul"),
         ("Held by unnamed wallets", f"{sup['Unnamed wallets']['end']/1e6:,.1f}M", f"from {sup['Unnamed wallets']['start']/1e6:,.1f}M"),
         ("Top 10 unnamed holders' share", f"{100*ce['top10_share']:.1f}%", f"from {100*cs['top10_share']:.1f}%"),
         ("Top 100 wallets: grew / same / shrank", f"{sum(x['grew'] for x in t)} / {sum(x['about_same'] for x in t)} / {sum(x['shrank'] for x in t)}", "ranked on 1 Jul")]
links = [("Read the report", "report/RBNT-Holder-Report-Q3-2026.html", "Web version, with charts", True),
         ("Download PDF", "report/RBNT-Holder-Report-Q3-2026.pdf", "A4, 14 pages", False),
         ("Community summary", "community/community-summary.md", "X thread + short version", False),
         ("Method and sources", "METHOD.md", "How every number was produced", False),
         ("Data (CSV)", "data/README.md", "The data behind every chart", False),
         ("Checks", "data/checks.csv", "Reconciliation checks", False)]
html = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>RBNT Holder Report Q3 2026</title>
<meta name="description" content="Quarterly on-chain report on how RBNT holders behaved in Q3 2026: accumulation, selling, staking and concentration.">
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;600;700&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">
<style>
:root{{--red:#EF5350;--red-text:#ffb3ae;--base:#0c1317;--deep:#0a1014;--slate:#141f26;--steel:#1d3140;--edge:#263641;--text:#f1f5f8;--muted:#8fa1ad}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--deep);color:var(--text);font:16px/1.5 'Be Vietnam Pro',system-ui,sans-serif}}
.wrap{{max-width:1080px;margin:0 auto;padding:48px 16px 64px}}
img{{height:72px;width:auto}}.eyebrow{{margin-top:40px;font-size:12px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--red-text)}}
h1{{font-size:clamp(32px,6vw,48px);line-height:1.1;letter-spacing:-.02em;margin:8px 0 12px}}.sub{{color:var(--muted);font-size:18px;max-width:680px;margin:0}}
.mono{{font-family:'JetBrains Mono',ui-monospace,monospace;font-size:14px;letter-spacing:.05em}}
.meta{{margin:16px 0 0;color:var(--muted)}}
.tiles{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin:40px 0}}
.tile{{background:var(--steel);border:1px solid var(--edge);border-radius:8px;padding:16px}}
.tl{{font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}}.tv{{font-size:32px;font-weight:700;margin:4px 0}}.td{{font-size:14px;color:#c2ced6}}
.links{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px}}
a.card{{display:block;background:var(--slate);border:1px solid var(--edge);border-radius:8px;padding:16px;color:var(--text);text-decoration:none}}
a.card:hover{{border-color:var(--red)}}a.card b{{display:block;font-weight:600}}a.card span{{color:var(--muted);font-size:14px}}
a.primary{{background:var(--red);border-color:var(--red)}}a.primary span{{color:#fff}}
.note{{margin-top:40px;border-top:1px solid var(--edge);padding-top:16px;color:var(--muted);font-size:14px;max-width:720px}}
</style></head><body><div class="wrap">
<img src="data:image/png;base64,{LOGO}" alt="Redbelly DAO">
<div class="eyebrow">Quarterly on-chain holder report · Edition 1</div>
<h1>RBNT holders in Q3 2026</h1>
<p class="sub">How RBNT holders behaved between 1 July and 30 September 2026: accumulation, selling, staking and how concentrated holdings are.</p>
<p class="meta">Snapshot blocks <span class="mono">3025809</span> → <span class="mono">3209414</span> · Redbelly mainnet (chain ID 151)</p>
<div class="tiles">{"".join(f'<div class="tile"><div class="tl">{a}</div><div class="tv">{b}</div><div class="td">{c}</div></div>' for a, b, c in tiles)}</div>
<div class="links">{"".join(f'<a class="card{" primary" if p else ""}" href="{h}"><b>{a}</b><span>{d}</span></a>' for a, h, d, p in links)}</div>
<p class="note">Facts only: this report describes what happened on the chain. It does not predict prices and it is not investment advice. Only publicly named wallets are named, and every other wallet appears only in groups.</p>
</div></body></html>'''
open("index.html", "w").write(html); print("index.html", len(html))
