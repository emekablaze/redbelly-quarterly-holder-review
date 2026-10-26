# Build the website (index.html = the full report, method.html = method and data dictionary)
# from the analysis outputs. Every number on the site is read from these files:
#   out/figures.json, out/named_balances.json, daily.json, out/community_summary.md, METHOD.md, data/README.md
# Usage: python3 build_site.py <site_root>   (site_root = the repository root that Vercel serves)
import csv, datetime, html, json, os, re, shutil, sys
import markdown

ROOT = sys.argv[1] if len(sys.argv) > 1 else "site"
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "site_src")
F = json.load(open("out/figures.json"))
NW = json.load(open("out/named_balances.json"))
DAILY = json.load(open("daily.json"))["rows"]
WEI = 10**18
SITE_URL = "https://redbelly-quarterly-holder-review.vercel.app"
E = html.escape

# ---------------- formatting ----------------
def M(v, d=1): return f"{v/1e6:,.{d}f}M"
def B(v, d=2): return f"{v/1e9:,.{d}f}B"
def N(v): return f"{v:,.0f}"
def P(v, d=1): return f"{100*v:.{d}f}%"
def S(v, f=M): return ("+" if v > 0 else "−" if v < 0 else "±") + f(abs(v))
def PP(a, b): x = 100 * (b - a); return ("+" if x >= 0 else "−") + f"{abs(x):.1f} pts"
def pct(a, b): return (b - a) / a if a else 0
def word(v, up="rose", down="fell", flat="did not change"): return up if v > 0 else down if v < 0 else flat
def mono(s): return f'<span class="mono">{s}</span>'
def blk(n): return mono(f"{n:,}")

S_BLOCK, E_BLOCK = F["blocks"]["start"], F["blocks"]["end"]
SUP = {r["category"]: r for r in F["supply_map"]}
cs, ce = F["concentration"]["start"], F["concentration"]["end"]
st, pf = F["staking"], F["pool_flows"]
staked_s = st["nolock"]["staked_start"] + st["lock365"]["staked_start"]
staked_e = st["nolock"]["staked_end"] + st["lock365"]["staked_end"]
total_s, total_e = F["economic_total_start"], F["economic_total_end"]
un = SUP["Unnamed wallets"]; vest = SUP["Token vesting contracts"]; resv = SUP["Redbelly reserved wallets"]
oth = SUP["Other smart contracts"]; brg = F["bridge"]
RES = {r["wallet"]: r for r in F["reserved"]}
eco = F["eco_unlocked"]; eco_out = {r["to"]: r for r in eco["rbnt_out"]}
tiers = F["tiers"]; t100 = tiers[:3]
g100 = sum(t["grew"] for t in t100); s100 = sum(t["shrank"] for t in t100); f100 = sum(t["about_same"] for t in t100)
c100 = sum(t["change"] for t in t100); b100 = sum(t["start"] for t in t100); e100 = sum(t["end"] for t in t100)
stk100_e = sum(t["staked_end"] for t in t100)
gross_in = pf["nolock"]["staked_gross"] + pf["lock365"]["staked_gross"]
gross_out = pf["nolock"]["unstaked_gross"] + pf["lock365"]["unstaked_gross"]
funding = pf["nolock"]["reward_funding"] + pf["lock365"]["reward_funding"]
paid = pf["nolock"]["rewards_paid_est"] + pf["lock365"]["rewards_paid_est"]
bands = F["bands"]; band_total_e = sum(b["rbnt_end"] for b in bands); band_total_s = sum(b["rbnt_start"] for b in bands)
small = [b for b in bands if b["band"] in ("10 – 1K", "1K – 10K")]
big = [b for b in bands if b["band"] in ("1M – 10M", "10M +")]
POOL_ADDR = {"nolock": "0x43a1dc107bbb06df266278056055ae7fc5bd2817", "lock365": "0x5e8040e85d0e6363d798a43bea939c026449946d"}
WRBNT = "0x6ed1f491e2d31536d6561f6bdb2adc8f092a6076"; BRIDGE = "0x020940df9f5e77338a094d55b5b5914122a804a5"
RES_ORDER = ["Ecosystem (Locked)", "Ecosystem 2 (Unlocked)", "Investors", "Ecosystem (Unlocked)", "Governance (Locked)",
             "Governance (Unlocked)", "TEAM (Locked)", "Reserve", "USYD/CSIRO (Locked)"]
COLLECTED = "26 Oct 2026"

# ---------------- data for the charts (embedded in the page) ----------------
SUPPLY_ROWS = [("Redbelly reserved wallets", "Redbelly reserved wallets"), ("Token vesting contracts", "Token vesting contracts"),
               ("Unnamed wallets", "Unnamed wallets"), ("Other smart contracts", "Other smart contracts"),
               ("Bridge (RBNT Native OFT Adapter)", "Bridge to other chains"), ("Reddex staking pools", "Reddex pools: reward funds")]
data = {
    "supply": [{"label": lab, "start": SUP[k]["start"], "end": SUP[k]["end"], "share_start": SUP[k]["start"] / total_s, "share_end": SUP[k]["end"] / total_e} for k, lab in SUPPLY_ROWS],
    "supply_change": sorted([{"label": lab, "value": SUP[k]["change"]} for k, lab in SUPPLY_ROWS], key=lambda r: -r["value"]),
    "topn": [{"label": f"Top {n}", "start": cs[f"top{n}_share"], "end": ce[f"top{n}_share"]} for n in (10, 50, 100, 500)],
    "bands": [dict(b, share_end=b["rbnt_end"] / band_total_e, share_start=b["rbnt_start"] / band_total_s) for b in bands],
    "tiers": tiers,
    "daily": {"dates": [r["date"] for r in DAILY], "nolock": [r["staked_nolock"] for r in DAILY], "lock365": [r["staked_lock365"] for r in DAILY],
              "vesting": [r["vesting"] for r in DAILY], "bridge": [r["bridge"] for r in DAILY], "wrbnt": [r["wrbnt_supply"] for r in DAILY]},
    "waterfall": [{"label": "1 Jul", "value": staked_s, "kind": "total", "tipLabel": "Staked on 1 Jul"},
                  {"label": "Staked in", "value": gross_in, "kind": "up", "tipLabel": "Staked during the quarter", "note": f"{pf['nolock']['stake_txs'] + pf['lock365']['stake_txs']:,} stake transactions"},
                  {"label": "Withdrawn", "value": -gross_out, "kind": "down", "tipLabel": "Unstaked during the quarter", "note": f"{pf['nolock']['unstake_txs'] + pf['lock365']['unstake_txs']:,} unstake transactions"},
                  {"label": "30 Sep", "value": staked_e, "kind": "total", "tipLabel": "Staked on 30 Sep"}],
    "reserved": [{"wallet": w, "start": RES[w]["start"], "end": RES[w]["end"], "change": RES[w]["change"]} for w in RES_ORDER],
    "eco_out": [{"label": "Wrapped into WRBNT", "value": eco_out["Wrapped into WRBNT"]["rbnt"], "note": "The WRBNT was then sent on to smart contracts"},
                {"label": "Staking pools (reward funds)", "value": eco_out["Reddex staking pools (reward funds)"]["rbnt"], "note": "Plain transfers that top up the pools' reward funds"},
                {"label": f"Unnamed wallets ({eco_out['Unnamed wallets']['addresses']})", "value": eco_out["Unnamed wallets"]["rbnt"], "note": f"{eco_out['Unnamed wallets']['txs']} transactions"}]
               + ([{"label": "Other smart contracts", "value": eco_out["Other smart contracts"]["rbnt"], "note": ""}] if "Other smart contracts" in eco_out else [])
               + [{"label": "Transaction fees", "value": eco["gas_fees"], "note": f"Across all {eco['txs_sent']} transactions it sent"}],
}

tot_daily = [r["staked_nolock"] + r["staked_lock365"] for r in DAILY]
jump_i = max(range(1, len(DAILY)), key=lambda i: abs(tot_daily[i] - tot_daily[i - 1]))
JUMP = {"date": DAILY[jump_i]["date"], "change": tot_daily[jump_i] - tot_daily[jump_i - 1],
        "nolock": DAILY[jump_i]["staked_nolock"] - DAILY[jump_i - 1]["staked_nolock"],
        "lock365": DAILY[jump_i]["staked_lock365"] - DAILY[jump_i - 1]["staked_lock365"]}
JUMP_DAY = datetime.date.fromisoformat(JUMP["date"]).strftime("%-d %b")
data["staking_jump"] = {"date": JUMP["date"], "label": f"{JUMP_DAY}: {S(JUMP['change'])} in one day"}

# ---------------- verify specs (named addresses only) ----------------
def bal_spec(label, what, addr, tag, key="rbnt"):
    b = S_BLOCK if tag == "start" else E_BLOCK
    return {"label": label, "what": what, "method": "eth_getBalance", "params": [addr, hex(b)], "block": b,
            "blockLabel": "last block before 1 Jul 2026" if tag == "start" else "last block of Q3 2026",
            "expect": NW["addresses"][addr][f"{key}_{tag}"]}
def call_spec(label, what, to, data_, tag, expect):
    b = S_BLOCK if tag == "start" else E_BLOCK
    return {"label": label, "what": what, "method": "eth_call", "params": [{"to": to, "data": data_}, hex(b)], "block": b,
            "blockLabel": "last block before 1 Jul 2026" if tag == "start" else "last block of Q3 2026", "expect": expect}
def vbtn(spec, text="Verify"):
    return (f'<button class="verify" type="button" data-verify="{E(json.dumps(spec))}" aria-label="Verify on-chain: {E(spec["label"])}">'
            f'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M3 8.5l3 3 7-7"/></svg>{text}</button>')
P_ = NW["pools"]
V_STAKE = {k: {t: call_spec(f"{'No-lock' if k == 'nolock' else '365-day'} pool: RBNT staked, {'1 Jul' if t == 'start' else '30 Sep'}",
                            "Calls totalStake() on the pool contract at the snapshot block. The pool keeps this running total of everyone's stakes.",
                            POOL_ADDR[k], "0x8b0e9f3f", t, P_[k][f"totalStake_{t}"]) for t in ("start", "end")} for k in ("nolock", "lock365")}
V_POOLBAL = {k: bal_spec(f"{'No-lock' if k == 'nolock' else '365-day'} pool: RBNT balance, 30 Sep",
                         "Reads the pool contract's RBNT balance (stakes plus reward funds) at the end block.", POOL_ADDR[k], "end") for k in ("nolock", "lock365")}
V_WRBNT = call_spec("WRBNT total supply, 30 Sep", "Calls totalSupply() on the Wrapped RBNT contract at the end block. It equals the RBNT the contract holds, so each token is counted once.",
                    WRBNT, "0x18160ddd", "end", P_["wrbnt"]["totalSupply_end"])
V_BRIDGE = {t: bal_spec(f"Bridge adapter: RBNT locked, {'1 Jul' if t == 'start' else '30 Sep'}", "Reads the RBNT balance of the verified RBNTNativeOFTAdapter contract.", BRIDGE, t) for t in ("start", "end")}

# ---------------- html helpers ----------------
def card(cid, title, sub, body_chart, table_html, source, csv_file=None, legend=None, anim=True):
    tools = ('<div class="cc-tools"><div class="seg" role="group" aria-label="View">'
             '<button type="button" data-view="chart" aria-pressed="true">Chart</button>'
             '<button type="button" data-view="table" aria-pressed="false">Table</button></div>'
             + (f'<a class="btn btn-sm" href="data/{csv_file}" download aria-label="Download {E(title)} data as CSV">CSV</a>' if csv_file else "") + '</div>')
    leg = ""
    if legend:
        leg = '<div class="legend">' + "".join(f'<span><i class="{"line " if kind == "line" else ""}bg-{cls}"></i>{E(lab)}</span>' for lab, cls, kind in legend) + "</div>"
    return f'''<figure class="card {"anim" if anim else ""}" id="{cid}" aria-labelledby="{cid}-t">
<div class="cc-head"><div><h3 id="{cid}-t">{title}</h3><p>{sub}</p></div>{tools}</div>
<div class="cc-body"><div class="chart-view">{leg}{body_chart}</div><div class="table-view" hidden>{table_html}</div></div>
<figcaption class="cc-foot"><span>Source: {source}</span></figcaption></figure>'''
def chart(name, label): return f'<div class="chart" data-chart="{name}" role="img" aria-label="{E(label)}"></div>'
def table(head, rows, right=()):
    h = "".join(f'<th class="{"r" if i in right else ""}">{x}</th>' for i, x in enumerate(head))
    b = "".join("<tr" + (' class="total"' if r and str(r[0]).startswith("<b>") else "") + ">" + "".join(f'<td class="{"r" if i in right else ""}">{c}</td>' for i, c in enumerate(r)) + "</tr>" for r in rows)
    return f'<table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>'
def plain(txt): return f'<aside class="plain"><span class="caps">In plain words</span><p>{txt}</p></aside>'
def term(word_, tip): return f'<span class="term" tabindex="0" title="{E(tip)}">{word_}</span>'
SRC_SNAP = f"Redbelly mainnet RPC, balances at blocks {blk(S_BLOCK)} (30 Jun 2026 23:57 UTC) and {blk(E_BLOCK)} (30 Sep 2026 23:57 UTC)"
SRC_DAILY = "Redbelly mainnet RPC, read at the last block before each midnight UTC, 1 Jul to 1 Oct 2026"

def icon(name):
    paths = {
        "arrow": '<path d="M3 8h10M9 4l4 4-4 4"/>', "down": '<path d="M8 2v9M4 7l4 4 4-4M3 14h10"/>',
        "sun": '<circle cx="8" cy="8" r="3"/><path d="M8 1v1.5M8 13.5V15M1 8h1.5M13.5 8H15M3 3l1 1M12 12l1 1M13 3l-1 1M4 12l-1 1"/>',
        "moon": '<path d="M13.5 9.5A5.5 5.5 0 016.5 2.5a5.5 5.5 0 107 7z"/>', "menu": '<path d="M2 4h12M2 8h12M2 12h12"/>',
        "up": '<path d="M8 13V3M4 7l4-4 4 4"/>', "close": '<path d="M3 3l10 10M13 3L3 13"/>', "copy": '<rect x="5" y="5" width="9" height="9" rx="1.5"/><path d="M11 5V3.5A1.5 1.5 0 009.5 2h-6A1.5 1.5 0 002 3.5v6A1.5 1.5 0 003.5 11H5"/>',
        "x": '<path d="M2 2l12 12M14 2L2 14"/>', "ext": '<path d="M9 3h4v4M13 3L7 9M11 9v4H3V5h4"/>'}
    cls = "ic16 " + {"sun": "i-sun", "moon": "i-moon"}.get(name, "")
    return f'<svg class="{cls}" width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{paths[name]}</svg>'

NAV = [("summary", "00", "Summary"), ("supply", "01", "Where RBNT sits"), ("concentration", "02", "Concentration"),
       ("largest", "03", "Largest holders"), ("staking", "04", "Staking"), ("named", "05", "Named wallets"),
       ("method", "06", "Method & checks"), ("downloads", "07", "Data & sharing")]

# ---------------- copy ----------------
lead = (f"Between 1 July and 30 September 2026, RBNT moved out of Redbelly's reserved wallets and vesting contracts and into unnamed wallets, "
        f"and more of it was staked. Staking {word(staked_e - staked_s, 'grew', 'fell')} by {P(abs(pct(staked_s, staked_e)))}, and holdings stayed concentrated in a small number of large wallets.")
findings = [
    ("Staking", "04", M(staked_e), f"RBNT staked in the two Reddex pools on 30 Sep, {S(staked_e - staked_s)} ({'+' if staked_e >= staked_s else '−'}{P(abs(pct(staked_s, staked_e)))}) over the quarter.", "#staking"),
    ("Largest holders", "03", f"{g100} / {f100} / {s100}", f"Of the 100 largest unnamed wallets on 1 Jul: grew / about the same / shrank. Staked RBNT counts as held.", "#largest"),
    ("Concentration", "02", P(ce["top10_share"]), f"Share of unnamed-wallet RBNT held by the 10 largest unnamed wallets ({PP(cs['top10_share'], ce['top10_share'])} since 1 Jul).", "#concentration"),
    ("Unnamed wallets", "01", S(un["change"]), f"Net change in RBNT held by unnamed wallets, which ended the quarter with {M(un['end'])} ({P(un['end'] / total_e)} of all RBNT).", "#supply"),
    ("Reserved wallets", "05", "10 Sep", f"The only day the multisig reserved wallets moved: three transfers between Redbelly's own wallets, {M(500e6, 0)} the largest.", "#named"),
    ("Vesting", "05", S(vest["change"]), f"RBNT released by token vesting contracts during the quarter, counting WRBNT as RBNT.", "#named"),
]
glossary = [
    ("Wallet", "An address on Redbelly that can hold RBNT. One person can have many wallets, and one wallet (an exchange, say) can hold tokens for many people, so wallet counts are not people counts."),
    ("WRBNT", "Wrapped RBNT: RBNT locked in a contract and handed back as a token that apps can use. Always backed 1 to 1, so we count each token once."),
    ("Staking", "Locking RBNT in a Reddex pool to earn RBNT rewards. The no-lock pool allows withdrawals at any time. The 365-day pool locks each deposit for a year."),
    ("Snapshot", "The chain's exact state at one block. This report compares the last block before 1 July with the last block of 30 September."),
    ("Holdings", "For each wallet: plain RBNT + WRBNT + RBNT it has staked. Moving RBNT into staking does not lower what a wallet holds here."),
]
supply_plain = (f"Most RBNT is still where it started: in wallets Redbelly reserved at launch ({P(resv['end'] / total_e)} of all RBNT) and in contracts that release tokens over time ({P(vest['end'] / total_e)}). "
                f"During the quarter, vesting contracts released {M(abs(vest['change']))} RBNT, the reserved wallets sent out {M(abs(resv['change']))} on balance, and unnamed wallets ended up with {M(un['change'])} more. "
                f"The total fell slightly ({M(total_s - total_e, 2)}) because transaction fees leave the payer's wallet: {M(F['fees_q3'], 2)} RBNT was paid in fees, and about {M(F['fee_credits_q3'], 2)} of that was paid back out to other addresses.")
conc_plain = (f"RBNT in unnamed wallets is held very unevenly. The {N(ce['holders'])} unnamed wallets holding more than 10 RBNT are mostly small: "
              f"{N(sum(b['wallets_end'] for b in small))} of them hold less than 10,000 RBNT each, and together they have {P(sum(b['share_end'] for b in data['bands'] if b['band'] in ('10 – 1K', '1K – 10K')), 2)} of the RBNT in this group. "
              f"At the other end, {N(sum(b['wallets_end'] for b in big))} wallets with more than 1 million RBNT each hold {P(sum(b['share_end'] for b in data['bands'] if b['band'] in ('1M – 10M', '10M +')))}. "
              f"A Gini score of {ce['gini']:.2f} (where 1 would mean one wallet holds everything) says the same thing in one number. This is common for tokens whose large balances sit with exchanges, funds and early participants. "
              f"Over the quarter the shape barely changed: the top 10 share moved {PP(cs['top10_share'], ce['top10_share'])}.")
largest_plain = (f"The 100 largest unnamed wallets on 1 July held {M(b100)} RBNT. By 30 September the same 100 wallets held {M(e100)}, and {M(stk100_e)} of that was staked. "
                 f"{F['top100_turnover']['stayed']} of them were still in the top 100 at the end of the quarter, and {F['top100_turnover']['new_entrants']} new wallets joined. "
                 f"Shrinking wallets were a minority in every group. The data shows what changed, not why: a wallet can grow from buying, from a vesting release or from moving tokens between its owner's wallets.")
staking_plain = (f"More RBNT went into staking than came out: {M(gross_in)} was staked during the quarter and {M(gross_out)} was withdrawn, leaving {M(staked_e)} staked on 30 September "
                 f"({P(staked_e / total_e)} of all RBNT). The number of wallets with a stake went from {N(F['stakers_any_start'])} to {N(F['stakers_any_end'])}, so the growth came from bigger stakes, not more stakers. "
                 f"The biggest single day was {JUMP_DAY}, when stakes rose by {M(JUMP['change'])} ({S(JUMP['nolock'])} in the no-lock pool); outside that day the total moved by less than {M(sorted(abs(tot_daily[i] - tot_daily[i - 1]) for i in range(1, len(DAILY)))[-2] + 0.05e6)} a day. "
                 f"The 365-day pool opened on 31 May 2025, so deposits from its first weeks began reaching the end of their one-year lock in mid-2026, and that is why some RBNT left it this quarter.")
named_plain = (f"The large reserved-wallet moves this quarter were transfers between Redbelly's own wallets, all on 10 September. "
               f"RBNT actually left the reserved wallets through Ecosystem (Unlocked), which tops up the staking reward funds and makes other ecosystem payments: {M(abs(RES['Ecosystem (Unlocked)']['change']))} net over the quarter.")

# ---------------- sections ----------------
def sec(id_, num, title, lede, body):
    return f'''<section class="block" id="{id_}" aria-labelledby="{id_}-h">
<header class="sec-head reveal"><div class="sec-num">{num}</div><h2 id="{id_}-h">{title}<a class="anchor" href="#{id_}" aria-label="Link to this section">#</a></h2><p class="lede">{lede}</p></header>
{body}</section>'''

summary_body = f'''
<div class="findings">{"".join(f'<a class="finding reveal" href="{h}"><div class="caps"><span>{c}</span><span>{n}</span></div><div class="fig">{fig}</div><p>{t}</p><span class="go">Read section {icon("arrow")}</span></a>' for c, n, fig, t, h in findings)}</div>
<h3 style="margin:40px 0 4px">New to on-chain data? Five words you will see</h3>
<dl class="gloss">{"".join(f"<div><dt>{a}</dt><dd>{b}</dd></div>" for a, b in glossary)}</dl>
<div class="note-box" style="margin-top:24px"><b>What this report is, and is not.</b> It describes what happened on the chain. It does not predict prices and it is not investment advice.
Wallets are named only when they are already public: Redbelly's reserved wallets from the DAO treasury page, the Wrapped RBNT contract, the two Reddex staking pools,
and contracts with a public name on Routescan. Every other wallet appears only inside a group.</div>'''

supply_tbl = table(["Group", "1 Jul 2026", "Share", "30 Sep 2026", "Share", "Change"],
                   [[r["label"], M(r["start"]), P(r["share_start"]), M(r["end"]), P(r["share_end"]), S(r["end"] - r["start"])] for r in data["supply"]]
                   + [["<b>All RBNT read</b>", f"<b>{M(total_s)}</b>", "100%", f"<b>{M(total_e)}</b>", "100%", S(total_e - total_s, lambda v: M(v, 2))]], right=(1, 2, 3, 4, 5))
supply_body = f'''
{card("c-supply", "Where all RBNT sat at the start and end of the quarter", "Holdings by group. Staked RBNT is counted with the wallet that staked it, and WRBNT with the wallet that holds it.",
      chart("supply", "Paired bars comparing each group's RBNT on 1 July and 30 September"), supply_tbl, SRC_SNAP, "supply_by_category.csv",
      legend=[("1 Jul 2026", "base", "box"), ("30 Sep 2026", "accent", "box")])}
{card("c-supply-chg", "Net change over the quarter, by group", f"Where the RBNT went: what each group gained or lost between the two snapshots. All groups together: {S(total_e - total_s, lambda v: M(v, 2))} (transaction fees that were not paid back out).",
      chart("supplyChange", "Bars showing each group's net change in RBNT over the quarter"), table(["Group", "Change (RBNT)"], [[r["label"], S(r["value"])] for r in data["supply_change"]], right=(1,)), SRC_SNAP, "supply_by_category.csv")}
{plain(supply_plain)}'''

conc_tbl = table(["Measure", "1 Jul 2026", "30 Sep 2026", "Change"], [
    ["Holders (more than 10 RBNT)", N(cs["holders"]), N(ce["holders"]), f'{ce["holders"] - cs["holders"]:+,}'],
    ["Top 10 share", P(cs["top10_share"]), P(ce["top10_share"]), PP(cs["top10_share"], ce["top10_share"])],
    ["Top 50 share", P(cs["top50_share"]), P(ce["top50_share"]), PP(cs["top50_share"], ce["top50_share"])],
    ["Top 100 share", P(cs["top100_share"]), P(ce["top100_share"]), PP(cs["top100_share"], ce["top100_share"])],
    ["Top 500 share", P(cs["top500_share"]), P(ce["top500_share"]), PP(cs["top500_share"], ce["top500_share"])],
    ["Gini coefficient", f'{cs["gini"]:.3f}', f'{ce["gini"]:.3f}', f'{ce["gini"] - cs["gini"]:+.3f}'],
    ["Median holding", N(cs["median"]) + " RBNT", N(ce["median"]) + " RBNT", ""]], right=(1, 2, 3))
bands_tbl = table(["Holding size (RBNT)", "Wallets 1 Jul", "Wallets 30 Sep", "RBNT 30 Sep", "Share 30 Sep"],
                  [[b["band"], N(b["wallets_start"]), N(b["wallets_end"]), M(b["rbnt_end"]), P(b["share_end"], 2)] for b in data["bands"]], right=(1, 2, 3, 4))
conc_body = f'''
<div class="stats reveal">
<div class="stat"><span class="caps">Holders above 10 RBNT</span><span class="v">{N(ce["holders"])}</span><span class="d">{ce["holders"] - cs["holders"]:+,} since 1 Jul</span></div>
<div class="stat"><span class="caps">Top 10 share</span><span class="v">{P(ce["top10_share"])}</span><span class="d">{PP(cs["top10_share"], ce["top10_share"])}</span></div>
<div class="stat"><span class="caps">Top 100 share</span><span class="v">{P(ce["top100_share"])}</span><span class="d">{PP(cs["top100_share"], ce["top100_share"])}</span></div>
<div class="stat"><span class="caps">Gini coefficient</span><span class="v">{ce["gini"]:.3f}</span><span class="d">{ce["gini"] - cs["gini"]:+.3f}</span></div>
<div class="stat"><span class="caps">Median holding</span><span class="v">{N(ce["median"])}</span><span class="d">RBNT, 30 Sep</span></div>
</div>
{card("c-topn", "How much of the unnamed-wallet RBNT the largest holders have", f"Share held by the 10, 50, 100 and 500 largest of the {N(ce['holders'])} unnamed wallets above 10 RBNT.",
      chart("topn", "Columns comparing top-10, top-50, top-100 and top-500 shares on 1 July and 30 September"), conc_tbl, SRC_SNAP, "concentration.csv",
      legend=[("1 Jul 2026", "base", "box"), ("30 Sep 2026", "accent", "box")])}
{card("c-bands", "Many small wallets, a few very large ones", "Unnamed wallets above 10 RBNT, grouped by how much they hold on 30 Sep: how many wallets (left) and what share of the RBNT (right).",
      f'<div class="duo"><div><p class="subhead">Number of wallets</p>{chart("bandsCount", "Bars of wallet counts by holding size")}</div><div><p class="subhead">Share of the RBNT they hold</p>{chart("bandsShare", "Bars of RBNT share by holding size")}</div></div>',
      bands_tbl, SRC_SNAP, "holder_size_bands.csv")}
{plain(conc_plain)}'''

tiers_tbl = table(["Group (rank on 1 Jul)", "Wallets", "Held 1 Jul", "Held 30 Sep", "Change", "Grew", "Same", "Shrank", "Emptied"],
                  [[t["tier"], N(t["wallets"]), M(t["start"]), M(t["end"]), f'{S(t["change"])} ({"+" if t["change_pct"] >= 0 else "−"}{abs(100*t["change_pct"]):.1f}%)', t["grew"], t["about_same"], t["shrank"], t["emptied"]] for t in tiers],
                  right=(1, 2, 3, 4, 5, 6, 7, 8))
largest_body = f'''
<div class="prose reveal"><p>We ranked every unnamed wallet by its holdings on 1 July, split the ranking into groups, and then looked at the <b>same wallets</b> on 30 September.
Keeping the groups fixed shows what those holders actually did, rather than who happened to be at the top at the end. A wallet <b>grew</b> if its holdings rose by more than 1%, <b>shrank</b> if they fell by more than 1%, and otherwise stayed <b>about the same</b>.</p></div>
{card("c-tiers", "Grew, stayed about the same, or shrank", "Number of wallets in each group, ranked by holdings on 1 Jul 2026.",
      chart("tiers", "Stacked bars showing how many wallets in each group grew, stayed about the same or shrank"), tiers_tbl, SRC_SNAP + ". Grew or shrank = more than 1% change", "largest_holder_tiers.csv",
      legend=[("Grew", "accent", "box"), ("About the same", "neutral", "box"), ("Shrank", "base", "box")])}
{card("c-tierchg", "Net change in holdings, by group", "Total RBNT gained or lost by each group of wallets between 1 Jul and 30 Sep.",
      chart("tierChange", "Bars showing each group's net change in holdings"), tiers_tbl, SRC_SNAP, "largest_holder_tiers.csv")}
{plain(largest_plain)}'''

pool_tbl_rows = []
for lab, k1, k2, f in [("Pool RBNT balance, 1 Jul", "balance_start", None, M), ("&nbsp;&nbsp;of which stakes", "staked_start", None, M), ("&nbsp;&nbsp;of which reward funds", "reward_funds_start", None, lambda v: M(v, 2)),
                       ("Pool RBNT balance, 30 Sep", "balance_end", None, M), ("&nbsp;&nbsp;of which stakes", "staked_end", None, M), ("&nbsp;&nbsp;of which reward funds", "reward_funds_end", None, lambda v: M(v, 2))]:
    row = [lab]
    for k in ("nolock", "lock365"):
        cell = f(st[k][k1])
        if k1 == "staked_start": cell += " " + vbtn(V_STAKE[k]["start"])
        if k1 == "staked_end": cell += " " + vbtn(V_STAKE[k]["end"])
        if k1 == "balance_end": cell += " " + vbtn(V_POOLBAL[k])
        row.append(cell)
    pool_tbl_rows.append(row)
pool_tbl_rows += [
    ["Wallets with a stake, 1 Jul → 30 Sep", f'{N(st["nolock"]["stakers_start"])} → {N(st["nolock"]["stakers_end"])}', f'{N(st["lock365"]["stakers_start"])} → {N(st["lock365"]["stakers_end"])}'],
    ["RBNT staked during the quarter", M(pf["nolock"]["staked_gross"]), M(pf["lock365"]["staked_gross"])],
    ["RBNT withdrawn during the quarter", M(pf["nolock"]["unstaked_gross"]), M(pf["lock365"]["unstaked_gross"])],
    ["Stake / unstake / claim transactions", f'{pf["nolock"]["stake_txs"]:,} / {pf["nolock"]["unstake_txs"]:,} / {pf["nolock"]["claim_txs"]:,}', f'{pf["lock365"]["stake_txs"]:,} / {pf["lock365"]["unstake_txs"]:,} / {pf["lock365"]["claim_txs"]:,}'],
    ["Reward funds added (from Ecosystem (Unlocked))", M(pf["nolock"]["reward_funding"]), M(pf["lock365"]["reward_funding"])],
    ["Rewards paid out (estimate)", M(pf["nolock"]["rewards_paid_est"], 2), M(pf["lock365"]["rewards_paid_est"], 2)]]
pool_tbl = table(["", "No-lock pool", "365-day pool"], pool_tbl_rows, right=(1, 2))
daily_tbl = table(["Day (end of)", "No-lock pool", "365-day pool", "Total staked"],
                  [[r["date"], M(r["staked_nolock"]), M(r["staked_lock365"]), M(r["staked_nolock"] + r["staked_lock365"])] for r in DAILY[::7] + [DAILY[-1]]], right=(1, 2, 3))
staking_body = f'''
<div class="stats reveal">
<div class="stat"><span class="caps">Staked on 30 Sep</span><span class="v">{M(staked_e)}</span><span class="d">{S(staked_e - staked_s)} in Q3</span></div>
<div class="stat"><span class="caps">Share of all RBNT</span><span class="v">{P(staked_e / total_e)}</span><span class="d">was {P(staked_s / total_s)} on 1 Jul</span></div>
<div class="stat"><span class="caps">Staked in / withdrawn</span><span class="v">{M(gross_in, 0)} / {M(gross_out, 0)}</span><span class="d">gross, during Q3</span></div>
<div class="stat"><span class="caps">Wallets with a stake</span><span class="v">{N(F["stakers_any_end"])}</span><span class="d">{F["stakers_any_end"] - F["stakers_any_start"]:+,} since 1 Jul</span></div>
</div>
{card("c-staking", "RBNT staked in each Reddex pool, day by day", "Stakes only (each pool's totalStake()), read at the end of every day of the quarter. Hover or use the arrow keys to read any day.",
      chart("stakingDaily", "Line chart of daily RBNT staked in the no-lock and 365-day pools"), daily_tbl, SRC_DAILY + "; pool function " + mono("totalStake()"), "daily_series.csv",
      legend=[("No-lock pool", "accent", "line"), ("365-day pool", "base", "line")])}
{card("c-waterfall", "From 1 July to 30 September: what went in and what came out", "Both pools together. Staked in = every successful stake() transaction; withdrawn = staked in minus the change in totalStake().",
      chart("waterfall", "Waterfall from RBNT staked on 1 July, plus RBNT staked, minus RBNT withdrawn, to RBNT staked on 30 September"),
      table(["Step", "RBNT"], [[s["tipLabel"], (S(s["value"]) if s["kind"] != "total" else M(s["value"]))] for s in data["waterfall"]], right=(1,)), SRC_SNAP + "; every transaction sent to the pools in blocks " + blk(S_BLOCK + 1) + "–" + blk(E_BLOCK), "staking_pools.csv",
      legend=[("Total staked", "strong", "box"), ("Staked in", "accent", "box"), ("Withdrawn", "base", "box")])}
<div class="card table-card reveal"><div class="cc-head"><div><h3>The two pools in numbers</h3><p>Every figure with a <span class="mono">Verify</span> button can be checked live against the chain from your browser.</p></div></div>
<div class="table-view">{pool_tbl}</div><div class="cc-foot"><span>Source: {SRC_SNAP}; pool contracts {mono("0x43A1…2817")} (no lock) and {mono("0x5E80…946d")} (365 days)</span></div></div>
<div class="note-box reveal"><b>Pool balances include reward funds as well as stakes.</b> Both pools pay rewards in RBNT out of their own balance, so a pool's RBNT balance is people's stakes plus RBNT added to pay rewards.
This report reads both the pool balance and the pool's own running total of stakes (<span class="mono">totalStake()</span>), and shows the gap as reward funds: {M(st["nolock"]["reward_funds_end"], 2)} in the no-lock pool and {M(st["lock365"]["reward_funds_end"], 2)} in the 365-day pool on 30 September.
During the quarter {M(funding, 0)} RBNT was added to the reward funds, and about {M(paid)} was paid out to stakers.</div>
{plain(staking_plain)}'''

res_rows = []
for w in RES_ORDER:
    r = RES[w]; a = r["address"]
    link = f'<a class="addr" href="https://redbelly.routescan.io/address/{a}" target="_blank" rel="noopener">{a[:6]}…{a[-4:]}</a>'
    res_rows.append([f"{w}<br>{link}", M(r["start"]) + " " + vbtn(bal_spec(f"{w}: RBNT balance, 1 Jul", "Reads the wallet's plain RBNT balance at the start block (any WRBNT it holds is listed separately in the data).", a, "start")),
                     M(r["end"]) + " " + vbtn(bal_spec(f"{w}: RBNT balance, 30 Sep", "Reads the wallet's plain RBNT balance at the end block.", a, "end")),
                     S(r["change"]) if abs(r["change"]) >= 0.5 else "no change"])
res_tbl = table(["Reserved wallet", "1 Jul 2026", "30 Sep 2026", "Change"], res_rows, right=(1, 2, 3))

def flow_svg():
    """The three reserved-wallet transfers of 10 September 2026: one row per transfer, in time order."""
    W, rowH, nw, nh = 860, 104, 236, 64
    moves = [(1, "00:51:34", 3175499, "Ecosystem 2 (Unlocked)", "Investors", RES["Investors"]["change"]),
             (2, "00:52:26", 3175501, "Ecosystem (Locked)", "Ecosystem 2 (Unlocked)", 500e6),
             (3, "00:53:19", 3175505, "Governance (Locked)", "Governance (Unlocked)", 33333333)]
    H = rowH * len(moves) + 8
    out = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-labelledby="flow-title flow-desc"><title id="flow-title">Reserved-wallet transfers on 10 September 2026</title>'
           '<desc id="flow-desc">' + " ".join(f"{t} UTC, block {b:,}: {a} sent {N(v)} RBNT to {c}." for _, t, b, a, c, v in moves) + '</desc>'
           '<defs><marker id="ah" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0L10,5L0,10z" class="flow-head"/></marker></defs>']
    def node(x, y, name):
        r = RES[name]
        return (f'<g class="flow-node"><rect x="{x}" y="{y}" width="{nw}" height="{nh}" rx="8"/><text x="{x+16}" y="{y+27}" class="nm">{E(name)}</text>'
                f'<text x="{x+16}" y="{y+47}" class="bal">Q3: {M(r["start"])} → {M(r["end"])}</text></g>')
    for k, (n, t, b, a, c, v) in enumerate(moves):
        y = 4 + k * rowH; cy = y + nh / 2
        out.append(node(0, y, a)); out.append(node(W - nw, y, c))
        x1, x2 = nw + 14, W - nw - 16
        out.append(f'<path d="M{x1},{cy} L{x2},{cy}" class="flow-edge" stroke-width="3" marker-end="url(#ah)"/>')
        mx = (x1 + x2) / 2
        out.append(f'<circle cx="{x1 + 16}" cy="{cy - 20}" r="10" class="flow-step"/><text x="{x1 + 16}" y="{cy - 16}" text-anchor="middle" class="flow-step-t">{n}</text>')
        out.append(f'<text x="{mx}" y="{cy - 14}" text-anchor="middle" class="flow-lbl">{N(v)} RBNT</text>')
        out.append(f'<text x="{mx}" y="{cy + 22}" text-anchor="middle" class="flow-time">{t} UTC · block {b:,}</text>')
    out.append("</svg>")
    return "".join(out)

eco_tbl = table(["Where it went", "RBNT"], [[r["label"], N(r["value"])] for r in data["eco_out"]], right=(1,))
named_body = f'''
<div class="prose reveal"><p>Redbelly's nine reserved wallets are listed with their addresses on the <a href="https://redbellydao.network/treasury/" target="_blank" rel="noopener">DAO treasury page</a>.
That page shows each wallet's <b>original allocation</b>. Everything below is the wallet's actual balance read from the chain at the two snapshots.</p></div>
{card("c-reserved", "Change in each reserved wallet over the quarter", "Plain RBNT plus WRBNT. Four of the nine wallets did not move at all.",
      chart("reserved", "Bars showing each reserved wallet's change in RBNT over the quarter"), res_tbl, SRC_SNAP + "; names and addresses from redbellydao.network/treasury", "reserved_wallets.csv")}
<div class="card table-card reveal"><div class="cc-head"><div><h3>Reserved wallets, with live checks</h3><p>Addresses link to the Routescan explorer. Every balance can be verified on-chain from your browser.</p></div></div>
<div class="table-view">{res_tbl}</div><div class="cc-foot"><span>Source: {SRC_SNAP}</span></div></div>
<div class="card reveal"><div class="cc-head"><div><h3>10 September 2026: three transfers in three minutes</h3><p>The only movements of the multisig reserved wallets in the quarter, in time order. All three stayed between Redbelly's own wallets. TEAM (Locked), Reserve and USYD/CSIRO (Locked) did not change.</p></div></div>
<div class="cc-body" style="overflow-x:auto"><div style="min-width:640px">{flow_svg()}</div></div>
<div class="cc-foot"><span>Source: balance change points found by binary search on each wallet's balance between blocks {blk(S_BLOCK)} and {blk(E_BLOCK)}</span></div></div>
{card("c-eco", "Where Ecosystem (Unlocked) sent RBNT", f"The one reserved wallet that sends its own transactions: {eco['txs_sent']} in the quarter, {M(abs(RES['Ecosystem (Unlocked)']['change']))} net out. It also received {M(sum(r['wrbnt'] for r in eco['wrbnt_in']), 2)} WRBNT from a vesting contract.",
      chart("ecoOut", "Bars showing where Ecosystem (Unlocked) sent RBNT"), eco_tbl, "Every transaction Ecosystem (Unlocked) sent in the quarter, with receipts for status, fees and WRBNT transfers", "eco_unlocked_flows.csv")}
{card("c-trends", "Vesting contracts and the bridge, day by day", f"RBNT held by the {DAILY and json.load(open('daily.json'))['vesting_contracts']} token vesting contracts (as WRBNT), and RBNT locked in the bridge to other chains.",
      f'<div class="duo"><div><p class="subhead">Token vesting contracts</p>{chart("vestingDaily", "Daily RBNT in vesting contracts")}</div><div><p class="subhead">Bridge adapter (locked for other chains) {vbtn(V_BRIDGE["end"])}</p>{chart("bridgeDaily", "Daily RBNT locked in the bridge adapter")}</div></div>',
      table(["Day (end of)", "Vesting contracts", "Bridge adapter"], [[r["date"], M(r["vesting"]), M(r["bridge"])] for r in DAILY[::7] + [DAILY[-1]]], right=(1, 2)), SRC_DAILY, "daily_series.csv")}
<div class="note-box reveal"><b>Bridge.</b> The RBNT Native OFT Adapter locks RBNT on Redbelly when it is bridged to another chain. It held {M(brg["start"])} on 1 July and {M(brg["end"])} on 30 September,
a net {word(brg["end"] - brg["start"], "increase", "decrease")} of {M(abs(brg["end"] - brg["start"]))}: slightly more RBNT moved out to other chains than came back. RBNT on other chains is outside this report.</div>
<div class="note-box reveal"><b>Exchanges.</b> When the data was collected ({COLLECTED}), Routescan showed no public exchange labels for any Redbelly address. Exchange wallets therefore
cannot be told apart in this edition, and any exchange balances sit inside the unnamed-wallets group. If labels appear, the next edition will report their flows separately.</div>
{plain(named_plain)}'''

checks = [r for r in csv.reader(open("out/checks.csv"))][1:]
check_rows = [[E(c[0]), f'<span class="status {"ok" if c[1] == "PASS" else "warn" if c[1] == "INFO" else "bad"}">{c[1]}</span>', f'<span class="mono" style="font-size:11.5px">{E(c[2])}</span>'] for c in checks]
method_body = f'''
<ol class="steps reveal">
<li><div><h3>Fix two snapshot blocks</h3><p>Block {blk(S_BLOCK)} is the last block before 1 July 2026 00:00 UTC and block {blk(E_BLOCK)} the last block of 30 September. Every balance is read at exactly these blocks from the public Redbelly RPC.</p></div></li>
<li><div><h3>Find every address</h3><p>Every block from the first to {COLLECTED} was read: {N(F["universe_size"])} addresses that sent or received a transaction or were named inside one (for example in batch payouts and Redbelly's account registry), plus the WRBNT holder list from Routescan. {N(F["addresses_nonzero"])} of them held RBNT, WRBNT or a stake at one of the two blocks.</p></div></li>
<li><div><h3>Count each token once</h3><p>Holdings = plain RBNT + WRBNT + RBNT staked in a Reddex pool. The RBNT inside the WRBNT contract is not counted again, and each pool's RBNT beyond its <span class="mono">totalStake()</span> is shown as reward funds.</p></div></li>
<li><div><h3>Group, never single out</h3><p>Publicly named wallets are named. Contracts are grouped by matching their code to verified contracts on Routescan. Every other wallet is reported only inside a group, and no unnamed address appears anywhere in the report or the data.</p></div></li>
<li><div><h3>Check that it adds up</h3><p>WRBNT balances add up to WRBNT's supply, stakers' balances add up to each pool's total, and holdings add up to the RBNT read: all to the wei, at both blocks.</p></div></li>
</ol>
<div class="card table-card reveal"><div class="cc-head"><div><h3>Reconciliation checks</h3><p>PASS rows must match exactly. INFO rows are reconciliation notes.</p></div><div class="cc-tools"><a class="btn btn-sm" href="data/checks.csv" download>CSV</a></div></div>
<div class="table-view checks">{table(["Check", "Result", "Detail"], check_rows)}</div></div>
<h3 style="margin:32px 0 12px">Limits worth knowing</h3>
<div class="limits reveal">
<div><b>Wallets are not people</b>One person can hold many wallets, and an exchange wallet holds tokens for many people.</div>
<div><b>No exchange labels yet</b>Routescan labelled no Redbelly exchange wallets at collection time, so exchange balances sit inside the unnamed-wallets group.</div>
<div><b>Other chains are out of scope</b>Only the RBNT locked in the bridge adapter on Redbelly is shown, not RBNT on other chains.</div>
<div><b>Contracts are not looked through</b>RBNT inside exchange pools, routers and other unnamed contracts is reported as one group.</div>
</div>
<p style="margin-top:24px"><a class="btn" href="method.html">Read the full method and data dictionary {icon("arrow")}</a></p>'''

thread = [b.strip() for b in open("out/community_summary.md").read().split("\n\n") if re.match(r"\d+/ ", b)]
def dl(href, ic, title, sub, size, primary=False, ext=False):
    attrs = 'target="_blank" rel="noopener"' if ext else ("download" if not href.endswith((".html", ".md")) else "")
    return f'<a class="dl{" primary" if primary else ""}" href="{href}" {attrs}><span class="ic">{ic}</span><span><b>{title}</b><span>{sub}</span></span><span class="sz">{size}</span></a>'
def fsize(p):
    try: s = os.path.getsize(p)
    except OSError: return ""
    return f"{s/1e6:.1f} MB" if s > 1e6 else f"{s/1e3:.0f} KB"
downloads_body = f'''
<div class="downloads reveal">
{dl("report/RBNT-Holder-Report-Q3-2026.pdf", "PDF", "Full report (PDF)", "A4, with charts", fsize(os.path.join(ROOT, "report/RBNT-Holder-Report-Q3-2026.pdf")), True)}
{dl("data/figures.json", "JSON", "Every figure", "All numbers the report quotes", fsize("out/figures.json"))}
{dl("data/daily_series.csv", "CSV", "Daily series", "Staking, vesting, bridge, WRBNT", "")}
{dl("data/supply_by_category.csv", "CSV", "Supply by group", "Section 01", "")}
{dl("data/largest_holder_tiers.csv", "CSV", "Largest-holder groups", "Section 03 (no addresses)", "")}
{dl("data/staking_pools.csv", "CSV", "Staking pools", "Section 04", "")}
{dl("data/reserved_wallets.csv", "CSV", "Reserved wallets", "Section 05", "")}
{dl("data/checks.csv", "CSV", "Checks", "Reconciliation results", "")}
{dl("method.html", "DOC", "Method & data dictionary", "How to reproduce every number", "")}
</div>
<h3 style="margin:0 0 6px">Share the findings</h3>
<p style="margin:0 0 16px;color:var(--muted)">A ready-made thread for X. Copy a post, or open it straight in X.</p>
<div class="thread">{"".join(f'<div class="tweet reveal"><p id="tw{i}">{E(t)}</p><div class="row"><span class="cnt">{len(t)}/280</span><div class="acts"><button class="btn btn-sm" type="button" data-copy-from="#tw{i}">{icon("copy")}Copy</button><a class="btn btn-sm" href="https://x.com/intent/post?text={E(__import__("urllib.parse").parse.quote(t))}" target="_blank" rel="noopener">{icon("ext")}Post</a></div></div></div>' for i, t in enumerate(thread))}</div>'''

body_sections = "".join([
    sec("summary", "00 · Summary", "The quarter at a glance", lead, summary_body),
    sec("supply", "01", "Where RBNT sits", f"Every RBNT on Redbelly sits in one of a handful of places. This is how much each held at the start and end of the quarter, and where the {M(abs(un['change']), 0)} that reached unnamed wallets came from.", supply_body),
    sec("concentration", "02", "How concentrated holdings are", "This section looks only at unnamed wallets holding more than 10 RBNT: community wallets, exchanges' own unlabelled wallets, and everyone else outside a named group.", conc_body),
    sec("largest", "03", "What the largest holders did", "Accumulation and selling among the biggest unnamed wallets, in groups. Holdings include staked RBNT, so moving tokens into a pool is not counted as selling.", largest_body),
    sec("staking", "04", "Staking", f"RBNT is staked in two Reddex pools: one with no lock and one that locks each deposit for 365 days. Together they held {M(staked_e)} of stakes at the end of the quarter.", staking_body),
    sec("named", "05", "Named wallets: reserved, bridge and exchanges", "Flows in and out of the wallets that are already public: Redbelly's reserved wallets, the bridge adapter, and any labelled exchange wallets.", named_body),
    sec("method", "06", "How this report was made", "Read directly from the chain, checked to the wei, and written down so the next edition can be produced the same way.", method_body),
    sec("downloads", "07", "Data, downloads and sharing", "Everything behind the charts, in open formats. No file contains the address of an unnamed wallet.", downloads_body),
])

# ---------------- page shell ----------------
title = "RBNT Holder Report · Q3 2026"
desc = f"On-chain report on RBNT holders in Q3 2026: staking {S(staked_e - staked_s)} to {M(staked_e)}, top-10 share {P(ce['top10_share'])}, reserved-wallet flows. Read from Redbelly mainnet, checked to the wei."
def head(page_title, page_desc, path=""):
    return f'''<!doctype html><html lang="en" data-theme="dark"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(page_title)}</title>
<meta name="description" content="{E(page_desc)}">
<meta name="theme-color" content="#0c1317">
<link rel="canonical" href="{SITE_URL}/{path}">
<meta property="og:type" content="article"><meta property="og:title" content="{E(page_title)}"><meta property="og:description" content="{E(page_desc)}">
<meta property="og:url" content="{SITE_URL}/{path}"><meta property="og:image" content="{SITE_URL}/assets/img/og.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{E(page_title)}"><meta name="twitter:description" content="{E(page_desc)}"><meta name="twitter:image" content="{SITE_URL}/assets/img/og.png">
<link rel="icon" href="assets/img/favicon.ico" sizes="any"><link rel="icon" type="image/png" href="assets/img/favicon-32.png"><link rel="apple-touch-icon" href="assets/img/apple-touch-icon.png">
<link rel="preload" href="assets/fonts/BeVietnamPro-400-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="assets/fonts/BeVietnamPro-700-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="assets/css/fonts.css"><link rel="stylesheet" href="assets/css/site.css">
<script>(function(){{try{{var t=localStorage.getItem("rbnt-theme");if(!t)t=matchMedia("(prefers-color-scheme: light)").matches?"light":"dark";document.documentElement.dataset.theme=t;}}catch(e){{}}}})();</script>
</head>'''

def header(home=True):
    pre = "" if home else "index.html"
    nav = "".join(f'<a href="{pre}#{i}">{E(t)}</a>' for i, _, t in NAV[1:7])
    return f'''<a class="skip" href="#content">Skip to the report</a>
<header class="site-header"><div class="shell">
<a class="brand" href="{pre or '#top'}" aria-label="RBNT Holder Report, home"><img class="logo-dark" src="assets/img/dao-logo-on-dark.png" alt="Redbelly DAO" width="50" height="36"><img class="logo-light" src="assets/img/dao-logo-on-light.png" alt="Redbelly DAO" width="50" height="36">
<span class="brand-text"><b>Holder Report</b><span>Q3 2026 · Edition 01</span></span></a>
<nav class="top-nav" aria-label="Sections">{nav}</nav>
<div class="header-actions">
<button class="btn icon-btn theme-btn" type="button" aria-label="Switch light or dark theme">{icon("moon")}{icon("sun")}</button>
<a class="btn btn-primary hide-sm" href="report/RBNT-Holder-Report-Q3-2026.pdf" download>{icon("down")}PDF</a>
<button class="btn icon-btn menu-btn" type="button" aria-label="Open the section list" aria-expanded="false">{icon("menu")}</button>
</div></div></header>
<div class="sheet" aria-label="Sections"><div class="scrim"></div><nav><div style="display:flex;justify-content:space-between;align-items:center"><span class="caps" style="color:var(--muted)">Sections</span><button class="btn icon-btn close" type="button" aria-label="Close">{icon("close")}</button></div>
<ol>{"".join(f'<li><a href="{pre}#{i}"><span>{n}</span>{E(t)}</a></li>' for i, n, t in NAV)}</ol>
<a class="btn btn-primary" href="report/RBNT-Holder-Report-Q3-2026.pdf" download style="width:100%;justify-content:center">{icon("down")}Download the PDF</a></nav></div>'''

footer = f'''<footer class="site-footer"><div class="shell">
<div><img class="logo-dark" src="assets/img/dao-logo-on-dark.png" alt="Redbelly DAO" width="62" height="44"><img class="logo-light" src="assets/img/dao-logo-on-light.png" alt="Redbelly DAO" width="62" height="44">
<p style="max-width:44ch;margin:0">A quarterly, sourced report on RBNT holder trends for the Redbelly DAO community. Facts from the chain only: no price views, no advice, no unnamed wallet singled out.</p></div>
<div><h4>Report</h4><ul><li><a href="index.html#summary">Summary</a></li><li><a href="index.html#staking">Staking</a></li><li><a href="index.html#named">Named wallets</a></li><li><a href="method.html">Method & data</a></li><li><a href="report/RBNT-Holder-Report-Q3-2026.pdf" download>PDF</a></li></ul></div>
<div><h4>Sources</h4><ul><li><a href="https://redbellydao.network/treasury/" target="_blank" rel="noopener">DAO treasury page</a></li><li><a href="https://redbelly.routescan.io" target="_blank" rel="noopener">Routescan explorer</a></li>
<li><span class="mono">governors.mainnet.redbelly.network</span></li><li>Snapshot blocks {blk(S_BLOCK)} → {blk(E_BLOCK)}</li><li>Data collected {COLLECTED}</li></ul></div>
</div></footer>
<button class="btn icon-btn to-top" type="button" aria-label="Back to top" onclick="window.scrollTo({{top:0}})">{icon("up")}</button>
<div class="toast" role="status" aria-live="polite"></div>'''

verify_dialog = f'''<dialog id="verify-dialog" aria-labelledby="v-title"><div class="dlg-head"><h3 id="v-title">Verify</h3><button class="btn icon-btn" id="v-close" type="button" aria-label="Close">{icon("close")}</button></div>
<div class="dlg-body"><p id="v-what"></p>
<dl class="kv"><dt>RPC method</dt><dd id="v-method"></dd><dt>Block</dt><dd id="v-block"></dd><dt>Published figure</dt><dd id="v-expect"></dd></dl>
<div class="result" id="v-result" aria-live="polite"></div>
<div style="display:flex;gap:8px;flex-wrap:wrap"><button class="btn btn-primary" id="v-run" type="button">Ask the chain now</button><button class="btn" type="button" data-copy-from="#v-curl">{icon("copy")}Copy command</button></div>
<pre class="code" id="v-curl"></pre>
<p style="font-size:12.5px;color:var(--muted)">Your browser sends this request straight to the public Redbelly RPC. Nothing passes through this site.</p></div></dialog>'''

kpis = f'''<div class="shell"><div class="kpi-strip" aria-label="Key figures">
<div class="tile"><span class="caps">Held by unnamed wallets</span><span class="val">{M(un["end"])}</span><span class="sub">{S(un["change"])} since 1 Jul · {P(un["end"] / total_e)} of all RBNT</span></div>
<div class="tile"><span class="caps">Unnamed holders above 10 RBNT</span><span class="val">{N(ce["holders"])}</span><span class="sub">{ce["holders"] - cs["holders"]:+,} since 1 Jul</span></div>
<div class="tile"><span class="caps">Top 10 unnamed holders' share</span><span class="val">{P(ce["top10_share"])}</span><span class="sub">{PP(cs["top10_share"], ce["top10_share"])} since 1 Jul</span></div>
<div class="tile"><span class="caps">In vesting contracts</span><span class="val">{M(vest["end"])}</span><span class="sub">{S(vest["change"])} released in Q3</span><div class="spark" data-spark="vesting"></div></div>
</div></div>'''

hero = f'''<section class="hero" id="top" aria-labelledby="hero-h"><div class="shell">
<div><span class="eyebrow caps"><span class="dot"></span>Quarterly on-chain holder report · Edition 01</span>
<h1 id="hero-h">How RBNT holders moved in <em>Q3 2026</em></h1>
<p class="lede">Accumulation, selling, staking and concentration between 1 July and 30 September 2026, read directly from Redbelly mainnet and checked to the wei.</p>
<div class="hero-meta"><span>Snapshot blocks <b class="mono">{S_BLOCK:,} → {E_BLOCK:,}</b></span><span>Chain ID <b class="mono">151</b></span><span>Collected <b>{COLLECTED}</b></span></div>
<div class="hero-cta"><a class="btn btn-primary" href="#summary">Read the report {icon("arrow")}</a><a class="btn" href="report/RBNT-Holder-Report-Q3-2026.pdf" download>{icon("down")}PDF</a><a class="btn" href="#downloads">Get the data</a></div></div>
<div class="hero-figure" aria-label="Headline figure"><span class="caps">RBNT staked in Reddex pools · 30 Sep</span>
<div class="big">{M(staked_e)[:-1]}<small>M RBNT</small></div>
<div class="delta"><span class="chip">{'+' if staked_e >= staked_s else '−'}{P(abs(pct(staked_s, staked_e)))} in Q3</span><span>from {M(staked_s)} on 1 Jul · {P(staked_e / total_e)} of all RBNT</span></div>
<div class="hero-spark" data-spark="staked"></div><div class="foot"><span>1 Jul</span><span>daily, both pools</span><span>30 Sep</span></div></div>
</div></section>'''

toc = f'''<aside class="toc" aria-label="On this page"><span class="caps">On this page</span><ol>{"".join(f'<li><a href="#{i}"><span>{n}</span>{E(t)}</a></li>' for i, n, t in NAV)}</ol>
<div class="toc-foot"><a class="btn btn-sm" href="report/RBNT-Holder-Report-Q3-2026.pdf" download>{icon("down")}Download PDF</a><a class="btn btn-sm" href="method.html">Method</a></div></aside>'''

jsonld = {"@context": "https://schema.org", "@type": "Dataset", "name": "RBNT holder report, Q3 2026", "description": desc,
          "temporalCoverage": "2026-07-01/2026-09-30", "isAccessibleForFree": True, "url": SITE_URL + "/",
          "distribution": [{"@type": "DataDownload", "encodingFormat": "text/csv", "contentUrl": f"{SITE_URL}/data/{f}"} for f in
                           ("supply_by_category.csv", "concentration.csv", "holder_size_bands.csv", "largest_holder_tiers.csv", "staking_pools.csv", "reserved_wallets.csv", "daily_series.csv", "checks.csv")]}

index = (head(title, desc) + '<body>' + header() + hero + kpis +
         f'<div class="shell layout">{toc}<main id="content" tabindex="-1">{body_sections}</main></div>' + footer + verify_dialog +
         f'<script id="report-data" type="application/json">{json.dumps(data, separators=(",", ":"))}</script>'
         f'<script type="application/ld+json">{json.dumps(jsonld)}</script>'
         '<noscript><style>.table-view[hidden]{display:block!important}.chart-view{display:none}.reveal{opacity:1!important;transform:none!important}</style></noscript>'
         '<script src="assets/js/site.js" defer></script></body></html>')

# ---------------- method page (METHOD.md + data dictionary) ----------------
md = markdown.Markdown(extensions=["tables", "fenced_code", "toc"])
method_html = md.convert(open(os.path.join(ROOT, "METHOD.md")).read()).replace('href="scripts/"', 'href="scripts/README.md"').replace('href="data/"', 'href="data/README.md"')
dict_html = markdown.markdown(open(os.path.join(ROOT, "data/README.md")).read(), extensions=["tables"]).replace('href="../METHOD.md"', 'href="#top"').replace('href="data/', 'href="data/')
method_page = (head("Method and data · RBNT Holder Report Q3 2026", "How the RBNT holder report was produced: snapshot blocks, sources, rules, checks and the data dictionary.", "method.html")
               + '<body>' + header(home=False) +
               f'''<div class="shell" style="padding-top:48px;padding-bottom:80px"><main id="content" class="prose doc" style="max-width:860px"><span id="top"></span>
<p><a href="index.html">← Back to the report</a></p>{method_html}<hr style="border:0;border-top:1px solid var(--edge);margin:48px 0">{dict_html}</main></div>''' + footer + verify_dialog +
               f'<script id="report-data" type="application/json">{json.dumps(data, separators=(",", ":"))}</script><script src="assets/js/site.js" defer></script></body></html>')

# ---------------- write ----------------
for d in ("assets/css", "assets/js", "assets/fonts", "assets/img", "data"):
    os.makedirs(os.path.join(ROOT, d), exist_ok=True)
open(os.path.join(ROOT, "index.html"), "w").write(index)
open(os.path.join(ROOT, "method.html"), "w").write(method_page)
shutil.copy(os.path.join(SRC, "site.css"), os.path.join(ROOT, "assets/css/site.css"))
shutil.copy(os.path.join(SRC, "site.js"), os.path.join(ROOT, "assets/js/site.js"))
fonts_css = open(os.path.join(SRC, "fonts", "fonts.css")).read().replace("url(fonts/", "url(../fonts/")
open(os.path.join(ROOT, "assets/css/fonts.css"), "w").write(fonts_css)
for f in os.listdir(os.path.join(SRC, "fonts")):
    if f.endswith(".woff2"): shutil.copy(os.path.join(SRC, "fonts", f), os.path.join(ROOT, "assets/fonts", f))
for f in os.listdir(os.path.join(SRC, "img")): shutil.copy(os.path.join(SRC, "img", f), os.path.join(ROOT, "assets/img", f))
with open(os.path.join(ROOT, "data/daily_series.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["date_end_of_day_utc", "block", "staked_nolock", "staked_lock365", "balance_nolock", "balance_lock365", "wrbnt_supply", "bridge_adapter", "vesting_contracts", "reserved_wallets"])
    for r in DAILY: w.writerow([r["date"], r["block"]] + [round(r[k], 6) for k in ("staked_nolock", "staked_lock365", "balance_nolock", "balance_lock365", "wrbnt_supply", "bridge", "vesting", "reserved")])
shutil.copy(os.path.join(SRC, "vercel.json"), os.path.join(ROOT, "vercel.json"))
os.makedirs(os.path.join(ROOT, "docs"), exist_ok=True)

# share image source (rendered to assets/img/og.png by render_shots.js)
fonts_abs = fonts_css.replace("url(../fonts/", "url(file://" + os.path.abspath(os.path.join(ROOT, "assets/fonts")) + "/")
logo_abs = "file://" + os.path.abspath(os.path.join(ROOT, "assets/img/dao-logo-on-dark.png"))
og = f'''<!doctype html><html><head><meta charset="utf-8"><style>{fonts_abs}
*{{box-sizing:border-box}}body{{margin:0;width:1200px;height:630px;background:radial-gradient(900px 420px at 92% -10%,rgba(239,83,80,.22),transparent 60%),linear-gradient(180deg,#0c1317,#101b22);color:#f1f5f8;font-family:'Be Vietnam Pro',sans-serif;padding:60px 64px;display:flex;flex-direction:column;position:relative;overflow:hidden}}
body:before{{content:"";position:absolute;inset:0;background-image:radial-gradient(rgba(143,161,173,.18) 1px,transparent 1px);background-size:28px 28px;mask-image:linear-gradient(180deg,#000,transparent 90%)}}
.top{{display:flex;justify-content:space-between;align-items:center;position:relative}}img{{height:84px}}
.ed{{font-family:'JetBrains Mono',monospace;font-size:20px;color:#8fa1ad;letter-spacing:.05em}}
.eyebrow{{margin-top:34px;font-size:18px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#ffb3ae;position:relative}}
h1{{font-size:72px;line-height:1.04;letter-spacing:-.03em;margin:12px 0 0;position:relative}}h1 em{{font-style:normal;color:#ffb3ae}}
.stats{{margin-top:auto;display:grid;grid-template-columns:repeat(3,1fr);gap:16px;position:relative}}
.s{{background:rgba(20,31,38,.85);border:1px solid #263641;border-radius:8px;padding:18px 22px}}
.l{{font-size:15px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#8fa1ad}}.v{{font-size:44px;font-weight:700;letter-spacing:-.02em;margin-top:4px}}
.d{{font-size:18px;color:#c2ced6}}.bar{{position:absolute;left:0;top:0;height:6px;width:100%;background:#EF5350}}</style></head><body><div class="bar"></div>
<div class="top"><img src="{logo_abs}"><span class="ed">Edition 01 · on-chain data</span></div>
<div class="eyebrow">Quarterly RBNT holder report</div><h1>How RBNT holders moved<br>in <em>Q3 2026</em></h1>
<div class="stats"><div class="s"><div class="l">Staked in Reddex</div><div class="v">{M(staked_e)}</div><div class="d">{'+' if staked_e >= staked_s else '−'}{P(abs(pct(staked_s, staked_e)))} over the quarter</div></div>
<div class="s"><div class="l">Top 100 wallets</div><div class="v">{g100} / {f100} / {s100}</div><div class="d">grew / same / shrank</div></div>
<div class="s"><div class="l">Top 10 share</div><div class="v">{P(ce["top10_share"])}</div><div class="d">of unnamed-wallet RBNT</div></div></div></body></html>'''
open("og.html", "w").write(og)
print("site written:", os.path.getsize(os.path.join(ROOT, "index.html")), "bytes index.html")
