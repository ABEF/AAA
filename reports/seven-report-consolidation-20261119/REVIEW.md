# Seven subsequent reports: current findings and remaining work

19 November 2026. Source baseline main: `f1ef361cccfd5d88136463c9cdd107491aca67ef`.
Production remains undeployed and NOT APPROVED.

This reconciliation covers all seven report families added after the
[previous consolidation](../five-report-consolidation-20261117/REVIEW.md), including
the local32M candidate. Selection follows first Git publication, with that local
report included explicitly. [SCOPE.json](SCOPE.json) pins1,363 original files,
including64 Markdown files. No original report is rewritten or deleted.

The [disposition matrix](RECONCILIATION.json) carries every original64 ID forward
and separately assesses24 subsequent issues, implementation changes, decisions
and limits. These are not88 new vulnerabilities. Nineteen original rows have
changed cited source hashes; their relevant behavior was reinspected. Their
previous dispositions still hold. The original registry remains immutable.

## Reports reconciled

| Report | Current interpretation |
| --- | --- |
| [Launch workload](../launch-workload-20261117/REVIEW.md) | Capacity/admission, first activation versus growth, optional sync, cold claims and maximum-component limits remain distinct. Old whole-claim gas figures are historical after F6 code changes. |
| [Keeper recovery](../q06-keeper-recovery-20261117/REVIEW.md) | Stop-before-sign and watchdog failover corrections remain source-exact. Finite Linux/inert-signer recovery does not qualify the actual normal daemon and release host. |
| [Earlier Q03 gas](../q03-activation-gas-20261117/REVIEW.md) | Its old pending-currency refusals and rejected allocator experiments retain their exact source scope; they are not current F6 failures. |
| [Royalty rounds](../royalty-rounds-20261118/REVIEW.md) | Bounded exact rounds, funded read isolation and synchronized-prefund import correction remain implemented. Historical C08 sizes and8 padding refusals are superseded only where later measured. |
| [Intermediate gas reduction](../activation-gas-20261118/REVIEW.md) | Exact carry/projection changes improved the recorded workloads; its six remaining refusals and component regression are resolved by later matched F6 evidence. |
| [Final six resolution](../activation-final-six-20261118/REVIEW.md) | All13 controlled cold cases pass20M/full20%, closing all six previous matched refusals. Wider workloads and release qualification remain open. |
| [Selected32M profile](../contribution-gas32-20261119/REVIEW.md) | Existing schema2 supports the new non-live candidate; seven original new software checks are separate from20M EVM evidence and actual32M/provider acceptance. |

## Resolved implementation problems

The stop-during-intent race now checks an observed stop before signer launch and
retains the hashless recovery record. Completed bounded HTTP failover attempts
report real main-thread watchdog progress; blocked I/O is not disguised as health.
All three implementation files still match the Q06 evidence exactly.

Royalty reads are separately bounded and funded before a failed currency can
defer enrollment. Other partial accounting failures revert. Receipt allocation
uses constant-size rounds rather than holder-tree writes, with bounded birth
lookup. Replacement import no longer double-counts synchronized target opening
prefunds. Checked liabilities, original units, one-hour/fault cohorts and funded
abort remain separate from those implementation optimizations.

Current F6 compact/full-width spill codecs, transaction-only contribution Pricing
and Oracle/feed projection optimizations preserve the reviewed logical rights and
external-call proofs. All six matched gas refusals close: worst16,460,899 raw gas
becomes19,753,079 with full20% padding. The13 cases are scenarios from one existing
1,000-NFT producer, not13 new test methods or universal maximum-state acceptance.

No production implementation is changed in this consolidation. These corrections
were made in the originating source stages; their tests are not rerun or added
into a new whole-project pass count.

## Current policy and source boundaries

- Trusted build remains `activation-final-six-20261118`, explicit Factory6 and
  allocation2. [Source reuse](SOURCE_REUSE.json) checks61 project sources,
  39 dependencies and4 build controls against exact recorded hashes: no mismatch.
- Selected contribution candidate is32M/full20%; maximum admitted estimate is
  26,666,666. Each transaction receives its exact padded allowance, rather than
  automatically the whole ceiling. Defaults12M and maintenance24M/full25% remain.
- A synthetic Nitro header is not actual transaction execution capacity. The
  current helper clamps the header only. The last execution32M observation is
  dated13November; the19November identity refresh failed before obtaining state.
  Current capacity/provider/complete-fee approval is still absent.
- Current runtime/headroom: Royalty24562/14, Manager24459/117, Oracle23406/1170,
  Vault24544/32 bytes. Access full initcode is48580/49152. Old Oracle3-byte/C08
  figures are historical. Passing size gates is not construction/release approval.
- Fresh private codecs require exact F6 source/runtime/Factory pins and logical
  canonicalV10 import. Old physical slots, payload5 environments and journals
  cannot be copied or relabelled. ABI selector/type equality does not imply all
  JSON parameter names or private layouts are identical.
- Extra compound waiting remains a keeper-software policy. Cumulative loss caps
  remain declined. Governance emergency financial checks remain explicitly
  optional. Unallocated recovery uses actual inclusion-time active weights.
  Questions about gas ceilings did not authorize removing the selected policy.

## What remains open

The original Q01-Q07 remain seven broad **qualification buckets**, not seven
remaining coding bugs. [The index](INDEX.md) gives each original and later item.

| Bucket | Required remaining evidence |
| --- | --- |
| Q01: markets | Actual independent ETH/ZZZ sources and compatible, usable bidirectional depth/routes; controlled prices/liquidity do not qualify markets. |
| Q02: execution and fees | Current transaction/block and provider bounds, complete Nitro fees and explicit spending ceilings; fresh F6 construction/bindings and exact operations. |
| Q03: populated workloads | Selected currencies and64-currency/two-LP/order scenarios where supported, current cold claim batches, full latest-codec canonical coordinator/funding/abort and actual32M whole-operation checks. Component/setup allowances and older gas numbers are insufficient. |
| Q04: authorities | Reviewed actual governance/guardian/keeper/payee and contract-wallet execution envelopes. |
| Q05: external integrations | Actual OpenSea drop/stages/fees, supported VRF/liveness/funding, immutable content/hosting and marketplace metadata acceptance. |
| Q06: operation | Matching consumers, actual keys/Cast/provider/full normal loop, interruption and disk/DNS/body faults, off-host recovery/fencing/alerts, host loss/key rotation and sustained acceptance. |
| Q07: release approval | Exact frozen-release independent audit, remediation and final sign-off. |

Frozen/malicious assets, rejecting recipients, pending randomness, coupled
per-NFT principal legs and immutable mistakes retain their explicit limits.
Exact backing cannot make arbitrary tokens transferable or guarantee canonical
completion through a failed token. Smaller healthy claim batches preserve other
rights without claiming every imaginable asset can always be paid.

The inaccurate Royalty packed-status inline comment is a deferred editorial
item: actual fields are16/16/16 with bit48. Correct it during the next justified
source revision and repin, rather than invalidating the qualified build solely
for a comment. Rejected engineering experiments are not unfinished requirements.

## Current-document corrections and verification

Current guidance now uses the selected32M profile, actual F6 sizes/private codec
identity and resolved finite gas status. Repeated chronology is removed from
instructions/context/handoff, roadmap and release preambles. The operator guide
labels older cold-claim gas measurements as historical and explains the exact
sale-end revision boundary: equality with the old end is allowed if the new end
is future and opening is not finalized; a later timestamp is rejected.

Original dirty documentation was archived and hashed before consolidation.
The Todo remains the only task ledger. [Verification](VERIFICATION.json) records
source/old-report preservation and current document/reference checks. No old test,
compiler, static analysis or RPC campaign is rerun. The32M report's seven checks
retain their original single-run scope.

All financial and NFT rights, services/sites, existing chains/databases/journals,
signer, public null configurations and user-paused heartbeat remain unchanged.
Source/docs publication is separate from any operating rollout or deployment.
