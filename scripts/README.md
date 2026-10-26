# Scripts: from the chain to the published report

Every number in the report, the website, the CSVs, `METHOD.md` and the repository README comes out of these scripts. Run them in one working folder, outside the repository:

```bash
pip install pycryptodome markdown          # Keccak hashes; Markdown for the method page
npm i -g playwright                        # only for the PDF and screenshots (Chromium)
mkdir work && cd work
```

The snapshot blocks are set at the top of each script (`S = 3025809`, `E = 3209414`). For a new quarter, change them everywhere (`grep -rn 3025809 ../scripts`).

## Run order

| # | Command | Writes | What it does |
|---|---|---|---|
| 1 | `python3 ../scripts/get_treasury.py` | `treasury_table.json` | Reserved wallets, from the DAO treasury page |
| 2 | `python3 ../scripts/scan_chunks.py 0 <head> chunks` | `chunks/*.json` | Every transaction (block, time, hash, from, to, value, selector). Resumable; several copies can run on different ranges |
| 3 | `python3 ../scripts/scan_addrs.py 0 <head> addr_chunks` | `addr_chunks/*.json` | Every address a transaction touches or names in its data (ABI arguments, `bytes`/text addresses, multisig batches) |
| 4 | `python3 ../scripts/paginate2.py "/v2/network/mainnet/evm/151/erc20/0x6ed1f491e2d31536d6561f6bdb2adc8f092a6076/holders?limit=100" wrbnt_holders_now.json` | WRBNT holder list | Routescan API |
| 5 | `python3 ../scripts/build_universe.py` | `universe.json`, `q3_txs.json` | The address list, plus the quarter's transactions |
| 6 | `python3 ../scripts/snapshot.py universe.json snapshots.json` | `snapshots.json` | RBNT, WRBNT and stakes at both blocks. For a very large list, run it on addresses seen since the first pool launched, then `snapshot_native.py` for the rest |
| 7 | `python3 ../scripts/codes_pools.py` | `codes.json`, `pools.json` | Contract code hashes; pool and WRBNT totals |
| 8 | `python3 ../scripts/changepoints.py '<reserved multisig addresses as JSON>' changes_locked.json` | `changes_locked.json` | Blocks where each reserved multisig changed balance |
| 9 | `python3 ../scripts/eco_receipts.py` | `receipts_eco_unlocked.json` | Receipts of every transaction Ecosystem (Unlocked) sent |
| 10 | `python3 ../scripts/pool_flows.py` | `pool_flows.json` | Gross staking flows from every transaction to the pools |
| 11 | `python3 ../scripts/fees.py 3025810 3209414 > fees_q3.json` | `fees_q3.json` | Transaction fees paid in the quarter |
| 12 | `python3 ../scripts/genesis_check.py` | `genesis_found.json` | Balances at block 0 (all RBNT at genesis must be in the list) |
| 13 | `python3 ../scripts/daily.py` | `daily.json` | Daily series: pool stakes, WRBNT supply, bridge, vesting, reserved |
| 14 | `python3 ../scripts/analyze.py` | `out/*.csv`, `out/figures.json`, `out/checks.csv` | All tables and checks. Every PASS row must pass |
| 15 | `python3 ../scripts/text.py` | text in `out/figures.json`, `out/community_summary.md` | Plain-language text and the X thread |
| 16 | `python3 ../scripts/build_report.py && node ../scripts/render.js $PWD/report/report.html $PWD/report/report.pdf` | the PDF | Print report |
| 17 | `python3 ../scripts/build_site.py <repo>` | `index.html`, `method.html`, `assets/`, `data/daily_series.csv`, `vercel.json` | The website |
| 18 | `python3 ../scripts/build_method.py <repo> && python3 ../scripts/build_readme.py <repo>` | `METHOD.md`, `README.md` | Method note and repository README |
| 19 | `node ../scripts/render_shots.js <repo> http://localhost:8765/` (with the repo served on port 8765) | `assets/img/og.png`, `docs/*.png` | Social image and README screenshots |

## Helpers

* `rpc.py`: batched JSON-RPC with retries. It raises `TooLarge` so callers can split a request.
* `charts.py`: static SVG charts for the PDF. The site's interactive charts live in `site_src/site.js` (copied to `assets/js/site.js`).
* `block_delta.py`: reads every known address at one block and the block before it. It was used to see where a block's fee goes.
* `calldata_addrs.py`: pulls addresses out of the data of chosen transactions.

## Limits met while producing this edition

* The RPC caps `eth_getLogs` at 100 blocks per call and rate-limits it, so the pipeline reads blocks and contract state instead of event logs.
* The RPC refuses batches of more than about 100 calls and responses that are too large. `scan_chunks.py` and `scan_addrs.py` split a request when that happens.
* Without a key, the Routescan API returns HTTP 429 after heavy use. A free key (https://rscan.link/api) avoids that.
* Routescan's sorted address list carries stale balances for some addresses, so it is not used as a holder count. Balances always come from the chain.
