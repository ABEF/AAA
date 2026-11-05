# Verification scope

Baseline bce897c. Internal focused verification of original-currency royalty2,
not production approval. Raw commands, source hashes, outputs and earlier failed/
empty attempts are retained in the external evidence directory in evidence.json.

| Check | Result and boundary |
| --- | --- |
| Production changes | RoyaltyRewards removes conversion and replaces recovery1 with same-currency allocation; RoyaltyConverter removed from src. Other production source bytes and31dependency pins remain unchanged. Legacy implementations are explicit test-only fixtures. |
| Normal compile |51production/31dependency sources,42normal runtime/initcode gates pass at pinned Solidity0.8.26/Cancun/viaIR/optimizer1/Yulfalse. Royalty runtime22559→18580; factory24113→20127. Target deployment gas/arguments still unqualified. |
| Selected EVM |58methods pass at the corrected royalty/claim stage, including1000NFTs/999active across mixed wallets and all rarities, one dormant, exact original-token wallet deltas and1000-input conservation fuzz. Three additional canonical cases verify both reward ledgers, destination-prefund exclusion and real local native custody handoff.61distinct current successes; no broad contract suite rerun. |
| Python |144affected methods pass at their recorded stage. The later131-method stage retains one obsolete source-inventory failure; the required class list is corrected and15selected methods pass. Counts overlap; final source/reference checks are recorded separately, never summed. |
| Website |Final156selected cases pass with source hashes stable and shared signer unchanged. Includes non-ETH-only claim enablement, per-currency fallback, full unsigned ETH+USDC review, incorrect metadata/selection rejection and existing local-only wallet controls. Earlier187/153pass and152case failed stages overlap; not added. |
| Static |Fresh Slither0.11.6/crytic-compile0.4.2 completes with466alerts and a nonzero detector exit.25changed/ambiguous contexts explicitly reviewed;441unique normalized contexts reuse exact referenced source and prior rationale. Full strict review/default updated together. Alerts are not confirmed vulnerabilities or proof of safety. |
| Callable and inventory |36contracts/797functions/36constructors/12receivers;845short example rows, no explanation/input/output gaps. Schema11 authenticates18helpers/no royalty routes; schemas10and older are explicit historical inspection. |
| History/API |Reporting3 requires runtime-bound settlement2/converter:null; currencies remain raw, no pending ETH. New allocation event credits only that currency once; old descriptors remain exact. Checkpoint semantic source changes require reviewed rebuild/re-pin. |
| Raw admission |91selected final Python methods pass after removing the obsolete release requirement for royalty-to-ETH routes. Explicit royalty-only original claims may omit a USD policy; token metadata and admission still validate. Assets also used for LP/contributions/conversion retain mandatory pricing. Old profile validation/observation controls pass; no guessed price or changed financial guard. |
| Preservation |Four protected dirty files, earlier tracked report bytes and shared signer preserved; existing sites/services/Anvil/holdings/journals unchanged. Source/docs publication only. |

The first EVM run's single failure was a test prank consumed by a getter before
calling the router; resolving the router before the prank corrects the fixture,
without changing any production guard. Initial Python failures were a test
reading balances from the reporting summary instead of claimable.royalties and a
fresh fixture retaining obsolete royalty routes. The first canonical selection
matched zero tests and is retained as a non-pass; the corrected selection runs
three explicit methods. A website test initially read claim_operations instead
of the API's existing reviewed claims field. No failed/empty attempt is counted.
The later152-method Python stage retained one new observer-fixture failure:
its synthetic runtime pins had not been patched to the fake RPC's code. Correct
fixture pins produce61passes without weakening the production observer, followed
by the final91-method raw-admission/historical-control stage. Counts overlap.

Actual token behavior, OpenSea payments, maximum populated target gas, matching
API/site rollout/restore and independent audit/remediation remain open. No source
change authorizes deployment, sealing, public signing or a running-service change.
