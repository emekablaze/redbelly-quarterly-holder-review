# Scripts: run order

Everything runs with Python 3.10+ and the standard library. Two extras are needed: `pycryptodome` (Keccak hashes, for `codes_pools.py`) and, to make the PDF, Node with `playwright` and Chromium (`render.js`). Run all scripts from one working folder, for example:

```bash
pip install pycryptodome
mkdir work && cd work
```

Each step reads the files written by the steps before it. The snapshot blocks are set at the top of each script (`S = 3025809`, `E = 3209414`). For a new quarter, change them everywhere (`grep -rn 3025809 ../scripts`).

| # | Command | Writes | Notes |
|---|---|---|---|
| 1 | `python3 ../scripts/get_treasury.py` | `treasury_table.json` | Reserved wallets from the DAO treasury page |
| 2 | `python3 ../scripts/scan_chunks.py 0 3238634 chunks` | `chunks/*.json` | Every transaction from genesis to the collection date. Resumable, and several copies can run on different ranges at once. Took about 2 hours here |
| 3 | `python3 ../scripts/paginate2.py "/v2/network/mainnet/evm/151/erc20/0x6ed1f491e2d31536d6561f6bdb2adc8f092a6076/holders?limit=100" wrbnt_holders_now.json` | WRBNT holder list | Routescan API. Optionally also run the native list (`/addresses?limit=100&sort=balance,desc` → `native_list.json`) |
| 4 | `python3 ../scripts/build_universe.py` | `universe.json`, `q3_txs.json` | Address list + the quarter's transactions |
| 5 | `python3 ../scripts/snapshot.py universe.json snapshots.json` | `snapshots.json` | RBNT, WRBNT and staked amounts at both blocks. For a very large list, run it on addresses seen since the first pool launched, then `snapshot_native.py` for the rest |
| 6 | `python3 ../scripts/codes_pools.py` | `codes.json`, `pools.json` | Contract code hashes; pool and WRBNT totals |
| 7 | `python3 ../scripts/changepoints.py '[reserved multisig addresses]' changes_locked.json` | `changes_locked.json` | Blocks where each reserved multisig changed balance |
| 8 | `python3 ../scripts/eco_receipts.py` | `receipts_eco_unlocked.json` | Receipts of every transaction Ecosystem (Unlocked) sent |
| 9 | `python3 ../scripts/pool_flows.py` | `pool_flows.json` | Gross staking flows from every transaction to the pools |
| 10 | `python3 ../scripts/fees.py 3025810 3209414 > fees_q3.json` and `python3 ../scripts/fees.py 1 3025809 > fees_to_start.json` | fee totals | Base fees burned (for the reconciliation checks) |
| 11 | `python3 ../scripts/analyze.py` | `out/*.csv`, `out/figures.json`, `out/checks.csv` | All tables and checks. Every `checks.csv` row must say PASS |
| 12 | `python3 ../scripts/text.py` | text in `out/figures.json`, `out/community_summary.md` | Plain-language text and the community summary, generated from the figures |
| 13 | `python3 ../scripts/build_report.py && node ../scripts/render.js $PWD/report/report.html $PWD/report/report.pdf` | `report/report.html`, `report/report.pdf` | The report |

Helper modules: `rpc.py` (batched JSON-RPC with retries), `charts.py` (brand SVG charts). `block_delta.py` reads every known address at one block and the block before it. It was used to confirm that transaction fees are burned.

**Rate limits met while producing this edition.** The RPC caps `eth_getLogs` at 100 blocks per call and rate-limits it, which is why the scripts scan blocks and read contract state instead of using event logs. It also refuses batches above about 100 calls, or responses that are too large; `scan_chunks.py` splits the request when that happens. The Routescan API without a key returns HTTP 429 after heavy use. A free key (https://rscan.link/api) avoids this.
