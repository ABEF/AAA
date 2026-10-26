# Keeper and shared-LP management audit - 2026-10-26

Initial main9fe9997. The user requested robust, safe, secure, consistent and
efficient keeper/LP management, without assuming dependencies or tests were sound.
This is an internal source-scoped audit and remediation, not a guarantee of no
vulnerabilities or independent production approval.

## Scope and method

Read the actual controller/custody, Vault/Strategy/Liquidity/Oracle/Budget,
contribution/share and fee/conversion flows, installed Uniswap/OZ execution,
keeper submission/recovery/configuration/health and shared RPC/state/fee helpers.
Trace authorization, callback order, exact balances/approvals, LP ownership/key/
ticks/liquidity, conservative prices, loss floors, allocations/fractions and
failure rollback. Preserve current economic rights and accepted governance trust.
Actual service choices cannot be qualified by assuming mocks represent them.

Verify a suspected defect before fixing it. Retain failed controls, disproved
hypotheses and initial aggregate failures. Use affected tests, actual compiled
fixture calls and exact source pins; do not repeat an unchanged whole release,
static analyzer or full Solidity suite merely to increase counts.

## Findings and implemented changes

| ID | Finding and consequence | Correction |
| --- | --- | --- |
| K-01 / P2 | Health artifacts identified chain/signer but could pass for a different Vault/profile/provider/budget configuration. | Hash the exact loaded configuration in the writer; checker requires equality. Missing/stale/malformed identity yields configuration_mismatch. Hash only, no config secrets exported. [Operations review](operations/OPERATIONS.md). |
| K-02 / P2 | Noncanonical converter/route Boolean values2 or uintmax appeared legitimately disabled and healthy. | Accept only ABI0/1; malformed control produces deferred/degraded telemetry rather than a false healthy off switch. Valid0off,1on and unrelated upkeep remain. [Reward review](rewards/REVIEW.md). |
| V-01 / P3 | Range regression cast removed enum values5/6 and panicked before completing the intended assertions. | Iterate through actual PositionStatus.Parked; retain every supported inactive state. Original panic0x21 and final9-method execution are recorded. [Core review](core/REVIEW.md). |
| V-02 / P3 | Process rehearsal/new staging initializer silently used old accounting1/fee0 and a fifteen-word ERC20 fixture. It could not verify current3/native reader behavior. | Fresh test fixture now uses explicit accounting3/fee1,8words/native-zero and no creator job. New-only initializer matches it; source hashes include fee/range/Position dependencies. Existing installed services/configs remain unchanged. |
| V-03 / verification | Initial broader run exposed a mutable-after-construction fixture, unsupported Unix assertions, unread POST resets and a lazy-import hash-inventory false positive. | Finalize fixture config before constructing Keeper; retain Unix permission/locking assertions as explicit Unix tests; drain/witness actual redirect requests without relaxing client rejection; pin lazy dependencies before running. Frozen first attempt is retained. |

These changes do not fix or imply an identified on-chain theft exploit. No
production Solidity, economic rule, custody/claim authority, loss cap or ABI is
changed. The new observation checks improve safety of operator decisions and
visibility of faults; they do not authenticate an otherwise dishonest provider.

## Controls traced and retained

- Many NFTs share one LP; maintenance discovers bounded shared buckets, not a
  1,000-NFT rebalance loop. Width selection is reviewed/default-disabled and
  ordinary guarded rebalance is a separate operation.
- Entry/compound/rebalance settle prior fee entitlements before share/LP changes.
  Actual physical LP and marginal contribution guards exclude old principal,
  reserves and donations; two-pass placement stays bounded.
- Core callbacks, owner/key/range/liquidity checks and exact native/ERC20 deltas,
  approval reset, captured prices and final loss/idle checks remain. Removing
  them merely to save gas was not justified. Actual market cost remains unqualified.
- Fees remain80/10/5/5, royalties separate, collective equal per activated NFT;
  fractions and unclaimed rights follow NFT. Conversion debits only earned source
  balances and credits the same NFTs. Reserves/principal are not conversion input.
- Keeper simulates before signing, persists original intent/fee review first,
  reconciles exact hashes/nonce/cost/canonical receipt before new work and stops
  ambiguous broadcasts. Atomic private state and single-host process locking
  remain; there is no blind resend, reset, budget migration or second-host fencing.
- Governance alone approves pool moves/parking/custody exits. Snapshot, recipient,
  raw/normal minima and actually funded return/completion were inspected. Normal
  exit uses fixedZZZ; raw exit is explicitly authorized and never automatic.
  User loss limits do not haircut funded rewards; shared LP shares remain intact.
- External custody is trusted, not a forced-return guarantee. Same-chain NFT/
  ledger handoff is separate. Integrated bridging, arbitrary token replacement,
  external creator intake and remote-value proofs are not reintroduced.

Detailed boundaries and actual source/dependency pins are in the core,
operations and rewards reviews. A bounded deep-JSON RPC hypothesis already passed
on unchanged RPC source; it did not justify a production edit or a fix claim.

## Verification summary

Final affected Python run:359selected/executed methods, **354pass/5explicit Unix
skips**, no failures/errors, stable source inventory.13new portable regressions
pass; one additional Unix-only permission test awaits supported Linux execution.
All other passes are affected existing methods. Earlier focused subsets are
not added again. [Verification](VERIFICATION.md) and [machine result](affected-suite.json).

The nine affected RangePolicy methods pass, including1,000fuzz runs. Standalone
old/new KeeperVenue compile and disposable loopback Anvil observations verify
current version getters,8word Position/native identity and real current Keeper
reader; these are not Unix crash/recovery or actual Uniswap economics tests.

Production44Solidity/31normal dependency/four build pins remain unchanged;
existing37normal object and current static-review evidence retain their scope.
No speculative Solidity rewrite or guard relaxation was required.

## Remaining qualification and operator action

Deploy matching health writer/checker only through an authorized service rollout.
Old artifacts fail until a fresh cycle with the reviewed loaded config; never
edit hashes or clear journals to pass. New rehearsal source does not upgrade an
old installed fixture. Run the updated process campaign on supported Linux and
verify actual target-chain fee/RPC/gas/source/route behavior and off-host alerts.

Immediate governance and the chosen custodian can still lose/divert assets by
design. Token/proxy failure may block even raw exit; retired royalty receivers
cannot rescue new unadmitted currencies. Original VRF recovery, OpenSea primary
mint, authorities, independent feeds/routes, current3website/services, artwork
hosting, realistic strategy/MEV/gas and independent audit/remediation remain open.
Polling/wide ranges do not promise uninterrupted fees or protection from IL.

No public RPC/transaction/deployment/seal, existing Anvil8902/NFT/LP/balance/journal,
installed service, website source/build/server or paused monitor was changed.
Only isolated disposable fixture chains were used. Public DEPLOYMENT remains
null and browser signing Anvil-only. **Production NOT APPROVED.**
