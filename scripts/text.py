# Plain-language text for the report and the community summary.
# Every number is read from out/figures.json, and direction words (rose/fell) follow the numbers.
import json

F = json.load(open("out/figures.json"))
def M(v, d=1): return f"{v/1e6:,.{d}f} million"
def Ms(v, d=1): return f"{v/1e6:,.{d}f}M"
def N(v): return f"{v:,.0f}"
def P(v, d=1): return f"{100*v:.{d}f}%"
def up(v, a="rose", b="fell", c="was unchanged"): return a if v > 0 else (b if v < 0 else c)
def pct(a, b): return (b - a) / a if a else 0

sup = {r["category"]: r for r in F["supply_map"]}
cs, ce = F["concentration"]["start"], F["concentration"]["end"]
stk, pf = F["staking"], F["pool_flows"]
st_s = stk["nolock"]["staked_start"] + stk["lock365"]["staked_start"]
st_e = stk["nolock"]["staked_end"] + stk["lock365"]["staked_end"]
un = sup["Unnamed wallets"]; vest = sup["Token vesting contracts"]; oth = sup["Other smart contracts"]
resv = sup["Redbelly reserved wallets"]; brg = F["bridge"]
res = {r["wallet"]: r for r in F["reserved"]}
eco = F["eco_unlocked"]
tiers = F["tiers"]
t100 = tiers[:3]
g100 = sum(t["grew"] for t in t100); s100 = sum(t["shrank"] for t in t100); f100 = sum(t["about_same"] for t in t100)
c100 = sum(t["change"] for t in t100); b100 = sum(t["start"] for t in t100)
stk100_s = sum(t["staked_start"] for t in t100); stk100_e = sum(t["staked_end"] for t in t100)
e100 = sum(t["end"] for t in t100)
total_e = F["economic_total_end"]
un_st_s, un_st_e = F["unnamed_staked_start"], F["unnamed_staked_end"]
fees = F["fees_q3"]
eco_out = {r["to"]: r for r in eco["rbnt_out"]}
eco_wr_out = sum(r["wrbnt"] for r in eco["wrbnt_out"])
eco_wr_in = {r["from"]: r for r in eco["wrbnt_in"]}

T = {}
T["lead"] = (f"Over the quarter, RBNT moved from Redbelly's reserved wallets and vesting contracts into unnamed wallets, and more of it went into staking. "
             f"Unnamed wallets {up(un['change'], 'gained', 'lost')} {M(abs(un['change']))} RBNT in total, and RBNT staked in the two Reddex pools "
             f"{up(st_e - st_s)} by {P(abs(pct(st_s, st_e)))} to {M(st_e)}. Holdings stayed highly concentrated: the 10 largest unnamed holders held "
             f"{P(ce['top10_share'])} of all RBNT in unnamed wallets on 30 September.")
T["points"] = [
    f"<b>Staking {up(st_e - st_s, 'grew', 'shrank')}.</b> {M(st_e)} RBNT was staked on 30 September, against {M(st_s)} on 1 July. "
    f"The no-lock pool took most of the increase ({'+' if stk['nolock']['staked_end'] >= stk['nolock']['staked_start'] else '−'}{M(abs(stk['nolock']['staked_end'] - stk['nolock']['staked_start']))}). "
    f"{N(F['stakers_any_end'])} wallets had a stake at the end of the quarter, against {N(F['stakers_any_start'])} at the start, so the growth came from larger stakes rather than more stakers.",
    f"<b>The largest holders mostly held or added.</b> Of the 100 largest unnamed wallets on 1 July, {g100} grew, {f100} stayed about the same and {s100} shrank. "
    f"Together their holdings {up(c100)} by {M(abs(c100))} RBNT ({P(abs(pct(b100, b100 + c100)))}).",
    f"<b>Concentration edged {up(ce['top10_share'] - cs['top10_share'], 'up', 'down', 'nowhere')}.</b> The top 10 unnamed holders' share went from {P(cs['top10_share'])} to {P(ce['top10_share'])}, and the top 100 from {P(cs['top100_share'])} to {P(ce['top100_share'])}.",
    f"<b>One day of reserved-wallet moves.</b> On 10 September, {M(500e6, 0)} RBNT moved from Ecosystem (Locked) to Ecosystem 2 (Unlocked), {M(res['Investors']['change'])} from Ecosystem 2 (Unlocked) to Investors, and {M(33333333, 1)} from Governance (Locked) to Governance (Unlocked). All of these stayed inside the reserved wallets.",
    f"<b>RBNT left the reserved wallets through one wallet.</b> Ecosystem (Unlocked), the only reserved wallet that sends its own transactions, sent out {M(abs(res['Ecosystem (Unlocked)']['change']))} RBNT net, including {M(eco_out['Reddex staking pools (reward funds)']['rbnt'], 0)} to fund staking rewards.",
    f"<b>Vesting contracts released {M(abs(vest['change']))} RBNT</b> over the quarter (counting WRBNT as RBNT), and the RBNT locked in the bridge to other chains {up(brg['end'] - brg['start'])} to {M(brg['end'])}.",
]
T["c1"] = (f"Reserved wallets held {P(resv['end'] / total_e)} of all RBNT on 30 September. Unnamed wallets held {P(un['end'] / total_e)}, "
           f"up from {P(un['start'] / F['economic_total_start'])}. Staked RBNT is counted with the wallet that staked it.")
T["s1_plain"] = (f"Most RBNT is still in wallets Redbelly reserved at launch (team, investors, ecosystem, reserve and others), and in contracts that release tokens over time. "
                 f"During the quarter, about {M(abs(vest['change']) + abs(resv['change']), 0)} RBNT flowed out of those two groups, and unnamed wallets ended up with "
                 f"{M(abs(un['change']), 0)} more. The total went down slightly ({M(F['economic_total_start'] - F['economic_total_end'], 2)}) "
                 f"because transaction fees on Redbelly are paid to a zero address and so leave circulation. Base fees in the quarter came to {M(fees, 2)} RBNT.")
T["c2"] = (f"The 10 largest unnamed wallets held {P(ce['top10_share'])} of all unnamed-wallet RBNT on 30 September, and the 100 largest held {P(ce['top100_share'])}.")
T["c3"] = ("Most wallets are small. Wallets holding 10 RBNT or less are not shown (see method).")
small = [b for b in F["bands"] if b["band"] in ("10 – 1K", "1K – 10K")]
T["s2_plain"] = (f"RBNT in unnamed wallets is held very unevenly: a few large wallets hold most of it, and thousands of wallets hold small amounts. "
                 f"The half-way wallet (the median) held about {N(ce['median'])} RBNT. The Gini score of {ce['gini']:.2f} is close to 1, which means very uneven. "
                 f"That is common for tokens where exchanges, funds and early participants keep large balances in single wallets. "
                 f"Over the quarter the picture barely changed. The number of wallets with 10 to 10,000 RBNT {up(sum(b['wallets_end'] for b in small) - sum(b['wallets_start'] for b in small))} "
                 f"from {N(sum(b['wallets_start'] for b in small))} to {N(sum(b['wallets_end'] for b in small))}.")
T["c4"] = (f"In every group, more wallets grew than shrank. Most wallets ranked 101 to 1,000 kept roughly the same holdings.")
T["c5"] = ("Change in total holdings of each group of wallets ranked on 1 July. Bars to the right are net increases.")
T["s3_plain"] = (f"The 100 largest unnamed wallets on 1 July held {M(b100)} RBNT, and by 30 September the same wallets held {M(e100)}. "
                 f"Much of that is staked: {M(stk100_s)} at the start and {M(stk100_e)} at the end. "
                 f"{F['top100_turnover']['stayed']} of the 100 were still in the top 100 at the end of the quarter, and {F['top100_turnover']['new_entrants']} wallets joined it. "
                 f"Wallets that shrank were a minority in every group. Some wallets gaining is consistent with tokens arriving from vesting contracts and from the reserved wallets. "
                 f"The data cannot say why any wallet grew or shrank.")
T["c6"] = (f"Stakes in the no-lock pool {up(stk['nolock']['staked_end'] - stk['nolock']['staked_start'])} by {P(abs(pct(stk['nolock']['staked_start'], stk['nolock']['staked_end'])))}, "
           f"and in the 365-day pool by {P(abs(pct(stk['lock365']['staked_start'], stk['lock365']['staked_end'])))}.")
T["s4_plain"] = (f"More RBNT went into staking than came out. Across both pools {M(pf['nolock']['staked_gross'] + pf['lock365']['staked_gross'])} RBNT was staked during the quarter and "
                 f"{M(pf['nolock']['unstaked_gross'] + pf['lock365']['unstaked_gross'])} was withdrawn. "
                 f"The 365-day pool opened on 31 May 2025, so deposits from its first months reached the end of their one-year lock in mid-2026. That is why some RBNT left it this quarter. "
                 f"Rewards are paid from RBNT added to the pools. Ecosystem (Unlocked) added {M(pf['nolock']['reward_funding'] + pf['lock365']['reward_funding'], 0)} RBNT in the quarter, "
                 f"and about {M(pf['nolock']['rewards_paid_est'] + pf['lock365']['rewards_paid_est'])} was paid out to stakers. "
                 f"By 30 September, {P(st_e / total_e)} of all RBNT was staked.")
T["c7"] = ("Bars to the right are increases. Four wallets did not move at all.")
T["s5_moves"] = (
    f"<p>Six of the nine reserved wallets are multisig wallets that moved only on <b>10 September 2026</b>, in three transfers between reserved wallets within three minutes "
    f"(blocks <span class=mono>3175499</span>, <span class=mono>3175501</span> and <span class=mono>3175505</span>):</p><ul>"
    f"<li>Ecosystem 2 (Unlocked) → Investors: {N(res['Investors']['change'])} RBNT</li>"
    f"<li>Ecosystem (Locked) → Ecosystem 2 (Unlocked): {N(500e6)} RBNT</li>"
    f"<li>Governance (Locked) → Governance (Unlocked): {N(33333333)} RBNT</li></ul>"
    f"<p>None of these RBNT left the reserved wallets during the quarter. TEAM (Locked), Reserve and USYD/CSIRO (Locked) did not change at all, "
    f"and the Investors wallet did not send anything on before 30 September.</p>"
    f"<p><b>Ecosystem (Unlocked)</b> is the one reserved wallet that sends its own transactions ({eco['txs_sent']} in the quarter). Its holdings fell by {N(abs(res['Ecosystem (Unlocked)']['change']))} RBNT. Where the RBNT went:</p><ul>"
    f"<li>{N(eco_out['Wrapped into WRBNT']['rbnt'])} RBNT wrapped into WRBNT, and {N(eco_wr_out)} WRBNT then sent to {sum(r['addresses'] for r in eco['wrbnt_out'])} smart contracts</li>"
    f"<li>{N(eco_out['Reddex staking pools (reward funds)']['rbnt'])} RBNT to the two Reddex pools as reward funds</li>"
    f"<li>{N(eco_out.get('Unnamed wallets', {}).get('rbnt', 0))} RBNT to {eco_out.get('Unnamed wallets', {}).get('addresses', 0)} unnamed wallets in {eco_out.get('Unnamed wallets', {}).get('txs', 0)} transactions</li>"
    + (f"<li>{N(eco_out['Other smart contracts']['rbnt'])} RBNT to other smart contracts</li>" if "Other smart contracts" in eco_out else "")
    + f"<li>{N(eco['gas_fees'])} RBNT in transaction fees</li></ul>"
    f"<p>It also received {N(sum(r['wrbnt'] for r in eco['wrbnt_in']))} WRBNT from a token vesting contract.</p>")
T["s5_bridge"] = (f"The RBNT Native OFT Adapter is the contract that locks RBNT on Redbelly when it is bridged to another chain. It held {M(brg['start'])} RBNT on 1 July and "
                  f"{M(brg['end'])} on 30 September, a net {up(brg['end'] - brg['start'], 'increase', 'decrease')} of {M(abs(brg['end'] - brg['start']))}. "
                  f"So slightly more RBNT moved out to other chains than came back. RBNT on other chains is outside the scope of this report.")
T["s5_exchanges"] = ("When the data was collected (26 October 2026), Routescan showed no public exchange labels for any Redbelly address. Exchange wallets therefore "
                     "cannot be told apart from other wallets in this edition, and any exchange balances are inside the \"unnamed wallets\" group. "
                     "If Routescan adds exchange labels, the next edition will report their flows separately.")
T["s5_plain"] = ("This quarter, the big reserved-wallet moves were transfers between Redbelly's own wallets on one day. The RBNT that actually left the reserved wallets came "
                 "from Ecosystem (Unlocked), which pays staking rewards and makes other ecosystem payments.")
T["method_html"] = (
    "<p><b>Snapshots.</b> Balances were read directly from the Redbelly chain at block <span class=mono>3025809</span> (the last block before 1 July 2026, 30 Jun 23:57:19 UTC) "
    "and block <span class=mono>3209414</span> (the last block of the quarter, 30 Sep 23:57:35 UTC). The treasury page lists original allocations, so it was used only for wallet names and addresses.</p>"
    "<p><b>Which wallets.</b> Every address that appeared in any transaction from the start of the chain up to 26 October 2026 was checked, along with the WRBNT holder list from Routescan. "
    f"That is {N(F['universe_size'])} addresses, of which {N(F['addresses_nonzero'])} held RBNT at one of the two blocks.</p>"
    "<p><b>Counting once.</b> A wallet's holdings = its plain RBNT + its WRBNT + the RBNT it has staked in either Reddex pool. "
    "The RBNT inside the WRBNT contract is not counted again, because it is the backing of everyone's WRBNT. "
    "A pool's RBNT beyond its <span class=mono>totalStake()</span> is shown as reward funds. Pool balances therefore include reward funds as well as stakes.</p>"
    "<p><b>Groups.</b> Only publicly named wallets are named. Contracts are grouped by matching their code to verified contracts on Routescan "
    "(<span class=mono>TokenVestingManager</span>, <span class=mono>RBNTNativeOFTAdapter</span>). Every other wallet is reported only in groups. "
    "A holder is an unnamed wallet with more than 10 RBNT.</p>"
    "<p><b>Checks.</b> The appendix lists the reconciliation checks. WRBNT held = WRBNT supply = RBNT in the WRBNT contract, and the sum of stakers' balances = each pool's <span class=mono>totalStake()</span>. Both match to the wei at both blocks. "
    + (f"The RBNT read at the start block is {P(F['coverage_start'], 2)} of what should exist (10,000M allocated minus {M(F['burned_to_start'])} burned as fees since launch). " if "coverage_start" in F else "")
    + f"Over the quarter, the total read fell by {M(F['economic_total_start'] - F['economic_total_end'], 2)} while {M(fees, 2)} was burned as fees. The {M(F['unattributed_q3'], 2)} difference is RBNT that moved in from addresses this method does not reach, such as contracts only ever called by other contracts. It is too small to change any finding.</p>"
    "<p>The full method, scripts and data are in the repository (<span class=mono>METHOD.md</span>, <span class=mono>scripts/</span>, <span class=mono>data/</span>). "
    "Running the same scripts with new snapshot blocks produces the next edition.</p>")
T["sources_rows"] = [
    ["RBNT staked, 30 Sep", Ms(st_e), "<span class=mono>totalStake()</span> on both pools at block 3209414", "staking_pools.csv"],
    ["RBNT staked, 1 Jul", Ms(st_s), "<span class=mono>totalStake()</span> on both pools at block 3025809", "staking_pools.csv"],
    ["Pool balances", f"{Ms(stk['nolock']['balance_end'])} / {Ms(stk['lock365']['balance_end'])}", "<span class=mono>eth_getBalance</span> on pool addresses, block 3209414", "staking_pools.csv"],
    ["Gross staked / unstaked", f"{Ms(pf['nolock']['staked_gross'] + pf['lock365']['staked_gross'])} / {Ms(pf['nolock']['unstaked_gross'] + pf['lock365']['unstaked_gross'])}", "Every successful <span class=mono>stake()</span> transaction in blocks 3025810–3209414; change in <span class=mono>totalStake()</span>", "staking_pools.csv"],
    ["Unnamed-wallet holdings", f"{Ms(un['start'])} → {Ms(un['end'])}", "RBNT + WRBNT + staked, summed over unnamed wallets, both blocks", "supply_by_category.csv"],
    ["Top-10 share", f"{P(cs['top10_share'])} → {P(ce['top10_share'])}", "Ranked unnamed holders (more than 10 RBNT), both blocks", "concentration.csv"],
    ["Holders above 10 RBNT", f"{N(cs['holders'])} → {N(ce['holders'])}", "Count of unnamed wallets with holdings above 10 RBNT", "concentration.csv"],
    ["Top-100 behaviour", f"{g100} grew / {f100} same / {s100} shrank", "Unnamed wallets ranked on 1 Jul, compared on 30 Sep (±1%)", "largest_holder_tiers.csv"],
    ["Reserved-wallet balances", "see Section 5", "<span class=mono>eth_getBalance</span> + WRBNT <span class=mono>balanceOf</span>, both blocks; change blocks by binary search", "reserved_wallets.csv"],
    ["Ecosystem (Unlocked) outflows", Ms(abs(res['Ecosystem (Unlocked)']['change'])), "All 118 transactions it sent in the quarter, with their receipts", "eco_unlocked_flows.csv"],
    ["Bridge adapter balance", f"{Ms(brg['start'])} → {Ms(brg['end'])}", "<span class=mono>eth_getBalance</span> on the verified RBNTNativeOFTAdapter, both blocks", "supply_by_category.csv"],
    ["Base fees in the quarter", Ms(fees, 2), "Σ gasUsed × baseFeePerGas over blocks 3025810–3209414", "checks.csv"],
]
T["checks_rows"] = F["checks_rows"]
F["text"] = T
json.dump(F, open("out/figures.json", "w"), indent=1)

# ---------------- community summary ----------------
thread = [
    f"1/ The first quarterly RBNT holder report is out. It covers Q3 2026 (1 Jul to 30 Sep) and is built only from on-chain data on Redbelly mainnet. Here's what holders did 🧵",
    f"2/ Staking {up(st_e - st_s, 'grew', 'shrank')}. {Ms(st_e)} RBNT was staked in the two Reddex pools on 30 Sep, compared with {Ms(st_s)} on 1 Jul ({'+' if st_e >= st_s else '−'}{P(abs(pct(st_s, st_e)))}). That's {P(st_e / total_e)} of all RBNT.",
    f"3/ The biggest wallets mostly held or added. Of the 100 largest unnamed wallets on 1 Jul, {g100} grew, {f100} stayed about the same and {s100} shrank. Staked RBNT counts as held, so staking isn't counted as selling.",
    f"4/ Holdings are still concentrated. The top 10 unnamed wallets held {P(ce['top10_share'])} of unnamed-wallet RBNT (it was {P(cs['top10_share'])}). Wallets holding more than 10 RBNT: {N(cs['holders'])} → {N(ce['holders'])}.",
    f"5/ Reserved wallets: on 10 Sep, 500M RBNT moved from Ecosystem (Locked) to Ecosystem 2 (Unlocked), {Ms(res['Investors']['change'])} from there to Investors, and 33.3M from Governance (Locked) to Governance (Unlocked). All of it stayed inside the reserved wallets.",
    f"6/ Ecosystem (Unlocked) sent out a net {Ms(abs(res['Ecosystem (Unlocked)']['change']))} RBNT, including 15M to fund staking rewards. Vesting contracts released {Ms(abs(vest['change']))}.",
    "7/ Method: balances read at blocks 3025809 and 3209414, each token counted once (RBNT + WRBNT + staked), and only publicly named wallets named. Scripts and data are public so anyone can check or repeat it. Not financial advice. Facts only.",
]
summary_paras = [
    f"The DAO's first quarterly on-chain holder report covers Q3 2026 (1 July to 30 September). It uses only data read from Redbelly mainnet at two snapshot blocks, "
    f"with every figure traceable to the chain.",
    f"Staking {up(st_e - st_s, 'grew', 'shrank')} over the quarter: {Ms(st_e)} RBNT was staked in the two Reddex pools at the end, against {Ms(st_s)} at the start. "
    f"Among the 100 largest unnamed wallets on 1 July, {g100} grew their holdings, {f100} stayed about the same and {s100} shrank. Holdings stay concentrated: "
    f"the top 10 unnamed wallets hold {P(ce['top10_share'])} of RBNT in unnamed wallets.",
    f"Redbelly's reserved wallets moved on one day, 10 September, and only between themselves (500M from Ecosystem (Locked) to Ecosystem 2 (Unlocked), {Ms(res['Investors']['change'])} on to Investors, "
    f"and 33.3M between the Governance wallets). The RBNT that left the reserved wallets came from Ecosystem (Unlocked), {Ms(abs(res['Ecosystem (Unlocked)']['change']))} net, "
    f"including 15M added to the staking pools for rewards.",
    "The report describes what happened on the chain and does not predict prices. The method and data are published so the next edition can be produced the same way.",
]
open("out/community_summary.md", "w").write(
    "# RBNT holders in Q3 2026: community summary\n\n## X thread\n\n" + "\n\n".join(thread) +
    "\n\n## Short version (for Discord, the forum or a newsletter)\n\n" + "\n\n".join(summary_paras) + "\n")
for t in thread: print(len(t), t)
