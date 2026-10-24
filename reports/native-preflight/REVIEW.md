# Native production preflight: internal review

Recorded 2026-10-24. This reviews release-inventory tooling, not a new contract
implementation or independent audit. Public contracts remain undeployed and
production is NOT APPROVED.

## Trust boundaries

The offline gate compares declared approved policy and retained qualification
against read-only observations. It cannot authenticate who wrote a manifest,
a report or a claimed approval. Approved runtime pins must come from reviewed
release-specific artifacts with constructor values; successful observation must
never become approval automatically. Proxy/configuration and governance review
remain separate from code hashes.

The observer has a finite read-only RPC allowlist. It does not load a signer,
request a wallet, send transactions, deploy contracts, administer services or
change limits. Only the explicitly named read-RPC environment variable is read;
URLs and original provider exceptions are excluded from diagnostics. It copies
the input and writes a separate observation atomically.

## Findings corrected in this implementation

- **Version confusion:** the old blanket refusal is retained for schema 4.
  Explicit schema 5 checks current native accounting/routing, actual helper
  getters, canonical identity and retired zero module slots. Existing WETH state,
  local contracts and journals are never relabeled.
- **Missing or invented observations:** canonical network/genesis/block/depth and
  the final header are checked. Malformed/reverted values become unavailable;
  global anchor failure preserves the previous report. ABI types are code-owned,
  including bool/address/native distinctions and decimal-string policy inputs.
- **Incomplete custody and route visibility:** both native-first ledger asset
  inventories reconcile counts and indices. A nonzero external creator-reward
  receiver count blocks this profile explicitly. Pool/source/route mappings still
  require independently reviewed creation-to-current-anchor history; supplied
  IDs alone cannot prove completeness.
- **False operating readiness:** actual pause flags, zero bootstrap, role history,
  helper bindings, both converter identities, current loss limits and immutable
  maxima are checked. Direct, typed v3 and typed v4 descriptors are distinct.
  ETH is zero with no runtime; an ERC20 wrapper needs its own reviewed policy.
- **Stale qualification scope:** historical rehearsals keep their real tested
  block. Exact source/deployment/configuration, route/source/parent and current
  loss settings must match; mutable pool/governance configuration has explicit
  digest binding. Fresh observation and complete current admission history stay
  separate from older unchanged test evidence.
- **Malformed input and output corruption:** finite file/RPC/work limits,
  duplicate/nonfinite JSON rejection, sanitized errors, distinct input/output
  paths and atomic replacement preserve prior reports and approved inputs.

## Remaining review and qualification

No real PoPL deployment or actual provider was observed. Synthetic passing
records prove the checks compose; they do not prove those records are true.
Unknown authority addresses, independent ZZZ/native pricing, actual conversion
routes, target-chain RPC/VRF/keeper/API/metadata/OpenSea operation, gas rehearsals
and independent audit/remediation still block the example and release.

The current profile covers one active native-V2 canonical deployment with no
external creator inboxes. Cross-chain canonical completion, legacy V1 import,
atomic ETH/WETH principal conversion and external inbox inventory qualification
are not supplied. Governance retains immediate authority and accepts external
custody trust; this tool does not remove those risks. Execution checks still
run for each real operation under fresh prices, minima, deadline and gas policy.

No Solidity, website source/build/server, shared signer or existing local chain,
NFT, LP, balance, journal, repair overlay, service or monitor was changed. Earlier
contract checks retain their original scope; no fresh full regression is claimed.
See [verification](VERIFICATION.md), [operator runbook](../../docs/PRODUCTION_PREFLIGHT.md)
and the [single Todo](../../TODO.md).
