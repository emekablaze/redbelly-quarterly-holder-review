# Method and sources: RBNT Holder Report

This note explains how the Q3 2026 edition was produced, so the next edition can be produced the same way and anyone can check any figure. The scripts named here are in `scripts/`, and their outputs are in `data/`.

## 1. Period and snapshot blocks

| | Value |
|---|---|
| Quarter | 1 July 2026 00:00 UTC to 30 September 2026 23:59:59 UTC |
| Start snapshot | Block **3025809**, timestamp 1782863839 (30 Jun 2026 23:57:19 UTC), the last block before the quarter began |
| End snapshot | Block **3209414**, timestamp 1790812655 (30 Sep 2026 23:57:35 UTC), the last block of the quarter |
| Transactions inside the quarter | Blocks 3025810 to 3209414 inclusive |

Both blocks come from the explorer API (`module=block&action=getblocknobytime&closest=before`) for the timestamps 1782864000 (1 Jul 2026 00:00 UTC) and 1790812800 (1 Oct 2026 00:00 UTC). They were then checked against the block timestamps on the RPC. Redbelly only makes a block when there are transactions, so a snapshot block can sit a few minutes before midnight.

## 2. Data sources

| Source | Used for |
|---|---|
| Redbelly mainnet RPC `https://governors.mainnet.redbelly.network` (chain ID 151) | All balances at the two snapshot blocks (`eth_getBalance`, `eth_call`), every block and transaction (`eth_getBlockByNumber`), receipts (`eth_getTransactionReceipt`) and contract code (`eth_getCode`) |
| Routescan API `https://api.routescan.io/v2/network/mainnet/evm/151/...` | The WRBNT holder list, verified contract names and source code, and the snapshot block numbers |
| DAO treasury page `https://redbellydao.network/treasury/` | The names and addresses of the nine reserved wallets, taken from the table embedded in the page's own JavaScript bundle |
| Verified source code on Routescan | How the Reddex staking pools work (`ReddexRBNTLockStaker`), and the WRBNT, bridge and vesting contract names |

The treasury page table shows the **original allocations**. Every reserved-wallet figure in the report is a balance read from the chain at a snapshot block, not a figure from that table.

## 3. Which addresses were read

There is no single call that returns "every RBNT holder at block N", so the address list was built from three sources and then each address's balance was read at both snapshot blocks:

1. **Every sender and recipient of every transaction from the first block to block 3238634** (26 Oct 2026, the day the data was collected): 738,504 addresses from 7,124,044 transactions, found by reading every block (`scripts/scan_chunks.py`). This catches anyone whose balance changed in or after the quarter, and anyone who has ever staked, because staking needs a transaction to the pool.
2. **Routescan's WRBNT holder list** (`/v2/network/mainnet/evm/151/erc20/0x6ed1…6076/holders`), 2,139 holders.
3. **The named addresses**: the nine reserved wallets, the two staking pools, the WRBNT contract and the bridge adapter.

Of these, 160,262 held RBNT, WRBNT or a stake at one of the two snapshot blocks.

**How complete is the list?** Three independent checks (section 7):

* The WRBNT balances read add up exactly to WRBNT's total supply at both blocks, so every WRBNT holder is included.
* The stakes read add up exactly to each pool's `totalStake()` at both blocks, so every staker is included.
* Plain RBNT: the balances read at the start block come to 99.63% of the RBNT that should exist (10,000,000,000 allocated at launch, minus 30.06M RBNT burned as transaction fees since launch). The remainder sits in addresses that have only ever received RBNT through a contract and never appeared in a transaction, so a transaction scan cannot see them.

A planned fourth source, Routescan's native-balance list (`/addresses?sort=balance,desc`), was rate-limited (HTTP 429) for the whole collection window. The next edition should add it with a free API key, which closes the remaining gap.

## 4. Counting each token once

RBNT can sit in three places that point at the same tokens. The report credits each token to the wallet that controls it:

| Where the RBNT sits | How it is counted |
|---|---|
| In a wallet as plain RBNT | Counted for that wallet |
| Wrapped as WRBNT | WRBNT is backed one to one by RBNT held in the WRBNT contract. The WRBNT is counted for the wallet that holds it, and the RBNT inside the WRBNT contract is **not counted again**. Check: the WRBNT contract's RBNT balance equals WRBNT `totalSupply()` exactly at both blocks |
| Staked in a Reddex pool | The pool contract keeps each staker's amount (`userInfo(address).amount`). That amount is counted for the staker. Whatever is left in the pool beyond `totalStake()` is shown as the pool's **reward funds** |

So "holdings" in the report means plain RBNT + WRBNT + RBNT staked in either Reddex pool.

**Staking pools may hold reward funds as well as stakes.** Rewards are paid in RBNT from the pool's own balance. A pool's RBNT balance is therefore user stakes plus RBNT added to pay rewards. The report shows both the pool balance and the `totalStake()` figure, and the gap between them is the reward funds.

## 5. Groups

Each address is put into exactly one group:

| Group | Rule |
|---|---|
| Redbelly reserved wallets | The nine addresses on the DAO treasury page |
| Reddex staking pools | The two pools in the brief. Only their reward funds sit here, because stakes are credited to stakers |
| Bridge (RBNT Native OFT Adapter) | Verified contract `RBNTNativeOFTAdapter`. RBNT locked here backs RBNT that has been bridged to other chains |
| Token vesting contracts | Contracts whose code is byte-identical to the verified `TokenVestingManager` contract (same code hash) |
| Other smart contracts | Any other address with contract code, such as exchange pools and routers. Shown only as a group |
| Labelled exchange wallets | Addresses that Routescan publicly names as an exchange. **None were labelled on Routescan when the data was collected**, so this group is empty in this edition |
| Unnamed wallets | Every other address: ordinary wallets and unnamed multisig wallets. Shown **only as groups**, never one by one |

## 6. Measures

* **Holder**: an unnamed wallet holding more than 10 RBNT. About 145,600 addresses hold some RBNT but no more than 10 (about 199,000 RBNT between them, 0.002% of supply). Most are dust left after transaction fees. They are left out of holder counts and concentration figures so that dust does not drown out real holders, but they are included in every supply total.
* **Top 10 / 50 / 100 share**: the share of all RBNT held by unnamed holders that sits in the 10, 50 or 100 largest of them.
* **Gini coefficient**: one number for inequality, from 0 (everyone holds the same) to 1 (one wallet holds everything).
* **Largest-holder tiers**: unnamed wallets ranked by holdings at the **start** of the quarter. The groups stay fixed, so the end figures show what the same wallets did. A wallet "grew" if its holdings rose by more than 1%, "shrank" if they fell by more than 1%, and otherwise "stayed about the same".
* **Staking flows**: gross RBNT staked = the value of every successful `stake()` transaction to the pool. Gross unstaked = staked minus the change in `totalStake()`. Reward funding = plain RBNT transfers to the pool. Rewards paid = reward funding minus the change in reward funds.
* **Reserved-wallet movements**: the reserved wallets (apart from Ecosystem (Unlocked)) are multisig contracts, so their transfers appear as balance changes, not as transactions they send. Every block where one of them changed balance was found by binary search on its balance between the snapshot blocks (`scripts/changepoints.py`).

## 7. Checks that were run

All results are in `data/checks.csv`.

| Check | Result |
|---|---|
| WRBNT contract RBNT balance = WRBNT `totalSupply()` (both blocks) | PASS, equal to the wei |
| Sum of WRBNT balances read = WRBNT `totalSupply()` (both blocks) | PASS, equal to the wei |
| Sum of stakers' `userInfo` amounts = each pool's `totalStake()` (both blocks, both pools) | PASS, equal to the wei |
| Sum of holdings (RBNT + WRBNT + stakes + pool reward funds, WRBNT contract excluded) = sum of plain RBNT balances read | PASS, equal to the wei, so nothing is counted twice |
| Ecosystem (Unlocked): start − sent − fees + received = end | PASS, equal to the wei, using fees from transaction receipts |
| Where fees go | Every block names the zero address as fee recipient, and the zero address's balance does not change. In a test block (3100000), the RBNT read fell by exactly that block's base fee: fees are burned |
| Fall in RBNT read over the quarter vs fees burned | INFO: fall 1.45M, fees burned 2.00M. The 0.55M difference moved in from addresses outside the list (see section 3) |
| RBNT read vs RBNT that should exist | INFO: 99.63% at the start block |

## 8. Producing the next edition

1. Set the new quarter's snapshot blocks in the scripts (`S`, `E`) using `getblocknobytime` for the first second of the quarter and of the following quarter, with `closest=before`.
2. Re-read the DAO treasury page for any new or changed reserved wallets (`scripts/get_treasury.py`).
3. Run the scripts in the order listed in `scripts/README.md`. The block scan is resumable, and earlier chunks can be reused.
4. Check Routescan for any newly labelled exchange wallets, and add them to the labels file.
5. Run `analyze.py`, then `build_report.py`, and confirm every row in `checks.csv` passes before publishing.

The Routescan API is rate limited without a key. A free key (https://rscan.link/api) makes the list downloads much faster. The RPC limits `eth_getLogs` to 100 blocks per call and rate-limits it, which is why this method scans blocks and reads contract state instead of relying on event logs.

## 9. Limits

* Anyone can hold many wallets, and one wallet can belong to many people, as with exchanges and contracts. Wallet counts are not people counts.
* Holdings on other chains (bridged RBNT) are not covered. The report shows only the RBNT locked in the bridge adapter on Redbelly.
* RBNT sitting in exchange-pool contracts, routers or other unnamed contracts is grouped under "Other smart contracts". This report does not look through those contracts.
