"""Reconcile this follow-up into current guides without rewriting old evidence."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/operator-behavior-followup-20261117/docs-before')


def change(name, transform):
    path = ROOT / name
    raw = path.read_bytes()
    dest = ARCHIVE / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        dest.write_bytes(raw)
    old = raw.decode('utf-8')
    new = transform(old)
    if old != new:
        path.write_bytes(new.encode('utf-8'))


def insert_after_title(text, paragraph):
    at = text.index('\n') + 1
    return text[:at] + '\n' + paragraph + '\n' + text[at:]


def manual(text):
    marker = '### Fixed ZZZ setup order'
    addition = '''### Verify artwork before sealing

The current controller rejects `Access.seal()` while
`NFT.artworkBaseURI()` is empty. A blank NFT constructor root is still allowed
during setup: bootstrap must call the one-time `NFT.setBaseURI(base)` before
sealing. Read the root back, verify the reviewed immutable content and all four
evolution paths, then independently complete every other seal prerequisite.
The nonempty check does not validate a CID, hosted content or OpenSea retrieval.
A rejected seal preserves bootstrap and bindings; a successful seal erases
bootstrap and permanently prevents changing the artwork root. Do not seal merely
because this one read succeeds. Use the fresh `operator-seal-20261117` build
family; older construction receipts retain their original controller scope.

'''
    assert marker in text
    text = text.replace(marker, addition + marker, 1)
    marker = '<a id="deep-cleanup-review---2026-10-25"></a>'
    addition = '''### Revoke and replace a keeper key

Only an authorized keeper address can perform keeper work. The extra software
rule that waits near/outside the adjustment threshold or during pending geometry
remains **service-only by the operator's explicit decision**. An authorized key
using other software can ignore that extra rule where the contracts permit;
contract authorization, cooldowns, financial guards and atomic rollback remain.

For a compromised limited keeper key, use the separate uncompromised governance
wallet:

1. Pause ordinary operations with `Access.setPaused(true)` if the incident calls
   for it. Confirm the receipt; pause blocks both ordinary compound and harvest,
   while funded holder claims remain separate.
2. In the operating sealed lifecycle, call `Access.setKeeper(oldKeeper,false)`.
   Confirm `KeeperChanged(oldKeeper,false)`, `keepers(oldKeeper)==false` and
   `keeperAuthorized(oldKeeper)==false`. This setter works while paused. During
   reversible canonical preparation, configuration is locked: pause first and
   review the exact preparation cancellation before changing roles. Frozen or
   retired systems do not regain operating authority just to rotate a key.
3. Reconcile every pending hash, nonce and spend record. A transaction ordered
   before revocation can still execute; revocation does not undo a mined result.
   Do not delete a journal, guess nonce adoption or resend an uncertain action.
4. Qualify the replacement wallet and reviewed keeper release, then call
   `Access.setKeeper(newKeeper,true)` and verify its mapping/authorization.
   Configure the reviewed sender and a separately reviewed state identity; never
   relabel an old sender's journal. Fund gas and use the documented controlled
   service restart/adoption procedure. Source publication itself changes nothing
   running.
5. Review remaining incident causes, then governance may call
   `Access.setPaused(false)`. A new key does not reset cooldowns, observation
   evidence, liabilities, LP geometry or NFT shares. Verify old-key rejection
   and inspect new-key readiness before resuming work.

One human may operate both roles, but reusing the same signing key removes this
recovery separation: compromised governance can grant authority again. There is
no hidden administrator that repairs lost or compromised governance.

'''
    assert marker in text
    text = text.replace(marker, addition + marker, 1)
    marker = 'Harvest first creates the designated 5% reserve; standalone compound also harvests'
    addition = '''The maintained keeper now refreshes chain time after slow reserve/maintenance
reads **before** deciding whether enabled compound or standalone harvest is due.
The fresh head also supplies that action's deadline; a failed/retreated head is
not replaced with a guessed time. Pending-transaction recovery still comes
first. This avoids an extra polling delay when the interval passes during reads;
it does not promise a transaction at an exact hour. Existing intervals, gas
budgets and on-chain readiness remain. Adopting the changed worker requires a
reviewed controlled restart, preserving sender/configuration/journal identity;
no on-chain setting or old pending record is rewritten.

'''
    assert marker in text
    text = text.replace(marker, addition + marker, 1)
    marker = '### Read royalty status and conversion history'
    addition = '''#### Stabilize the cohort for a reviewed recovery

Unallocated royalty recovery uses the active weighted cohort **when the
allocation transaction executes**. `reviewHash` records the review; it does not
freeze that cohort. An NFT activated ahead of allocation can join under the
approved economic rule. Already earned liabilities are never reallocated.

If a stable cohort is needed, governance can first confirm
`PoolRegistry.disablePool(currentPoolId,true,false)`, then read the cohort and
allocate the reviewed unallocated currency. This stops new activations/growth
through both Entry and direct Vault calls, without globally pausing recovery.
An activation ordered before the stop may still succeed. Keep global pause false
because royalty allocation rejects a globally paused controller. Restore the
reviewed complete pool configuration through `configureNative` afterward;
re-enabling requires healthy validation and is not a boolean-only undo. Existing
claims/transfers remain subject to their own rules. This is an optional use of
existing controls, not a new allocation permission or guaranteed recovery of a
broken token.

'''
    assert marker in text
    text = text.replace(marker, addition + marker, 1)
    text = text.replace('is a nonzero reviewed classification/beneficiary fingerprint.',
                        'is a nonzero reviewed classification/beneficiary fingerprint, not an on-chain cohort lock.')
    return text


def main():
    short = ('The [behavior follow-up](reports/operator-behavior-followup-20261117/REVIEW.md) '
             'fixes irreversible empty-artwork sealing and keeper due-clock lag, strengthens '
             'royalty recovery checks and updates obsolete canonical test fixtures. Actual '
             'keeper revoke/replace and LP execution checks retain their stated local scope. '
             'Extra compound waiting remains service-only by explicit operator choice; '
             'production is not approved.')
    for name in ('README.md', 'PROJECT_CONTEXT.md', 'AGENTS.md'):
        change(name, lambda s: insert_after_title(s, short))
    for name in ('docs/IMPLEMENTATION_STATUS.md', 'docs/WORK_HANDOFF.md'):
        change(name, lambda s: insert_after_title(s, short.replace('(reports/', '(../reports/')))
    change('reports/README.md', lambda s: insert_after_title(s,
           short.replace('(reports/operator-behavior-followup-', '(operator-behavior-followup-')))
    change('docs/ROADMAP.md', lambda s: insert_after_title(s,
           'The [behavior follow-up](../reports/operator-behavior-followup-20261117/REVIEW.md) '
           'closes confirmed sealing/setup and due-clock defects, and repairs stale current-'
           'behavior fixtures. Keep actual markets, provider/host, maximum-state gas, '
           'OpenSea/VRF and independent approval as the next release prerequisites. '
           'Software-only compound coordination is an accepted decision, not a pending '
           'on-chain policy change.'))
    change('docs/RELEASE_CHECKLIST.md', lambda s: insert_after_title(s,
           'The [current controller fix](../reports/operator-behavior-followup-20261117/REVIEW.md) '
           'requires the fresh source-bound `operator-seal-20261117` build. Older constructor '
           'receipts do not qualify the changed controller. Normal size and scoped local '
           'behavior/static checks are evidence, not real dependency, deployment, fee or '
           'operating approval. All release sign-offs remain unchanged.'))
    change('docs/OPERATOR_MANUAL.md', manual)

    def ledger(text):
        data = json.loads(text)
        data['reviewed'] = '2026-11-17'
        additions = {
            'security-governance': 'The [17 November behavior follow-up](reports/operator-behavior-followup-20261117/REVIEW.md) fixes actual sealing with an empty artwork root: rejection retains bootstrap, then a one-time configured root can seal. Exact ABI/storage stay unchanged. The fresh trusted controller build is operator-seal-20261117; all48 normal gates and scoped static review pass. This checks nonempty root only, not content/marketplace availability or release approval.',
            'keeper-guardrails': 'The [behavior follow-up](reports/operator-behavior-followup-20261117/KEEPER_REVIEW.md) fixes interval crossings during slow reads by refreshing chain time before compound/harvest due decisions. Nine new worker checks plus one adapted timing check pass with injected RPC. Actual-core authorized/revoked/replacement/pause checks are separate. Extra compound waiting remains software-only by explicit operator choice; governance can revoke/replace its limited keeper key. Existing cooldowns/guards/journals and running services stay unchanged.',
            'royalty-eth-settlement': 'The [behavior follow-up](reports/operator-behavior-followup-20261117/RIGHTS_REVIEW.md) strengthens recovery fuzz to require exact six-ticket recipient payouts and full drainage/repeat-zero across1000 inputs. Recovery still uses active weights at transaction inclusion; reviewHash does not freeze the cohort. Optional existing contribution-stop/re-enable workflow is documented. Broken admitted tokens and incompatible receivers remain dependency limits, not a universal no-stuck-funds guarantee.',
            'audit-release': 'The [behavior follow-up](reports/operator-behavior-followup-20261117/REVIEW.md) adds actual behavioral verification beyond the earlier92-action input inventory, repairs a retired two-token canonical fixture and preserves exact finite coverage. Current Slither570=5 individually current+565 exact unique referenced-source reuses; internal triage is not independent approval. No unchanged suite or live environment is rerun/adopted.',
            'deployment-initcode': 'The fresh [operator-seal build](reports/operator-behavior-followup-20261117/build/BUILD_PINS.json) changes only the controller creation/runtime objects across48 checked normal objects. Controller full constructor48377/49152bytes leaves775bytes; Oracle runtime retains3bytes and Vault32bytes. Current default planner admits exact new pins; metadata2/manual families stay historical and cannot silently qualify changed source. No new construction rehearsal/deployment/fee approval is claimed.'
        }
        found = set()
        for area in data['areas']:
            for task in area['tasks']:
                if task['id'] in additions:
                    task.setdefault('acceptance', []).append(additions[task['id']])
                    found.add(task['id'])
        assert found == set(additions)
        # Preserve the file's established JSON formatting and CRLF convention.
        newline = '\r\n' if '\r\n' in text else '\n'
        return (json.dumps(data, ensure_ascii=False, indent=2) + '\n').replace('\n', newline)
    change('docs/project-todo.json', ledger)
    paths = sorted(p for p in ARCHIVE.rglob('*') if p.is_file())
    manifest = {str(p.relative_to(ARCHIVE)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    (ARCHIVE / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print('Updated current guides and task acceptance; original files archived externally.')


if __name__ == '__main__':
    main()
