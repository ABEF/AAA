# $1 local rehearsal verification - 2026-10-18

**10 focused Solidity cases and four generator-boundary Python cases passed.**
This is a separate local-only contract copy, with mocked venue, prices, VRF and
authority. No real funds were used and no public contract was deployed.

The generator changes the copied Entry and budget activation floors to $1 and
adds constructor checks for local chain ID 31337. The other 37 production Solidity
files are copied unchanged. Production remains at $100; all 39 repository Solidity
sources match the baseline main revision `350c00b32aa0b11ce2a27c5739bac37042451100`.
The mint price stays 0.05 ETH and the marginal deployed-LP limit stays 99%.

The successful cases cover $1 gross / $0.99 deployed, rejection below $1,
direct-entry floor independent of a lower pool setting, compounded conversion
and deployment loss rejection, oracle-priced stable input rounded upward,
top-ups preserving the shared LP and membership, accrued LP and native royalty
claims following a transfer, old-owner rejection, pause/owner restrictions,
nonzero swap-output minima and copied-constructor rejection on chain 4663.

The four Python checks cover the exact two-file transformation and preserved 1%
formula, missing/duplicated anchors, repository/ancestor output rejection and
existing-directory refusal. No unchanged broad production regression, static
analysis or size suite was repeated: production Solidity did not change.

The first Solidity attempt had four failures caused by a zero minimum-output
field in the new test fixture. Its generic-revert passes did not establish all
intended failure paths. The final fixture uses valid minima and exact error
selectors, and includes an explicit zero-minimum rejection. The original failed
receipt and diagnostic trace remain preserved; results are not merged.

## Evidence

- [Final verification](verification.json): case results, unchanged production
  hashes, tooling/manifest identity and raw-log hashes.
- [Generated source manifest](generated-manifest.json): original/copied hashes,
  compiler hash, minimum and scope.
- [Initial attempt](initial-attempt.json): retained failure and correction record.
- [Instructions and limitations](../../docs/ONE_DOLLAR_REHEARSAL.md).

Raw builds/logs remain outside Git under the session's
`dollar-rehearsal-20261018/` directory. The public wallet observation also stays
outside Git: native/USDG balances and token identities were readable, but live
price/route checking failed closed on an RPC HTTP error on both attempts. No
complete conversion or LP quote is claimed. The supplied private key was neither
used nor written to a file.

No production defect was found by this scoped run. New defects identified later
must be corrected in production and verified through targeted regressions. This
record does not authorize copying the $1 override into production, live funds,
deployment, website/server changes or restarting the paused monitor. Release
remains **NOT APPROVED**.
