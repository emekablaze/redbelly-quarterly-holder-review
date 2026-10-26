# Redbelly quarterly holder review

A regular, sourced report on how RBNT holders behave on Redbelly mainnet (chain ID 151): accumulation, selling, staking and how concentrated holdings are. This first edition covers **Q3 2026 (1 July to 30 September 2026)** and sets the method that later editions repeat.

## What is in this repository

| Path | What it is |
|---|---|
| `index.html` | Landing page (homepage when the repository is served as a static site, e.g. on Vercel) |
| `report/RBNT-Holder-Report-Q3-2026.pdf` | **The report** (A4, with charts) |
| `report/RBNT-Holder-Report-Q3-2026.html` | The same report as a single self-contained web page |
| `community/community-summary.md` | **Community summary**: an X thread and a short version in a few paragraphs |
| `data/` | **The data behind every chart and table** (CSV), plus `figures.json` with every number the report quotes |
| `METHOD.md` | **Method and sources**: snapshot blocks, data sources, rules, checks, limits, and how to produce the next edition |
| `scripts/` | The scripts that produced everything, in run order (see `scripts/README.md`) |
| `assets/` | Brand fonts (Be Vietnam Pro, JetBrains Mono, both open-licence) and the DAO logo, from the Task Board brand kit |

## Headline figures, Q3 2026

All figures are read from the chain at block `3025809` (30 Jun 2026 23:57 UTC) and block `3209414` (30 Sep 2026 23:57 UTC). See `data/` and the appendix of the report for where each one comes from.

| Measure | 1 Jul 2026 | 30 Sep 2026 |
|---|---|---|
| RBNT staked in the two Reddex pools | 635.8M | 751.3M |
| Wallets with a stake | 1,268 | 1,255 |
| RBNT held by unnamed wallets (incl. WRBNT and stakes) | 1,783.0M | 1,922.1M |
| Unnamed holders with more than 10 RBNT | 14,441 | 14,552 |
| Top 10 / top 100 share of unnamed-wallet RBNT | 48.4% / 76.6% | 49.3% / 77.4% |
| Redbelly reserved wallets | 5,974.8M | 5,931.0M |
| Token vesting contracts | 1,520.0M | 1,446.1M |

Of the 100 largest unnamed wallets on 1 July, **43 grew, 49 stayed about the same and 8 shrank** by 30 September (staked RBNT counts as held).

## Ground rules this report follows

* **Trends, not people.** Only publicly named wallets are named: the nine reserved wallets on the DAO treasury page, the Wrapped RBNT contract, the two Reddex staking pools, and contracts with a public name on Routescan. Every other wallet appears only inside groups. The data files hold no addresses of unnamed wallets.
* **Each token counted once.** Holdings = plain RBNT + WRBNT + RBNT staked in a Reddex pool. The RBNT backing WRBNT is not counted a second time.
* **No predictions.** The report describes what happened on the chain. It contains no price views and no advice.

## Checking a figure

Every row in `data/checks.csv` must show `PASS` (rows marked `INFO` are reconciliation notes). To check any balance yourself, ask the public RPC:

```bash
curl -s -X POST https://governors.mainnet.redbelly.network -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"eth_getBalance","params":["0x7473fEAf836b5319D9190d8367991Dc6ef33C16d","0x30f8c6"]}'
# Reserve wallet at block 3209414 (0x30f8c6) -> 0x6765c793fa10079d0000000 = 2,000,000,000 RBNT
```

## Data sources

* Redbelly mainnet RPC: `https://governors.mainnet.redbelly.network`
* Routescan explorer and API: `https://redbelly.routescan.io`, `https://api.routescan.io/v2/network/mainnet/evm/151/etherscan/api`
* DAO treasury page: `https://redbellydao.network/treasury/`
* Task Board brand kit: `https://taskboard.redbellydao.network/brand`
