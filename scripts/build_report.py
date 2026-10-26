# Build the report (HTML, then PDF via Chromium) from out/figures.json.
# Every number in the text is read from figures.json, so the report cannot drift from the data.
import base64, json, os, datetime
from charts import paired_hbar, diverging_hbar, stacked_share, columns, fmt_m, RED, SLATE

F = json.load(open("out/figures.json"))
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "site_src", "pdf")   # brand fonts (embedded) and full-size logo
FONTS = open(os.path.join(ASSETS, "fonts_inline.css")).read()
LOGO_DARK = base64.b64encode(open(os.path.join(ASSETS, "dao-logo-on-dark.png"), "rb").read()).decode()

def M(v, d=1):  # millions
    return f"{v/1e6:,.{d}f}M"
def N(v): return f"{v:,.0f}"
def P(v, d=1): return f"{100*v:.{d}f}%"
def PP(a, b, d=1):  # percentage-point change
    x = 100 * (b - a); return ("+" if x >= 0 else "−") + f"{abs(x):.{d}f} pts"
def chg(v, d=1):
    return ("+" if v >= 0 else "−") + f"{abs(v)/1e6:,.{d}f}M"
def pct(a, b): return (b - a) / a if a else 0

sup = {r["category"]: r for r in F["supply_map"]}
C = F["concentration"]; cs, ce = C["start"], C["end"]
stk = F["staking"]; pf = F["pool_flows"]
staked_s = stk["nolock"]["staked_start"] + stk["lock365"]["staked_start"]
staked_e = stk["nolock"]["staked_end"] + stk["lock365"]["staked_end"]
supply_total = F["economic_total_end"]
res = {r["wallet"]: r for r in F["reserved"]}
eco = F["eco_unlocked"]; br = F["bridge"]
tiers = F["tiers"]
unnamed = sup["Unnamed wallets"]
unnamed_staked_s = F["unnamed_staked_start"]; unnamed_staked_e = F["unnamed_staked_end"]

LABEL = {"Reddex staking pools": "Reddex pools: reward funds (stakes are counted with stakers)"}
# ---------------- charts ----------------
seg = [("Reserved wallets", "#1d3140"), ("Vesting contracts", "#3F4C6B"), ("Other contracts", SLATE),
       ("Bridge", "#8fa1ad"), ("Pool reward funds", "#C3CDD4"), ("Unnamed wallets", RED)]
def segvals(tag):
    g = lambda c: sup[c][tag]
    return {"Reserved wallets": g("Redbelly reserved wallets"), "Vesting contracts": g("Token vesting contracts"),
            "Other contracts": g("Other smart contracts"), "Bridge": g("Bridge (RBNT Native OFT Adapter)"),
            "Pool reward funds": g("Reddex staking pools"), "Unnamed wallets": g("Unnamed wallets") + g("Labelled exchange wallets")}
chart_supply = stacked_share([("1 Jul", segvals("start")), ("30 Sep", segvals("end"))], seg, "c1t")

chart_conc = columns(["Top 10", "Top 50", "Top 100", "Top 500"],
                     [("1 Jul 2026", SLATE, [100 * cs[k] for k in ("top10_share", "top50_share", "top100_share", "top500_share")]),
                      ("30 Sep 2026", RED, [100 * ce[k] for k in ("top10_share", "top50_share", "top100_share", "top500_share")])],
                     "c2t", height=200, unit_fmt=lambda v: f"{v:.1f}%")
bands = F["bands"]
chart_bands = columns([b["band"] for b in bands],
                      [("1 Jul 2026", SLATE, [b["wallets_start"] for b in bands]), ("30 Sep 2026", RED, [b["wallets_end"] for b in bands])],
                      "c3t", height=200)
chart_tiers = stacked_share([(t["tier"], {"Grew": t["grew"], "About the same": t["about_same"], "Shrank": t["shrank"]}) for t in tiers],
                            [("Grew", RED), ("About the same", "#C3CDD4"), ("Shrank", SLATE)], "c4t", bh=22, row_gap=14)
chart_tier_chg = diverging_hbar([(t["tier"], t["change"]) for t in tiers], "c5t")
chart_staking = paired_hbar([("No-lock pool: staked", stk["nolock"]["staked_start"], stk["nolock"]["staked_end"]),
                             ("365-day pool: staked", stk["lock365"]["staked_start"], stk["lock365"]["staked_end"])], "c6t")
res_order = ["Ecosystem (Locked)", "Ecosystem 2 (Unlocked)", "Investors", "Ecosystem (Unlocked)", "Governance (Locked)",
             "Governance (Unlocked)", "TEAM (Locked)", "Reserve", "USYD/CSIRO (Locked)"]
chart_res = diverging_hbar([(w, res[w]["change"]) for w in res_order], "c7t")

def table(head, rows, cls=""):
    h = "".join(f"<th>{x}</th>" for x in head)
    b = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<table class="{cls}"><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>'

def figure(num, title, svg, caption, source):
    return f'''<figure><figcaption class="ft" id="c{num}t"><span class="fnum">Chart {num}</span> {title}</figcaption>
{svg}<p class="cap">{caption}</p><p class="src">Source: {source}</p></figure>'''

SRC_SNAP = "Redbelly mainnet RPC, balances at blocks <span class=mono>3025809</span> (30 Jun 2026 23:57 UTC) and <span class=mono>3209414</span> (30 Sep 2026 23:57 UTC)"

# ---------------- text ----------------
top_tier = tiers[0]; t2 = tiers[1]; t3 = tiers[2]
grew100 = sum(t["grew"] for t in tiers[:3]); shrank100 = sum(t["shrank"] for t in tiers[:3])
same100 = sum(t["about_same"] for t in tiers[:3])
chg100 = sum(t["change"] for t in tiers[:3]); s100 = sum(t["start"] for t in tiers[:3])

glance = [
    ("Staked in Reddex pools", M(staked_e), f"{chg(staked_e - staked_s)} ({P(pct(staked_s, staked_e))}) over the quarter"),
    ("Held by unnamed wallets", M(unnamed["end"]), f"{chg(unnamed['end'] - unnamed['start'])} over the quarter"),
    ("Share held by the top 10 unnamed holders", P(ce["top10_share"]), f"{PP(cs['top10_share'], ce['top10_share'])} since 1 July"),
    ("Unnamed holders above 10 RBNT", N(ce["holders"]), f"{'+' if ce['holders'] >= cs['holders'] else '−'}{abs(ce['holders'] - cs['holders']):,} since 1 July"),
]
tiles = "".join(f'<div class="tile"><div class="tl">{a}</div><div class="tv">{b}</div><div class="td">{c}</div></div>' for a, b, c in glance)

html = f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>RBNT Holder Report Q3 2026</title>
<style>
{FONTS}
:root {{ --red:#EF5350; --red-text:#B3272A; --ink:#0F1A22; --muted:#596975; --line:#DAE1E7; --page:#EDF1F4; --card:#FFFFFF;
        --steel:#1d3140; --slate:#141f26; --base:#0c1317; --on-dark:#f1f5f8; --on-dark-muted:#8fa1ad; }}
@page {{ size: A4; margin: 16mm 16mm 18mm 16mm; }}
@page :first {{ margin: 0; }}
* {{ box-sizing: border-box; }}
html, body {{ margin:0; background: var(--card); color: var(--ink); font-family: 'Be Vietnam Pro', system-ui, sans-serif; font-size: 10.5pt; line-height: 1.55; }}
.mono {{ font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: .92em; }}
h1, h2, h3 {{ font-weight: 700; letter-spacing: -0.01em; line-height: 1.2; }}
h2 {{ font-size: 19pt; margin: 0 0 4pt; }}
h2 .k {{ display:block; font-size: 8pt; font-weight:700; letter-spacing: .1em; text-transform: uppercase; color: var(--red-text); margin-bottom: 6pt; }}
h3 {{ font-size: 12pt; margin: 14pt 0 4pt; }}
p {{ margin: 0 0 8pt; max-width: 165mm; }}
section {{ break-before: page; }}
.lead {{ font-size: 11.5pt; color: #263641; }}
.cover {{ height: 297mm; background: var(--base); color: var(--on-dark); padding: 26mm 20mm 20mm; display:flex; flex-direction:column; }}
.cover img {{ height: 30mm; width:auto; align-self:flex-start; }}
.cover .eyebrow {{ margin-top: 40mm; font-size: 9pt; letter-spacing:.1em; text-transform: uppercase; font-weight:700; color:#ffb3ae; }}
.cover h1 {{ font-size: 40pt; margin: 6pt 0 10pt; letter-spacing: -0.02em; }}
.cover .sub {{ font-size: 14pt; color: var(--on-dark-muted); max-width: 140mm; }}
.cover .band {{ margin-top:auto; border-top: 1px solid #263641; padding-top: 10pt; font-size: 9pt; color: var(--on-dark-muted); display:grid; grid-template-columns: 1fr 1fr; gap: 6pt 20pt; }}
.cover .band b {{ color: var(--on-dark); font-weight:600; }}
.bar {{ width: 18mm; height: 3px; background: var(--red); margin: 0 0 8pt; }}
.tiles {{ display:grid; grid-template-columns: 1fr 1fr; gap: 8pt; margin: 10pt 0 12pt; }}
.tile {{ background: var(--steel); color: var(--on-dark); border-radius: 8px; padding: 10pt 12pt; }}
.tl {{ font-size: 8pt; text-transform: uppercase; letter-spacing:.08em; color: var(--on-dark-muted); font-weight:700; }}
.tv {{ font-size: 24pt; font-weight: 700; margin: 2pt 0; letter-spacing:-0.01em; }}
.td {{ font-size: 9pt; color: #c2ced6; }}
.points li {{ margin-bottom: 5pt; }}
figure {{ margin: 10pt 0 14pt; padding: 10pt 12pt; border: 1px solid var(--line); border-radius: 8px; break-inside: avoid; }}
.ft {{ font-weight: 600; font-size: 10.5pt; margin-bottom: 6pt; }}
.fnum {{ font-family:'JetBrains Mono', monospace; font-size: 8pt; color: var(--red-text); font-weight:500; margin-right: 6pt; letter-spacing:.05em; text-transform: uppercase; }}
.cap {{ font-size: 9.5pt; color: var(--muted); margin: 6pt 0 2pt; }}
.src {{ font-size: 8pt; color: var(--muted); margin: 0; }}
table {{ width: 100%; border-collapse: collapse; font-size: 9pt; margin: 6pt 0 10pt; break-inside: avoid; }}
th {{ text-align:left; font-size: 7.5pt; text-transform: uppercase; letter-spacing:.08em; color: var(--muted); border-bottom: 1px solid #263641; padding: 4pt 6pt; font-weight:700; }}
td {{ border-bottom: 1px solid var(--line); padding: 4pt 6pt; vertical-align: top; }}
td:not(:first-child), th:not(:first-child) {{ text-align: right; font-variant-numeric: tabular-nums; }}
table.left td, table.left th {{ text-align:left; }}
.note {{ background: var(--page); border-left: 3px solid var(--red); padding: 8pt 12pt; border-radius: 4px; font-size: 9.5pt; margin: 8pt 0 12pt; break-inside: avoid; }}
.note b {{ font-weight: 600; }}
.plain {{ background: #F4F6F8; border-radius: 8px; padding: 8pt 12pt; margin: 6pt 0 12pt; font-size: 10pt; break-inside: avoid; }}
.plain .lbl {{ font-size: 7.5pt; text-transform: uppercase; letter-spacing:.1em; font-weight:700; color: var(--red-text); display:block; margin-bottom: 2pt; }}
dl.gloss {{ display:grid; grid-template-columns: 34mm 1fr; gap: 5pt 10pt; font-size: 10pt; }}
dl.gloss dt {{ font-weight: 600; }} dl.gloss dd {{ margin:0; }}
.small {{ font-size: 8.5pt; color: var(--muted); }}
</style></head><body>

<div class="cover">
  <img src="data:image/png;base64,{LOGO_DARK}" alt="Redbelly DAO">
  <div class="eyebrow">Quarterly on-chain holder report · Edition 1</div>
  <h1>RBNT holders in Q3 2026</h1>
  <div class="sub">How RBNT holders behaved between 1 July and 30 September 2026: accumulation, selling, staking and how concentrated holdings are.</div>
  <div class="band">
    <div><b>Period</b><br>1 Jul 2026 00:00 UTC to 30 Sep 2026 23:59 UTC</div>
    <div><b>Snapshot blocks</b><br><span class="mono">3025809</span> → <span class="mono">3209414</span></div>
    <div><b>Data source</b><br>Redbelly mainnet (chain ID 151), Routescan explorer</div>
    <div><b>Data collected</b><br>26 Oct 2026</div>
  </div>
</div>

<section style="break-before:auto">
<div class="bar"></div>
<h2><span class="k">Summary</span>The quarter at a glance</h2>
<p class="lead">{F["text"]["lead"]}</p>
<div class="tiles">{tiles}</div>
<ul class="points">{"".join(f"<li>{x}</li>" for x in F["text"]["points"])}</ul>
<div class="note"><b>What this report is and is not.</b> It describes what happened on the chain. It does not predict prices and it is not investment advice. Wallets are named only if they are already public: Redbelly's reserved wallets from the DAO treasury page, the WRBNT contract, the two Reddex staking pools, and contracts with a public name on Routescan. Every other wallet appears only inside a group.</div>
<h3>Five words you will see</h3>
<dl class="gloss">
<dt>Wallet</dt><dd>An address on the Redbelly chain that can hold RBNT. One person can have many wallets, and one wallet (an exchange, for example) can hold tokens for many people. So wallet counts are not people counts.</dd>
<dt>WRBNT</dt><dd>"Wrapped RBNT": RBNT locked in a contract and given back as a token that apps can use. 1 WRBNT is always backed by 1 RBNT. We count each token once.</dd>
<dt>Staking</dt><dd>Locking RBNT in a Reddex pool to earn RBNT rewards. The no-lock pool lets you withdraw at any time. The 365-day pool locks each deposit for a year.</dd>
<dt>Snapshot</dt><dd>The chain's state at one exact block. We compare the last block before 1 July with the last block before 1 October.</dd>
<dt>Holdings</dt><dd>For each wallet: plain RBNT + WRBNT + RBNT it has staked. Staking does not reduce what a wallet holds in this report.</dd>
</dl>
</section>

<section>
<div class="bar"></div>
<h2><span class="k">Section 1</span>Where RBNT sits</h2>
<p>We read the balance of every address that has ever sent, received or been named in a Redbelly transaction: {M(F["economic_total_end"])} RBNT at the end of the quarter. Here is how much each group held at the start and end of the quarter.</p>
{figure(1, "Share of all RBNT held by each group", chart_supply, F["text"]["c1"], SRC_SNAP)}
{table(["Group", "1 Jul 2026", "30 Sep 2026", "Change"], [[LABEL.get(r["category"], r["category"]), M(r["start"]), M(r["end"]), chg(r["change"]) if abs(r["change"]) >= 0.05e6 else "±0.0M"] for r in F["supply_map"] if (r["start"] or r["end"]) and r["category"] != "Zero address"] + [["<b>Total</b>", "<b>" + M(F["economic_total_start"]) + "</b>", "<b>" + M(F["economic_total_end"]) + "</b>", ""]])}
<div class="plain"><span class="lbl">In plain words</span>{F["text"]["s1_plain"]}</div>
</section>

<section>
<div class="bar"></div>
<h2><span class="k">Section 2</span>How concentrated holdings are</h2>
<p>This section looks only at <b>unnamed wallets holding more than 10 RBNT</b>: the community, exchanges' own wallets that are not labelled, and everyone else not in a named group. At the end of the quarter there were {N(ce["holders"])} of them, holding {M(ce["total"])} RBNT between them.</p>
{figure(2, "Share of unnamed-wallet RBNT held by the largest holders", chart_conc, F["text"]["c2"], SRC_SNAP)}
{table(["Measure", "1 Jul 2026", "30 Sep 2026", "Change"], [
    ["Holders (more than 10 RBNT)", N(cs["holders"]), N(ce["holders"]), f'{ce["holders"] - cs["holders"]:+,}'],
    ["Top 10 share", P(cs["top10_share"]), P(ce["top10_share"]), PP(cs["top10_share"], ce["top10_share"])],
    ["Top 50 share", P(cs["top50_share"]), P(ce["top50_share"]), PP(cs["top50_share"], ce["top50_share"])],
    ["Top 100 share", P(cs["top100_share"]), P(ce["top100_share"]), PP(cs["top100_share"], ce["top100_share"])],
    ["Top 500 share", P(cs["top500_share"]), P(ce["top500_share"]), PP(cs["top500_share"], ce["top500_share"])],
    ["Gini coefficient (0 = equal, 1 = one wallet holds all)", f'{cs["gini"]:.3f}', f'{ce["gini"]:.3f}', f'{ce["gini"] - cs["gini"]:+.3f}'],
    ["Median holding", N(cs["median"]) + " RBNT", N(ce["median"]) + " RBNT", ""]])}
{figure(3, "Number of unnamed wallets by holding size (RBNT)", chart_bands, F["text"]["c3"], SRC_SNAP)}
<div class="plain"><span class="lbl">In plain words</span>{F["text"]["s2_plain"]}</div>
</section>

<section>
<div class="bar"></div>
<h2><span class="k">Section 3</span>What the largest holders did</h2>
<p>We ranked unnamed wallets by holdings on 1 July and kept those groups fixed, then looked at the same wallets on 30 September. Holdings include staked RBNT, so moving tokens into a staking pool does not count as selling.</p>
{figure(4, "How many wallets in each group grew, stayed about the same, or shrank", chart_tiers, F["text"]["c4"], SRC_SNAP + ". Grew or shrank = more than 1% change")}
{figure(5, "Net change in holdings for each group (RBNT)", chart_tier_chg, F["text"]["c5"], SRC_SNAP)}
{table(["Group (rank on 1 Jul)", "Wallets", "1 Jul", "30 Sep", "Change", "Grew", "Same", "Shrank", "Emptied"],
       [[t["tier"], N(t["wallets"]), M(t["start"]), M(t["end"]), f'{chg(t["change"])} ({"+" if t["change_pct"] >= 0 else "−"}{abs(100*t["change_pct"]):.1f}%)', t["grew"], t["about_same"], t["shrank"], t["emptied"]] for t in tiers])}
<div class="plain"><span class="lbl">In plain words</span>{F["text"]["s3_plain"]}</div>
</section>

<section>
<div class="bar"></div>
<h2><span class="k">Section 4</span>Staking</h2>
<p>RBNT is staked in two Reddex pools. Both pay rewards in RBNT, taken from the pool's own balance, so <b>a pool's RBNT balance includes reward funds as well as people's stakes</b>. The pool contracts keep a running total of stakes (<span class="mono">totalStake()</span>), which lets us separate the two.</p>
{figure(6, "RBNT staked in each Reddex pool", chart_staking, F["text"]["c6"], SRC_SNAP + "; pool function <span class=mono>totalStake()</span>")}
{table(["", "No-lock pool", "365-day pool"], [
    ["Pool RBNT balance, 1 Jul", M(stk["nolock"]["balance_start"]), M(stk["lock365"]["balance_start"])],
    ["of which stakes", M(stk["nolock"]["staked_start"]), M(stk["lock365"]["staked_start"])],
    ["of which reward funds", M(stk["nolock"]["reward_funds_start"], 2), M(stk["lock365"]["reward_funds_start"], 2)],
    ["Pool RBNT balance, 30 Sep", M(stk["nolock"]["balance_end"]), M(stk["lock365"]["balance_end"])],
    ["of which stakes", M(stk["nolock"]["staked_end"]), M(stk["lock365"]["staked_end"])],
    ["of which reward funds", M(stk["nolock"]["reward_funds_end"], 2), M(stk["lock365"]["reward_funds_end"], 2)],
    ["Wallets with a stake, 1 Jul → 30 Sep", f'{stk["nolock"]["stakers_start"]} → {stk["nolock"]["stakers_end"]}', f'{stk["lock365"]["stakers_start"]} → {stk["lock365"]["stakers_end"]}'],
    ["RBNT staked during the quarter (gross)", M(pf["nolock"]["staked_gross"]), M(pf["lock365"]["staked_gross"])],
    ["RBNT unstaked during the quarter (gross)", M(pf["nolock"]["unstaked_gross"]), M(pf["lock365"]["unstaked_gross"])],
    ["Stake / unstake / claim transactions", f'{pf["nolock"]["stake_txs"]} / {pf["nolock"]["unstake_txs"]} / {pf["nolock"]["claim_txs"]}', f'{pf["lock365"]["stake_txs"]} / {pf["lock365"]["unstake_txs"]} / {pf["lock365"]["claim_txs"]}'],
    ["Reward funds added (all from Ecosystem (Unlocked))", M(pf["nolock"]["reward_funding"]), M(pf["lock365"]["reward_funding"])],
    ["Rewards paid out (estimate, see method)", M(pf["nolock"]["rewards_paid_est"], 2), M(pf["lock365"]["rewards_paid_est"], 2)]])}
<div class="plain"><span class="lbl">In plain words</span>{F["text"]["s4_plain"]}</div>
</section>

<section>
<div class="bar"></div>
<h2><span class="k">Section 5</span>Named wallets: reserved wallets, bridge and exchanges</h2>
<p>Redbelly's nine reserved wallets are listed on the DAO treasury page. The table there shows their <b>original allocations</b>. The figures below are their actual balances on the chain at the two snapshots.</p>
{figure(7, "Change in each reserved wallet's balance over the quarter (RBNT)", chart_res, F["text"]["c7"], SRC_SNAP + "; wallet names and addresses from redbellydao.network/treasury")}
{table(["Reserved wallet", "Address", "1 Jul 2026", "30 Sep 2026", "Change"], [[w, f'<span class="mono">{res[w]["address"][:8]}…{res[w]["address"][-4:]}</span>', M(res[w]["start"]), M(res[w]["end"]), chg(res[w]["change"]) if abs(res[w]["change"]) > 0.5 else "no change"] for w in res_order])}
<h3>What moved, and when</h3>
{F["text"]["s5_moves"]}
<h3>Bridge</h3>
<p>{F["text"]["s5_bridge"]}</p>
<h3>Exchanges</h3>
<p>{F["text"]["s5_exchanges"]}</p>
<div class="plain"><span class="lbl">In plain words</span>{F["text"]["s5_plain"]}</div>
</section>

<section>
<div class="bar"></div>
<h2><span class="k">Section 6</span>How this report was made</h2>
{F["text"]["method_html"]}
</section>

<section>
<div class="bar"></div>
<h2><span class="k">Appendix</span>Where each figure comes from</h2>
<p>Every figure is computed by the scripts in the repository from the files in <span class="mono">data/</span>. This table points each headline figure to its source.</p>
{table(["Figure", "Value", "Source", "Data file"], F["text"]["sources_rows"], "left")}
<h3 style="break-before:page">Checks</h3>
{table(["Check", "Result"], F["text"]["checks_rows"], "left")}
</section>
</body></html>'''
os.makedirs("report", exist_ok=True)
open("report/report.html", "w").write(html)
print("html written", len(html))
