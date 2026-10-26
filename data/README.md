# Data: Q3 2026 edition

Snapshot blocks: start `3025809` (30 Jun 2026 23:57:19 UTC), end `3209414` (30 Sep 2026 23:57:35 UTC). All amounts are in RBNT (WRBNT counted 1:1). "Holdings" = plain RBNT + WRBNT + RBNT staked in a Reddex pool. See `../METHOD.md` for the full method.

| File | Chart / table in the report | Contents |
|---|---|---|
| `supply_by_category.csv` | Chart 1, Section 1 table | Holdings by group at both blocks, with address counts |
| `concentration.csv` | Chart 2, Section 2 table | Holder count, top 10/50/100/500 shares, Gini, median (unnamed wallets above 10 RBNT) |
| `holder_size_bands.csv` | Chart 3 | Unnamed wallets and their RBNT by holding size band |
| `largest_holder_tiers.csv` | Charts 4 and 5, Section 3 table | Unnamed wallets ranked on 1 Jul: totals, grew / same / shrank / emptied, staked amounts |
| `holders_ranked_anonymous.csv` | Section 3 | The 1,000 largest unnamed wallets on 1 Jul by rank only (no addresses): holdings and stakes at both blocks |
| `staking_pools.csv` | Chart 6, Section 4 table | Pool balance, `totalStake()`, reward funds, stakers, gross flows |
| `reserved_wallets.csv` | Chart 7, Section 5 table | Each reserved wallet at both blocks, and the blocks where it changed |
| `eco_unlocked_flows.csv` | Section 5 | Ecosystem (Unlocked) outflows and inflows by destination group |
| `checks.csv` | Appendix | Reconciliation checks (PASS / INFO) |
| `figures.json` | Whole report | Every figure the report quotes, and the generated text |
| `treasury_table.json` | Section 5 | Reserved wallets as embedded in the DAO treasury page (original allocations) |
| `pools.json` | Section 4 | Raw pool and WRBNT balances, `totalStake()` and `totalSupply()` in wei |
| `pool_flows.json` | Section 4 | Raw gross staking flows |
| `changes_locked.json` | Section 5 | Blocks where each reserved wallet's balance changed, with the amount in wei |
| `fees_q3.json`, `fees_to_start.json` | Appendix | Base fees burned in the quarter and from launch to the start block |

Unnamed wallets are never listed by address in any file.
