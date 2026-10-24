# Hookless pool checkpoint: publication receipt

2026-10-24. Published on **main**; contracts remain undeployed and production
**NOT APPROVED**.

| Repository | Published work | Commit |
| --- | --- | --- |
| ABEF/AAA | Hookless native ETH/ZZZ admission, fee-aware planning, guarded pool moves, stricter normal-exit swap minimum, scoped evidence and current Todo/operator/architecture requirements | [7a1d564](https://github.com/ABEF/AAA/commit/7a1d564f3cb1c1aa34ab8e3a354c8f096493ae8c) |
| ABEF/AAA-website | Repository-memory update only | [5c5a1de](https://github.com/ABEF/AAA-website/commit/5c5a1de3708c09eff481c981f875aa44fe99ffc0) |

Both commits were pushed normally and authenticated with `git ls-remote origin
refs/heads/main` before this receipt was written. This receipt and the final
contract-memory update are a separate documentation follow-up, not a new code
candidate. Only main was used; no branch, PR or force push was created.

## Verification and limits

Read [scoped verification](VERIFICATION.md) and [internal review](REVIEW.md), not
an aggregate headline count. Earlier106/native24 fixture passes predate the final
exit-minimum fix. The final-source55-case scope had53 passes and two stale custody
fixture failures; corrected custody24 passed. Eight initial fork cases passed;
the two failing paths were corrected and rerun successfully. Those earlier eight
were not repeated. There is no fresh full final-source regression or independent
audit claim.

All94 source/test hashes in the final custody record match the published source
snapshot. All33 retained normal object gates remain source-bound; Vault runtime
24,019 bytes, with557 bytes margin. Nine focused Python checks pass against the
actual intended publication files, excluding older unrelated local runner/test
drafts. [Publication checks](runs/publication-python.json) and [raw output](runs/publication-python.log).
The generated Todo, intended-index Markdown file links and whitespace checks pass.
[Evidence hashes](artifact-sha256.json) cover the retained records; raw Forge logs
are preserved byte-for-byte, while JSON uses normalized LF line endings.

## Still unfinished

- [Native ETH accounting/recovery](../../docs/NATIVE_ETH_ARCHITECTURE.md): requested
  architecture, not implemented. This checkpoint still wraps native venue proceeds
  into WETH; raw exit remains wrapper-dependent.
- [Post-seal operational extensions](../../docs/POST_SEAL_POLICY.md): VRF request
  tuning, buyback operating ceiling and typed v4 conversion support need code and
  focused review before sealing. Current conversion executors remain v3-only.
- ZZZ LP-reward conversion keeps the user-approved1% limit, gas separate. Require
  a cheaper independently qualified route; the selected observed approximately
  1.101% swap charge cannot simply be accepted as a full-balance conversion.
- Real feeds/routes/VRF/services, release inventory, marketplace qualification,
  operating rehearsals and independent audit remain open. A real-funds rehearsal
  needs a separate reviewed deployment; there is no burn/reset or erasure of history.

## Preservation

No website source/build/server deployment, public contract deployment/transaction,
key use, service control,8902/Anvil/NFT/LP/balance/journal change or monitor restart.
Public `DEPLOYMENT` remains null and signing remains Anvil-only. Older unrelated
working drafts were intentionally left unstaged; this is not a claim that every
local draft was published. Both repository memories and operator/Todo guidance
record current requirements and implementation limits.
