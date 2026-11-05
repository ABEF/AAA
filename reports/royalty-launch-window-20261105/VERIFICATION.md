# Verification scope

Final policy:3600seconds after official mint end. Internal source/fixture checks,
not production or independent approval. [Exact evidence](evidence.json) records
source hashes and external attempts, including24-hour drafts and failures.

| Check | Result and limit |
| --- | --- |
| Normal production compile |51production/31dependency sources;42normal runtime/initcode gates pass, Solidity0.8.26/Cancun/viaIR/optimizer1/Yulfalse. No gate was relaxed. Royalty/NFT/Factory and V7 source pins are final. Exact deployment arguments and target gas remain unqualified. |
| One-hour EVM |125distinct selected successes across explicit source-stable stages.110-case core stage had one preseal-VRF fixture error; its other109passed. Corrected callback plus15additional integration methods pass in16-case stage. Includes1000NFT mixed holders/rarities/one dormant,1000-input fuzz, transfers/claims/outages/cutoff/capacity/allocation, actual local-v4 growth/fees/compound/rebalance and holder return, and three actual funded canonicalV7 cases. No full suite or public-chain rehearsal. |
| Python |183affected API/history/checkpoint/observer/gate/authority methods pass at recorded stage;71reference/static/publication methods also pass. Stages are separately scoped, not summed. Initial native-zero encoding/old template assertions were corrected without relaxing production guards. |
| Website source |157selected read/unsigned/wallet-control cases pass, source stable/shared signer unchanged. Locked royalties excluded while LP claims remain available; original-currency selection stays. Dormant cards show no deadline by user request. No browser/live-server rollout. |
| Internal static |Fresh Slither0.11.6/crytic-compile0.4.2 analyzes final normal compiler artifacts:479alerts,103current/ambiguous contexts reviewed and376unique exact referenced-source reuse. Nonzero detector exit retained. Accepted gas/dependency/timestamp/complexity risks are explicit; alerts are not exploit proofs or independent approval. |
| References |36contracts/809functions/36constructors/12receivers;857short operator examples,0input/output/explanation gaps. Generators/checks source-bound to final compiler output. No signing/simulation readiness inferred. |
| Preservation |Four protected dirty files and all earlier tracked reports preserved byte-identically. Events retain all176prior descriptors. Main-only source publication does not deploy/seal/restart/reset/submit public transactions or enable signing. |

The preseal-VRF error came from configuring a test coordinator after sealing;
moving fixture setup before seal restores the real rule. Other retained failures
were old claim-window assumptions and an expectRevert consumed by a getter;
updated phase-aware fixtures preserve their economic assertions. The prefund
regression led to separate openingPool storage rather than sweeping orphaned
prefunds. Earlier24-hour static/build/test artifacts are not final evidence.

Remaining: real OpenSea/final-stage binding, actual currencies/providers/authorities,
gas and64-currency workload/recovery qualification, matching fresh site/services,
checkpoint rebuild/restore, public CI and independent audit/remediation. No real
funds or production acceptance is claimed.
