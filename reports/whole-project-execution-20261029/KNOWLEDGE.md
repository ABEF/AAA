# Selected primary knowledge

These sources informed specific checks; documentation is not runtime evidence.

- [Solidity security](https://docs.soliditylang.org/en/v0.8.26/security-considerations.html)
  and [known bugs](https://docs.soliditylang.org/en/latest/bugs.html): callbacks,
  state-before-pay, bounded work, compiler-condition applicability. Actual local
  OpenZeppelin5.4/v4core1.0.2/periphery1.0.3/Permit2 code was read; package names
  do not authenticate deployed runtimes. [Applicability](COMPILER_DEPENDENCIES.md).
- [Ethereum JSON-RPC](https://ethereum.org/developers/docs/apis/json-rpc/)
  and [EIP1898](https://eips.ethereum.org/EIPS/eip-1898): canonical anchored
  observations, transaction/log identities, valid filtered gaps and final depth.
- [ERC721](https://eips.ethereum.org/EIPS/eip-721),
  [ERC2981](https://eips.ethereum.org/EIPS/eip-2981) and
  [ERC4906](https://eips.ethereum.org/EIPS/eip-4906): owner/approval/receiver
  semantics, requested versus funded royalties and cache refresh limits.
- [EIP170](https://eips.ethereum.org/EIPS/eip-170) and
  [EIP3860](https://eips.ethereum.org/EIPS/eip-3860): separate runtime and total
  initcode limits, including actual constructor arguments. Headroom is not gas qualification.
- [Python JSON](https://docs.python.org/3/library/json.html) and
  [SQLite transactions](https://docs.python.org/3.11/library/sqlite3.html#transaction-control):
  ambiguous/nonfinite inputs, atomic durable snapshots and committed projection.
- [XML stylesheets](https://www.w3.org/TR/xml-stylesheet/),
  [XML Base](https://www.w3.org/TR/xmlbase/),
  [CSS escapes](https://www.w3.org/TR/css-syntax-3/#escaping),
  [SVG animation](https://www.w3.org/TR/SVG2/animate.html): parser-discarded or
  alternate resource/style channels must not bypass an approved static format.

Available skill descriptions were evaluated. Image/office/site-generation and
OpenAI-product skills do not fit a source/refactoring audit of this existing
project. No skill was invoked just to match a keyword; no audit plugin was installed.
