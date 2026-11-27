# Clean keeper restart from a desktop-held kit — 27 November 2026

**c828 passes the finite clean application-root recovery composition against a separately retained, running local Anvil.**
One actual stock-keeper harvest was accepted and included before the desktop round trip.
The exact pending journal, original configuration and matching release returned from the desktop;
the fresh target verified/restored those bytes and reconciled that receipt without signing or resending.
Its first unsigned stock cycle exited **1 with the expected metadata-degraded health**;
a fresh second process exited **0 with dry_run_v2**.
The [target result](evidence/campaign-003/result2/TARGET2_RESULT.json) and
[final chain reads](evidence/campaign-003/fetch-final_chain/FINAL_CHAIN.json) retain their separate scopes.

This is recovery of application inputs against a retained isolated chain.
It is not a chain-history restore, physical second-host or OS disaster-recovery proof.
Production, readiness and canonical-adoption flags remain false.

**What ran.** The passing case reused the immutable, previously populated F6 base:
39 instances, two NFTs and an existing active LP position. No constructor, Entry population,
new deployment, seal or prior financial scenario was rerun.
[Fresh setup](evidence/campaign-003/fetch-bootstrap/BOOTSTRAP.json) made five isolated governance calls:
four controlled mock-feed timestamp refreshes with answers unchanged, and admission of one new disposable keeper.
Two local balance-funding calls are explicit fixture seams, not public funding or market-depth evidence.
The stock source then submitted exactly one local harvest.

| Passing c828 CLI partition | Actual operation | Result |
| --- | --- | --- |
| Stock source preparation | keeper.monitor --initialize-state, without --live | Fresh source journal only |
| Stock source submission | keeper.monitor --once --live | One actual accepted local harvest |
| Native source capture | keeper-recovery.py backup | Exact pending journal captured once |
| Native fresh-target review | keeper-recovery.py verify, then restore | Both exit 0 |
| Unsigned stock recovery | keeper.monitor --once, without --live | Exit 1; receipt booked, expected metadata degradation |
| Fresh unsigned stock cycle | Same unsigned CLI in a new process | Exit 0; fresh dry_run_v2 |

These are three native journal-tool invocations and four stock monitor invocations.
No old test body ran. Packaged test-source members remained inert.

| Preserved guard | Passing-case setting |
| --- | --- |
| Local node / maintenance gas | 32M node; 24M maintenance with full 25% padding |
| Keeper cadence / confirmations / harvest | 240 seconds / 12 / 3,600 seconds |
| Gas price / transaction / daily cost ceilings | 5,000,000,000 wei / 10,000,000,000,000,000 wei / 50,000,000,000,000,000 wei |
| Native recovery budget | 16 MiB / 60 seconds; original 900-second capture-age bound |
| Total RPC / hard node and gateway lifetime | 6,000 requests / 900 seconds |
| Combined command output / private input wire | 64 KiB / 2 MiB compressed and expanded |

**Actual acceptance and timing.** The new transaction is
0xbc4f7151d43ef650ad69027e1b81bdbc95de780f382221ff59c0f6b6c77046e1.
The gateway forwarded the signed request to Anvil once and independently checked the node-returned
pending transaction against the durable intent, sender, chain, nonce, calldata and fee envelope.
It did not fabricate a hash or merely retain an unsigned request.
The source writer and its restart path were fenced before capture.
The [inclusion record](evidence/campaign-003/fetch-included/INCLUDED.json) proves actual pending state before mining,
12 confirmations afterward and inclusion 66 seconds before the saved harvest deadline.
Inclusion occurred before desktop transfer, avoiding expiration of the unchanged 180-second harvest deadline.

Ordinary empty mining used the actual clock; no timestamp setter, launch timestamp override or as-of clock was used.
Twelve additional empty blocks before target2 refreshed both the tip and its confirmed observation anchor,
without creating another transaction or replacing the original receipt.
The unchanged 600-second head-freshness check and 900-second native capture-age check remained in force.
The older 86,400-second historical review allowance was not used.

**Desktop possession and fresh reconstruction.** The kit contained **45 exact files / 808,416 raw bytes**:
41 matching release files, their retained source manifest, the original raw configuration,
and the native journal manifest/journal pair.
The [desktop proof](evidence/campaign-003/desktop-kit/KIT_PROOF.json) reread all 45 private files;
its SHA-256 is 675282c7d2e577f0a3e13cf188bfd1a5f6868fbc2df80acc8bcbe2e234b2d9fc.
Release bytes came from current trusted Git source, not an old host-source fallback.
The 41-file manifest remains c287aa0c4b8e4113f7ffa1459f39a704bd17b5165f23084e3a8f26995cdb0e08;
the maintained source13/source19 identities and production ABI are unchanged.

The original captured and target pre-load journal are the same 2,752 bytes,
SHA-256 af9768346090961dd0799e11c8add3ea8269350ad1f7af37ccdf043a6a7d4498.
The native manifest pin is 6dab4a7754593d04b2785d2e6bf7b6907edb7dc55236f2dcc753fa48acf8fbf1.
Target2 copied only those verified desktop-imported inputs into fresh inodes.
The original configuration bytes and logical paths stayed exact; signer files and Cast were absent.
Native restore-plan readiness/adoption flags stayed false.
Raw configuration, journal, health records and compressed private review packets remain outside Git.

**Actual isolation and once-only accounting.** The target result records uid/gid 65534,
zero effective capabilities, a private network namespace shared with the retained node,
and a different cgroup from Anvil. Root and four copied-input inode checks passed.
The original source/configuration/secret paths and earlier application labs were unavailable inside the root.
Eighteen read-only OS-runtime mounts and the bounded Python stdlib inventory were independently checked.
These are explicitly external same-host OS dependencies, not a complete OS backup.

The [canonical record](evidence/campaign-003/fetch-canonical/CANONICAL.json) and unsigned target reconcile
**300,814 gas × 32 wei = 9,626,048 wei**, with zero additional L1 fee under the unchanged included-fee profile.
That cost was booked once to **2026-11-27**; pending cleared, the receipt anchor and fee observation matched,
and journal/latest/pending nonces became 1.
The second process preserved every checked financial/recovery field; only conversion_turn advanced.
The new keeper lock was empty, mode 0600, single-linked, owned by uid 65534, and retained its inode across both cycles.

Gateway raw attempts, raw forwards and transaction-method attempts stayed **1 / 1 / 1** before and after recovery.
The recovery transaction-attempt delta is **0**.
Final status records **2,119 / 6,000 RPC requests**.
FINAL_CHAIN.json snapshots 2,117 immediately before its two final nonce reads; this is the same bounded run.
The [initial](evidence/campaign-003/fetch-financial_initial/FINANCIAL_INITIAL.json),
[included](evidence/campaign-003/fetch-financial_included/FINANCIAL_INCLUDED.json) and
[final](evidence/campaign-003/fetch-financial_final/FINANCIAL_FINAL.json) physical vectors all match.
They cover NFT ownership/shares/eligibility, LP identity/liquidity, liabilities/reserves/claims and Vault ETH/ZZZ.
This fee-empty fixture does not add dynamic fee-allocation, real-market or sustained-operation qualification.

**Failures remain failures.** c826 stopped at the systemd-run client's host-side executable lookup:
no node, source keeper or transaction ran. A separate condition-false diagnostic confirmed the error without execution;
the fresh c827 added the supported ExecSearchPath property and retained bounded launch diagnostics.
c827 then stopped after 145 RPC requests because the report read helper rejected native-currency address zero.
Its five fixture governance calls belong to that separate partial case; no keeper harvest or raw submission occurred.
The c828 correction permits zero only in four exact read-only currency argument slots.
Transaction encoding and production address guards are unchanged; all 22 helper API contracts received static review.

c828's first target failed **226/NAMESPACE before any witness or keeper execution**:
the API-VFS /run overlay hid its prepared application paths.
That root, unit and attempt remain intact.
The separately pinned target2 continuation embeds controller 22d45943… byte-for-byte,
uses a new root/unit and binds only its own reconstructed /run read-only over the fallback overlay.
Its worker changes only the expected fresh-root identity literal.
No source, node, setup, submission or capture was replayed; no clock or resource cap was extended.
The original failed target is not relabelled as a pass.

**Cleanup and host preservation.** Final physical reads preceded node shutdown.
[Target2/fresh2 cleanup](evidence/campaign-003/stop2/SANITIZED_RESULT.json) and
[original-role cleanup](evidence/campaign-003/fetch-stop/FINAL_STOP.json) leave every new group empty.
All three lab campaigns are stopped; original immutable fixture inputs/tools match their retained hashes and metadata.
The [settled host comparison](verification/HOST_PRESERVATION.json) matches five existing states:
zero non-ambient differences and one disclosed periodic-observer invocation.
The [first observer-transition comparison](verification/HOST_TRANSITION_NONPASS.json) retains its five-difference NONPASS.
A separate local comparison path typo refused before input reading; its empty attempt is retained.
Existing services/sites, Anvil8902, original journals/assets and the user-paused desktop heartbeat remain unchanged.

**Operator boundary.** Preserve independent source/configuration/native-manifest pins and keep signer material separate.
Fence the old writer and every restart path; verify an existing exact journal before constructing a keeper.
Do not initialize a used sender or resend an uncertain transaction.
Reconcile the actual receipt, fee/day/nonce/anchor and physical after-state before any separate adoption.
Follow the [operator procedure](../../docs/OPERATOR_MANUAL.md#unsigned-keeper-restart-from-a-reconstructed-kit).
This lab retained its node deliberately; real provider availability, host-loss fencing, off-host chain/OS durability,
physical durability, sustained operation and independent release approval remain open under Q06/P20/P21.
The [independent saved-vector reconciliation](verification/SAVED_RECONCILIATION.json) passes **31 data-only checks**,
including all 45 kit files, eight private target records, 41 trusted Git source files, exact paid accounting,
dry financial-state preservation, final physical vectors, cleanup and host preservation.
Actual saved recovery age was **644.089 seconds, below the unchanged 900-second bound**.
The pinned worker checked actual native CLI stdout bodies; independent desktop review checked the raw restore plan
and captured process receipts, without independently fetching those stdout bodies.
The first saved-check timestamp-parser TypeError remains recorded; only saved timestamp parsing was corrected,
with no application, native, server or test rerun. These overlapping checks add no transaction or test-body count.
No production code, operating policy, financial limit or workload plan changed.
