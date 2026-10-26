# Data dictionary: Q3 2026 edition

Snapshot blocks: start `3025809` (30 Jun 2026 23:57:19 UTC), end `3209414` (30 Sep 2026 23:57:35 UTC). All amounts are in RBNT (WRBNT counted 1:1, 18 decimals already applied) unless a column says wei. "Holdings" = plain RBNT + WRBNT + RBNT staked in a Reddex pool. See [`../METHOD.md`](../METHOD.md) for the full method.

**No file contains the address of an unnamed wallet.** The only addresses are those already public: the reserved wallets, the WRBNT contract, the two Reddex pools and the bridge adapter.

| File | Used in | Contents |
|---|---|---|
| `supply_by_category.csv` | Section 01 | Holdings by group at both blocks, the change, and the number of addresses with a balance |
| `concentration.csv` | Section 02 | Holders above 10 RBNT, top 10/50/100/500 shares, Gini coefficient and median, at both blocks |
| `holder_size_bands.csv` | Section 02 | Unnamed wallets above 10 RBNT by holding size: how many, and how much RBNT |
| `largest_holder_tiers.csv` | Section 03 | Unnamed wallets ranked on 1 Jul: totals at both blocks, change, and counts that grew / stayed the same / shrank / emptied, plus staked amounts |
| `holders_ranked_anonymous.csv` | Section 03 | The 1,000 largest unnamed wallets on 1 Jul **by rank only** (no addresses): holdings and stakes at both blocks |
| `staking_pools.csv` | Section 04 | Each pool's RBNT balance, `totalStake()`, reward funds, stakers, gross staked and withdrawn, transactions, reward funds added and rewards paid |
| `daily_series.csv` | Sections 04–05 | End-of-day values for every day of the quarter: stakes and balances of both pools, WRBNT supply, bridge adapter, vesting contracts, reserved wallets |
| `reserved_wallets.csv` | Section 05 | Each reserved wallet at both blocks (RBNT + WRBNT), and every block where it changed |
| `eco_unlocked_flows.csv` | Section 05 | Ecosystem (Unlocked)'s outflows and inflows in the quarter, by destination group |
| `named_balances.json` | Verify buttons | Exact wei balances of the named addresses at both blocks, plus pool and WRBNT totals |
| `checks.csv` | Section 06 | Reconciliation checks (PASS / INFO) |
| `figures.json` | Whole report | Every figure the report quotes, and the generated text |
| `treasury_table.json` | Section 05 | Reserved wallets as embedded in the DAO treasury page (original allocations, not balances) |
| `pools.json` | Section 04 | Raw pool balances, `totalStake()`, WRBNT `totalSupply()` and backing, in wei |
| `pool_flows.json` | Section 04 | Raw gross staking flows |
| `changes_locked.json` | Section 05 | Blocks where each reserved multisig changed balance, with the change in wei |
| `fees_q3.json` | Section 06 | Transaction fees paid in the quarter (gas used × base fee, summed over every block) |
