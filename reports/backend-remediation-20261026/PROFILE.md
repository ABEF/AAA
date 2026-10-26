# Current-profile fee-read integrity

The accounting-3 NFT read boundary accepted two combinations that the pinned
contracts cannot legitimately produce. These are response-integrity defects:
they could misstate fees or conceal an omitted native ledger. They do not
demonstrate an on-chain entitlement, custody or signing vulnerability.

## Changes

| Boundary | Reproduced response | Correction |
| --- | --- | --- |
| Current native LP inventory | Accounting 3 with `Rewards.assets` omitting ETH was accepted if the union of LP/royalty currencies still matched the reviewed descriptors. | Require ETH as the first LP ledger currency for accounting 3. The actual `ZZZRewards` constructor always inserts `address(0)` first. Empty and misordered inventories are also rejected. |
| Inactive NFT claimable balances | A validated dormant NFT with zero shares, bucket and royalty weight could return positive LP or royalty claims. Optional royalty reporting caught some royalty contradictions but did not protect LP claims. | After validating activation identity, reject any available nonzero amount in either ledger for a never-activated NFT. This check applies with and without optional reporting. |

The inactive test uses the already validated activation state, not current LP
value. Active NFTs with parked or outbound principal retain their owed rewards.
A failed currency read under optional reporting remains `available: false`,
`raw: null`; it is neither invented as zero nor treated as a contradictory
positive balance. Historical profiles 1 and 2 retain their explicit source-only
LP inventory compatibility. Current-profile requirements are not retroactively
applied to old deployments.

There is no response-schema, Solidity, ABI, storage, economic-rights, allocation,
authority, public-signing or deployment change. No ETH row is synthesized.

## Verification

[The test module](../../tests_python/test_current_fee_integrity.py) instantiates
the real `Projection`, configuration validation, lifecycle/identity checks and
raw ABI-encoded RPC fixture responses. It does not replace the projection with a
hand-written stub and does not use live RPC, keys or the existing test chain.

- [Before](fee-integrity-before.json): seven methods, zero test errors, expected
  failures in four negative methods. A missing-native inventory and each
  dormant nonzero-claim case were accepted. Empty/misordered inventory cases
  already failed under less specific guards; those are retained controls rather
  than new acceptance bugs.
- [After](fee-integrity-after.json): the same seven methods and unchanged test
  fixture file pass against the corrected `service.py`.
- [Historical extension](fee-integrity-legacy-after.json): one subsequently
  added method passes, proving both verified dormant zero balances and rejection
  of nonzero source-token LP/native-or-token royalties under profiles 1 and 2.
  The first seven methods were not rerun for this test-only addition.

Eight distinct methods passed across these two explicit final-service scopes.
Source SHA-256 values and observation times are recorded in each result. These
are focused Python composition checks, not a full backend regression, an EVM
run or actual-provider qualification. The parent task owns the affected shared
suite and consolidated verification record.

## Fee presentation findings

The reviewed read contracts distinguish these values and must keep doing so:

- **Claimable now:** exact funded per-NFT LP total (individual plus collective)
  and its separate royalty claimable amounts. Optional reporting can expose
  unavailable currencies. Never sum a partial native leg as a complete total.
- **Earned over time:** processed individual LP plus equal collective rewards
  plus royalties attributed to the NFT. Compounding, buyback and collection
  gross intake are not the NFT's reward. Claims, conversions and custody
  returns are not new income. Pending unsynchronized royalties can be included
  in current contract claimable before they enter processed earnings history.
- **Previously claimed:** complete verified lifetime claims, including previous
  owners and reviewed predecessor lineage; not the last claim and not earned
  revenue again.

Collection allocation accumulators can retain rounding/fractional amounts and
are not an exact sum of all NFT claimable balances. A portfolio aggregate must
apply its own lightweight inactive-credit check because it does not call the
heavy full NFT projection; that correction is owned by the portfolio subtask.

The existing website native response validator already requires a native row
in **each** LP and royalty list before the view helper sums them. No additional
website edit was justified by this missing-leg reproduction. Its separate
native-2/current-3 integration gap remains open. The test suite does not qualify
that frontend profile, providers, feeds, routes or production operation.
