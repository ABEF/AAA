# Manipulation-related hardening: verification

Fresh undeployed source, production NOT APPROVED. [Review](REVIEW.md) distinguishes
the concrete health correction, callback completion hardening and remaining
economic/ordering qualification.

## Implemented and actually checked

- **58 distinct affected Solidity methods pass**, including9 new completion
  cases: pause/revocation rollback and unchanged-authority controls for real Vault
  rebalance, the Compounder coordinator and direct-ZZZ Buyback. The compound Vault
  stub, authority fixture, callback burn token and synthetic reserve are explicit
  test substitutes. Existing affected native flows, cadence, rebalance budget and
  buyback suites are included; this is not a fresh whole-repository regression.
- Initial execution had57 passes and one stale fixture failure: the old approved
  wrong-pair test attempted admission without the immutable ZZZ token. Current
  admission correctly rejected that obsolete setup. The test now verifies rejection
  and reserve isolation; all22 methods in that changed buyback test file pass.
  Earlier failures are retained; no production guard/admission was relaxed.
- **314 distinct affected Python methods:311 pass,3 explicit skips.**17 new
  paid-revert health cases are included once. Coverage includes durable gas/nonce/
  pending reconciliation, failed-save/reorg/ambiguous receipt handling, current
  and expired cooldowns, fresh/unavailable chain time, restart/unrelated success,
  historical journals and strict paired checker fields. The skips are Foundry
  cast absent from the test PATH, actual Unix ownership/permissions, and actual
  Unix datagram semantics. They are not successful operating rehearsals.
- Initial Python fixture failures omitted mandatory live nonce/receipt-anchor
  fields; fixture-only corrections and overlapping intermediate runs remain in
  the external evidence. Final source hashes are equal before/after testing and
  match current files. Counts do not add those intermediate selections.
- **37 normal object size gates pass**,75 closed solc0.8.26/Cancun inputs,
  viaIR/optimizer1/Yul disabled. Vault runtime23,783 (793bytes margin),
  Compounder2,206, Buyback7,549; their recursive storage layouts are unchanged.
  NFT runtime remains24,400 (176margin). Exact release arguments and target gas
  remain qualification work. No compiler or size gate was weakened.
- Exact project/test metadata hashes match current source for60 execution inputs;
  normal source/build/dependency bindings are recorded separately. ABI signatures
  remain unchanged. Callable meanings were updated and regenerated:31contracts,
  607functions,31constructors/13receivers; no missing purposes/input meanings.
  Existing122 getter/unnamed-output annotation limits are not relabelled complete.
- Generated Todo and44-file narrow source consistency checks pass. They are not
  EVM execution, economic evidence or independent security approval.

See [commands, pins and result provenance](verification.json),
[unique Solidity methods](solidity-methods.json),
[Python result inventory/skips](operations-results.json) and
[normal size evidence](production-size-gates.json). Repository JSON copies use
LF; exact original logs/compiler artifacts and their hashes remain under the
external directory recorded in metadata. The58 Solidity methods are the union
of36 unchanged-source passes and22 final changed-file passes, not58+22.

## Operational and release limits

Matching health writer/checker rollout is unperformed. The three new markers are
`confirmed_reverts`, `active_revert_cooldowns`, `next_revert_retry_after`.
An active existing restriction remains observable, but other jobs/backoff and all
journal state accounting retain their old behavior. Expiry means retry eligibility,
not successful execution/market recovery. Actual host alerts and Unix/recovery
rehearsals remain open.

Post-callback completion checks revert the entire operation and callback policy
change together; they do not persist a callback's attempted pause or interrupt
another transaction. They introduce no new role/custody/economic authority.

The delegated economic-attack simulation was blocked by a platform security
screen. No attacker-profit, mainnet-fork or protected-submission qualification was
completed here. Post-close liquidity depth, execution slack, independent feeds,
buyback discretion and actual ordering/provider behavior remain in the
[keeper](../../TODO.md#task-security-keeper-manipulation) and
[outside-actor](../../TODO.md#task-security-external-manipulation) tasks.

No public transaction, deployment, sealing, signing policy, website/server,
Anvil/NFT/LP/balance/journal or paused automation/service was changed. The four
unrelated tracked drafts remain untouched. Production approval remains open.
