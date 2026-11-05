# Factory deployment gas and exact claim planning

The selected improvements are implemented for the fresh source candidate.
**Undeployed; production NOT APPROVED.** Baseline main `4f7436a`.
[Verification](VERIFICATION.md) owns exact measurements and source/evidence pins.

The Factory previously stored25,522 deployment bytes in ordinary storage slots.
It now constructs two immutable inert data children, checks their exact runtime
length/hash, copies bytes after each three-byte REVERT prefix and verifies the
complete original creation hash before typed zero-value CREATE. The receiver's
creation bytes are byte-identical to the baseline, preserving royalty accounting,
NFT/controller binding and all holder rights. Neither caller-selected code nor
an execution/sweep/forwarding authority is introduced.

The exact-normal artifact comparison reduces Access construction gas by56.65%
and cold-read NFT construction by11.11%. Warm NFT construction falls0.93%.
These local inner-CREATE measurements exclude full wallet/network fees; normal
artifact runtime and initcode limits remain enforced. Unchanged instantiated
royalty runtime and exact source-payload identity are checked independently.

The two extra addresses are explicit in fresh schema14, outside17 modules and18
callable helpers. A fixed source-owned manifest derives their hashes and lengths
from normal compiler output. The read-only observer checks both actual runtime
bytes at the pinned block and reconstructs the whole payload. Observed code
cannot approve its own pin. Schema13 remains separately archived and inspectable;
settlement4/reporting5/canonicalV8 and existing runtime/journal profiles stay
unchanged. Ordinary mint/claim requests do not query the data children.

The new opt-in `/v1/claims/plan` keeps every explicitly selected NFT/currency/
ledger entry and prepares only the next exact unsigned batch. It tries bounded
subsets under existing32-entry,12M, fee and request limits, then freshly verifies
the selected batch through the existing preparer. Zero, blocked, unavailable and
remaining selections are explicit. An opaque refusal never proves a faulty token;
known provider/canonicality/global faults cannot produce a draft. Replan after
confirmation; no future transaction queue, silent omission or automatic resend.

Request-local caching covers successful same-block identity/admission metadata.
It excludes ownership, claimable/wallet balances, lifecycle, head/canonicality,
simulations, gas estimates and fee prices. Nested work shares one budget. The
existing prepare endpoint retains atomic exact-selection behavior; no ceilings
are widened. Claims remain original currencies without a royalty conversion job.

Operator procedures, full callable notes, short examples, current source profile,
central Todo/features/roadmap and repository memory are updated together. Stale
current references to royalty conversion, schema10 preflight and old Factory
storage are corrected; immutable old reports retain their source scope.

The new storage format requires Cancun-compatible opcodes and a fresh deployment.
Each data child rejects ordinary calls/native sends. Forced ETH and ERC20 transfers
cannot be prevented; never use these inert addresses as payment/custody targets.
Wrong fixed bytes require a fresh reviewed deployment, not a repair setter.

Actual Robinhood constructor/activation/claim gas, maximum currency/holder state,
RPC/fee semantics, frozen or malicious tokens, OpenSea, authorities, feeds/routes/
VRF, matching services/site, recovery operations and independent audit remain
release requirements. Source publication changes no existing service, website,
signer, Anvil state or journal. Public signing remains disabled and Anvil-only.
