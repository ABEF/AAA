# Knowledge applied

The current instructions, source6 contracts/interfaces, current consumers and
prior exact-source evidence establish product behavior. No provider, address or
economic parameter is inferred from an example or external recommendation.

- [Python3.11 AST reference](https://docs.python.org/3.11/library/ast.html):
  function/class/comprehension nodes have separate syntactic bodies; walking all
  descendants does not establish package-level bindings. The publication repair
  uses bounded syntactic scope and retains dynamic-export/runtime limitations.
- [EIP1898](https://eips.ethereum.org/EIPS/eip-1898): coherent block-specific
  reads matter for multiple dependent balances/identities. The shared custody
  cache is request/block-local; this neither authenticates a provider nor makes
  unavailable prices or contradictory custody valid.
- Actual source6 `Buyback.setMaximumTradeUSD` and `ProtocolPolicy` interfaces:
  current configuration is distinct from creation provenance, and a scoped
  maintenance fingerprint commits the exact address/bounds/revision. Neither
  reviewHash nor stored fingerprint is independent review/runtime attestation.

Primary online references were read for these narrow points. No new live-RPC,
service, market, provider, Solidity compiler or dependency qualification is
claimed. The reviewed source/dependency pins govern reuse, not a general claim
that a prior audit covers every new consumer or failure path.
