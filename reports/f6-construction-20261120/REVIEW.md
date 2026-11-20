# Current F6 construction, bindings and unsealed authority rehearsal

20 November 2026. Baseline `2891f6b29691449d6667d36b9c678a0746ce5d80`, main.
Trusted build: `activation-final-six-20261118`, Factory6/allocation2.
**Production is undeployed and NOT APPROVED.** Only new owned local chains were
used; no public transaction, sealing or existing environment was authorized.

## Result

The current full graph successfully performs **25 creations and19 bindings**,
discovers **39 actual instances** and passes the existing112 binding/state
assertions. These are real normal-build Access/Registry/Factory/module runtimes,
not the control mocks used by the earlier maximum-state producer. An additional
172 default/version/readiness observations pass against current ABI and raw wire.

A separate small fixture separates bootstrap from governance: two creations and
one policy binding produce six instances on another owned chain. Its35 read-only
permission cases produce nine successes and26 exact `Unauthorized()` rejections,
with35 relevant state checks and sender/factory nonces unchanged throughout.
Both nodes stop with no pending submission. The two inventories are separate;
do not add their reused addresses into a single45-instance production graph.

| Evidence | Result and boundary |
| --- | --- |
| Construction | All39 actual CREATE inputs/parents/returned runtimes match the trusted normal graph, including both inert Factory code children. No source or compiler change. |
| Bindings |112 independent expected bindings/state reads, source-pinned through the unchanged maintained checker. |
| Additional defaults |172 observations over28 targets, fixed local block44, no overlap with the112 original assertions. [Independent check](DEFAULT_VERIFICATION.json). |
| Authority |35 cases over six selectors in a distinct-role control fixture, fixed block3; nine exact successes and26 exact code3/`0x82b42900` errors. [Independent check](AUTHORITY_VERIFICATION.json). |
| Transaction preflight |132 ordered full-cap/estimate/padded calls and260 bracketing sender/factory nonce reads reconciled to the original immutable wire, exact submitted envelope and receipts. |
| Local canonicality | All44 numbered receipt headers and closing tip are linked to original node responses. This is coherent owned-local data, not proof of public-chain finality or provider honesty. |
| Preserved boundaries | Normal24,576-byte runtime/49,152-byte full-initcode gates, full25% construction padding and32M local transaction cap. No existing guard/default or permission changes. |

This closes the **current controlled F6 construction/binding rehearsal** portion
of P22. It does not close target deployment, real dependency/configuration,
contract-wallet/key, gas-fee, operating or independent approval requirements.

## Gas and size

[Gas records](GAS.json) preserve every estimate, padded allowance, exact submitted
gas and receipt usage. For the full44-transaction graph:

- Actual total gas: **144,113,280**; estimated total144,116,080.
- Worst padded creation: NFT,11,371,583 estimated/actual gas,
  **14,214,479 with full25% padding**, below the unchanged32M construction cap.
- Access full initcode:48,580bytes; Royalty creation code25,533bytes,
  NFT-created full Royalty initcode25,565bytes and runtime24,562bytes.
- Factory data-child runtimes:24,576 and963bytes. Payload6 identity is proved
  by exact reconstructed creation bytes and hashes, not a fictional public
  payload-version getter. `CODE_STORAGE_VERSION()==2` alone cannot distinguish
  F6 from earlier payloads in the same format.

The auxiliary three-transaction authority fixture separately uses14,054,626 raw
gas; it is not part of the production25-CREATE/19-binding deployment budget.
These are controlled local gas measurements, **not a Robinhood fee quote**.
Actual release addresses, argument byte patterns, final root, upstream state,
provider/execution limits and complete Nitro fees still need qualification.
Construction's25% padding is separate from contribution's20% policy; no budget
is raised or automatically adopted.

## What the permission cases establish

Bootstrap, governance, keeper, guardian, payee and outsider are fixed disposable
distinct addresses in the auxiliary fixture. No key is loaded or exposed.

- Before sealing, only bootstrap passes ordinary `canConfigure` and may
  simulate role/policy configuration; distinct governance must wait for seal
  for those configuration rights.
- Governance and bootstrap can pause/unpause; guardian can pause but cannot
  unpause. Keeper and outsider fail those calls with the exact expected error.
- Only governance can propose another governance address. All acceptance
  attempts fail while no proposal exists; this is not a completed key rotation.
- A registered keeper flag is true, but `keeperAuthorized` remains false while
  unsealed. Mapping membership is not permission to operate an unsealed protocol.
- Every `eth_call` success and failure leaves the35 checked state values,
  nonce snapshots and local head unchanged. No actual role/policy/pause write
  is submitted by the probe recorder.

The full graph retains the maintained runner's bootstrap/governance colocation;
the distinct-role fixture supplies the missing contrast separately. Neither
fixture exercises sealed operation, every operator selector, a real wallet
signature envelope, holder accounting or market execution. Those remain their
own evidence obligations.

## Complete readback is not complete seal readiness

The [readiness observations](READINESS.json) deliberately keep approval false.
The graph is unsealed/bootstrap-owned, with no NFTs, buckets or physical LPs,
fixed-ZZZ contribution/exit identities unset, ZZZ not admitted to Rewards,
converter disabled, SeaDrop mint helper unconfigured and randomness unconfigured.
Confirmation has its default duration but max observation gap0, requiring an
explicit operating configuration. Sale end0 may intentionally remain unset.

Native dependencies are constructor-only revert/selector doubles; they **cannot
pass real Registry native-code admission**. SeaDrop uses the archived code with
controlled storage, not an onboarded live collection. No feeds/routes/marketplace/
VRF/provider are qualified. The40-byte controlled artwork URI is not a verified
CID or production publication; its nonempty constructor value consumes the
one-time root choice. Never adopt these test addresses/configuration as a release.

## Verification method and limitations

The maintained runner, planner, ABI helper, normal artifacts, production code,
compiler, original evidence and build controls stay byte-identical. The new
report-owned [campaign](run_campaign.py) composes that runner with bounded
additional reads and a small distinct-role fixture. Expected-revert probes have
a separate typed recorder; the original success-only wire admission is not
weakened. All mutations retain the runner's fixed disposable sender, zero value,
owned PID/genesis/code guards, closed creation/binding allowlist and no seal.

[Additional offline verification](verify_execution.py) fills the maintained
checker's explicitly unproved preflight-field scope. Initial checker output is
retained; the final source-frozen run authenticates the100-source/four-control
closure and original envelopes. A verifier-source change during the review
required a second **offline** check; the actual EVM campaign was not repeated.

Ten new tamper-control methods passed at the first verifier stage; one newly
added build-control method passed separately. The original ten were not rerun,
and no final whole-file11-pass run is claimed. Initial whole-file test/source
hashes were not captured; final source hashes, stage limits and method names are
explicit in [verification](VERIFICATION.json). No unchanged suite, compiler,
normal size build or static analyzer was rerun.

One captured default-manifest metadata field spells a `bytes32` pool constant as
a decimal integer in `expected_values`; its authoritative `expected_return` and
actual RPC are already the same correct32-byte hex. The independent default
review records that representation normalization without rewriting the captured
manifest. Future operator calldata must use the ABI hex spelling. This is a
report metadata limit, not a contract or actual-return defect.

## Evidence and next work

[Evidence manifest](EVIDENCE_MANIFEST.json) binds the archive and each member.
The archive retains both stopped-node captures, all47 receipts, exact traces/
runtime proofs, permission raw responses, headers, source stages, initial and
final offline verification and recorded rejection/analysis limitations. Extract to a NEW
directory before passing `attempt1/full-graph` to the report verifier. The
archive's campaign layout is not the historical standalone checker's direct-ZIP
layout; do not relabel an old archive to fit it.

Before deployment still qualify actual inputs/addresses/final content, upstream
code/control/market/service compatibility, complete target fees, full canonical
cutover, supported populated claims/conversions and independent release review.
After separately authorized deployment, perform actual readback and separate
seal/public-opening decisions. Existing Anvil8902, journals/DBs/checkpoints,
websites/services and paused heartbeat are unchanged; both owned rehearsal nodes
are stopped. Production remains NOT APPROVED.
