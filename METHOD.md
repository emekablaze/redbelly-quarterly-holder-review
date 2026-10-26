# Method and sources: RBNT Holder Report

This note explains how the Q3 2026 edition was produced, so that anyone can check a figure and the next edition can be produced the same way. Everything here runs from the scripts in [`scripts/`](scripts/). Their outputs are in [`data/`](data/).

## 1. Period and snapshot blocks

| | Value |
|---|---|
| Quarter | 1 July 2026 00:00 UTC to 30 September 2026 23:59:59 UTC |
| Start snapshot | Block **3,025,809** (timestamp 1782863839, 30 Jun 2026 23:57:19 UTC), the last block before the quarter |
| End snapshot | Block **3,209,414** (timestamp 1790812655, 30 Sep 2026 23:57:35 UTC), the last block of the quarter |
| Transactions in the quarter | Blocks 3,025,810 to 3,209,414 inclusive |
| Daily series | The last block before each midnight UTC, 1 Jul to 1 Oct 2026 (93 points) |

The snapshot blocks come from the explorer API (`module=block&action=getblocknobytime&closest=before`) for 1782864000 (1 Jul 2026 00:00 UTC) and 1790812800 (1 Oct 2026 00:00 UTC), and were checked against block timestamps on the RPC. Redbelly only makes a block when there is a transaction, so a snapshot can fall a few minutes before midnight.

## 2. Sources

| Source | Used for |
|---|---|
| Redbelly mainnet RPC `https://governors.mainnet.redbelly.network` (chain ID 151) | Every balance at the snapshot blocks (`eth_getBalance`, `eth_call`), every block and transaction (`eth_getBlockByNumber`), receipts, contract code |
| Routescan API `https://api.routescan.io/v2/network/mainnet/evm/151/...` | WRBNT holder list, verified contract names and source code, snapshot block numbers, and a cross-check of the address list (section 4) |
| DAO treasury page `https://redbellydao.network/treasury/` | Names and addresses of the nine reserved wallets, read from the table embedded in the page's JavaScript bundle |
| Verified source code on Routescan | How the Reddex pools work (`ReddexRBNTLockStaker`), plus the WRBNT, bridge and vesting contracts |

The treasury page shows **original allocations**. Every reserved-wallet figure in the report is a balance read from the chain at a snapshot block.

## 3. Which addresses were read

No RPC call returns "every holder at block N", so the address list was built from the chain itself:

1. **Every block from the first to block 3,238,634** (26 Oct 2026) was read. For each transaction, the scan collected the sender, the recipient, and every address named in the transaction data: ABI-encoded address arguments, addresses passed as `bytes` or as text (as bridges do), and recipients inside multisig batch payouts (`scripts/scan_addrs.py`). This catches accounts that receive RBNT without ever sending a transaction. One example is the small RBNT credit that Redbelly's account-permission registry gives most newly permissioned accounts (in a random sample of 40 registrations: 10 RBNT for 19, 5 RBNT for 16, 125 RBNT for 2 and nothing for 3). The account is named in the registry call.
2. **Routescan's WRBNT holder list.**
3. **The named addresses**: the nine reserved wallets, the two staking pools, the WRBNT contract and the bridge adapter.

That gives **810,661 addresses**. **165,294** of them held RBNT, WRBNT or a stake at one of the two snapshot blocks.

## 4. How complete the list is

| Check | Result |
|---|---|
| All RBNT at genesis | All 10,000,000,000 RBNT sat in a single address at block 0, and that address is in the list |
| WRBNT | The WRBNT balances read add up exactly to WRBNT `totalSupply()` at both blocks, so every WRBNT holder is included |
| Staking | Stakers' `userInfo` amounts add up exactly to each pool's `totalStake()` at both blocks, so every staker is included |
| Cross-check with Routescan's sorted address list | 300 addresses sampled from it (ranks 1–200 and 501–600): 298 are in the list. The other 2 held **0 RBNT at the end block**: one was first funded in October, and the other is listed by Routescan with a balance of about 175,000 RBNT while both the chain and Routescan's own address page show 0 |

The last check matters for anyone repeating this work. **Routescan's sorted address list carries stale balances for some addresses**, so the number of addresses it lists above a threshold is not a reliable holder count. Read balances from the chain instead.

## 5. Counting each token once

| Where the RBNT sits | How it is counted |
|---|---|
| In a wallet as plain RBNT | For that wallet |
| Wrapped as WRBNT | For the wallet holding the WRBNT. The RBNT inside the WRBNT contract is **not counted again**. Check: the contract's RBNT equals WRBNT `totalSupply()` to the wei |
| Staked in a Reddex pool | For the staker (`userInfo(address).amount`). Whatever a pool holds beyond `totalStake()` is shown as that pool's **reward funds** |

"Holdings" = plain RBNT + WRBNT + RBNT staked in either pool.

**Pool balances include reward funds as well as stakes.** Rewards are paid in RBNT from each pool's own balance, so a pool's RBNT balance is user stakes plus RBNT added to pay rewards. The report shows the pool balance, the `totalStake()` figure and the gap between them.

## 6. Groups

| Group | Rule |
|---|---|
| Redbelly reserved wallets | The nine addresses on the DAO treasury page |
| Reddex pools: reward funds | The two pools named in the brief. Only their reward funds sit here, because stakes are counted with the stakers |
| Bridge to other chains | The verified `RBNTNativeOFTAdapter`. RBNT locked here backs RBNT bridged to other chains |
| Token vesting contracts | Contracts whose code is byte-identical to the verified `TokenVestingManager` (same code hash) |
| Other smart contracts | Any other address with code, such as exchange pools and routers. Reported only as a group |
| Labelled exchange wallets | Addresses that Routescan publicly names as an exchange. **None were labelled when the data was collected**, so this group is empty in this edition |
| Unnamed wallets | Every other address: ordinary wallets and unnamed multisig wallets. Reported **only in groups**, and never listed by address in any file |

## 7. Measures

* **Holder**: an unnamed wallet holding more than 10 RBNT. Wallets with 10 RBNT or less (mostly leftovers after fees) are left out of holder counts and concentration figures, but included in every supply total.
* **Top 10 / 50 / 100 / 500 share**: the share of unnamed-holder RBNT held by the largest 10, 50, 100 or 500 of them.
* **Gini coefficient**: from 0 (all hold the same) to 1 (one wallet holds everything).
* **Largest-holder groups**: unnamed wallets ranked by holdings at the **start**. The groups stay fixed, so the end figures show what the same wallets did. Grew = more than +1%, shrank = more than −1%, otherwise about the same. Emptied = below 1 RBNT at the end.
* **Staking flows**: staked in = the value of every successful `stake()` transaction to a pool (489 in the quarter). Withdrawn = staked in minus the change in `totalStake()`. Reward funds added = plain RBNT transfers to a pool. Rewards paid = reward funds added minus the change in reward funds.
* **Reserved-wallet movements**: eight of the nine reserved wallets are multisig contracts, so their transfers show up as balance changes, not as transactions they send. Every block where one of them changed balance was found by binary search on its balance (`scripts/changepoints.py`).

## 8. Checks

All results are in [`data/checks.csv`](data/checks.csv). PASS rows match to the wei. INFO rows are reconciliation notes.

| Check | Result |
|---|---|
| WRBNT contract RBNT = WRBNT `totalSupply()`, both blocks | PASS |
| Sum of WRBNT balances read = WRBNT `totalSupply()`, both blocks | PASS |
| Sum of stakers' `userInfo` = each pool's `totalStake()`, both blocks, both pools | PASS |
| Sum of holdings = sum of plain RBNT balances read (nothing counted twice), both blocks | PASS |
| Ecosystem (Unlocked): start − sent − fees + received = end | PASS, with fees from transaction receipts |
| All RBNT at genesis is held by an address in the list | PASS |
| Fees vs change in total | INFO: transaction fees paid in the quarter were 2.00M RBNT, and the total RBNT read fell by 1.20M. The 0.80M difference was paid back out to addresses as credits that are not transactions. For example, a group of 32 addresses received daily credits of 50 to 120 RBNT each, which track network activity |

## 9. Producing the next edition

1. Set the new snapshot blocks (`S`, `E`) in the scripts with `getblocknobytime` (`closest=before`) for the first second of the quarter and of the next quarter.
2. Re-read the treasury page for new or changed reserved wallets (`scripts/get_treasury.py`).
3. Extend the block scans to the new end block. The scans are resumable, so earlier chunks are reused (`scripts/scan_chunks.py`, `scripts/scan_addrs.py`).
4. Check Routescan for newly labelled exchange wallets.
5. Run the scripts in the order in [`scripts/README.md`](scripts/README.md), then confirm every PASS row in `checks.csv` before publishing.

The RPC limits `eth_getLogs` to 100 blocks per call and rate-limits it, so the method reads blocks and contract state instead of event logs. Without a key, the Routescan API rate-limits heavy use; a free key (https://rscan.link/api) avoids that.

## 10. Limits

* Wallets are not people: one person can hold many wallets, and an exchange wallet holds tokens for many people.
* RBNT on other chains is out of scope. Only the RBNT locked in the bridge adapter on Redbelly is shown.
* RBNT inside exchange pools, routers and other unnamed contracts is reported as one group and not looked through.
* The day-by-day series are read at the end of each UTC day. Movements inside a day net out.
