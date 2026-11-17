"""Reconcile current guidance; preserve original historical report bytes."""
from pathlib import Path
import hashlib
import json

ROOT=Path(__file__).resolve().parents[2]
ARCHIVE=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/test-seal-deep-review-20261117/docs-before')


def edit(name,fn):
    p=ROOT/name;raw=p.read_bytes();a=ARCHIVE/name;a.parent.mkdir(parents=True,exist_ok=True)
    if not a.exists():a.write_bytes(raw)
    text=raw.decode('utf-8');new=fn(text)
    if new!=text:p.write_bytes(new.encode('utf-8'))


def current_intro(text,relative):
    title_end=text.index('\n')+1
    next_paragraph=text.index('\n\n',title_end+2)
    old=text[title_end:next_paragraph]
    if 'behavior follow-up' not in old:
        raise ValueError('Unexpected current summary')
    summary=('\nThe [test and irreversible-setup review]('+relative+'reports/test-seal-deep-review-20261117/REVIEW.md) '
             'individually assesses the earlier30 and later29 focused methods, strengthens weak assertions and repairs stale execution fixtures. '
             'Fresh source rejects foreign-home Vaults, bare artwork schemes and incorrect new reservation IDs; existing pool-move aliases remain. '
             'The current trusted build is seal-boundaries-20261117. OpenSea minting still uses the NFT metadata root. '
             'Selected-release bindings, content, provider/market/operating qualification and independent approval remain open; no live environment is changed.')
    return text[:title_end]+summary+text[next_paragraph:]


def manual(text):
    text=text.replace('`operator-seal-20261117`','`seal-boundaries-20261117`')
    text=text.replace('--build-profile operator-seal-20261117','--build-profile seal-boundaries-20261117')
    text=text.replace('Current planning defaults to `seal-boundaries-20261117`; historical\n`metadata2-20261116` and legacy',
                      'Current planning defaults to `seal-boundaries-20261117`; historical\n`operator-seal-20261117`, `metadata2-20261116` and legacy')
    text=text.replace('../reports/operator-behavior-followup-20261117/VERIFICATION.md','../reports/test-seal-deep-review-20261117/VERIFICATION.md')
    marker='### Verify artwork before sealing'
    addition='''### Review every irreversible boundary

Use the [complete before-seal guide](SEAL_READINESS.md) and its source inventory.
Primary mint is OpenSea through SeaDrop; OpenSea still reads the collection's
`tokenURI`, so its fixed artwork/renderer remain our responsibility. The new
scheme check rejects bare `ipfs://` / `ar://`, not wrong content or unavailable
files. Review the actual chosen URI length and every evolution path.

The unsigned pre-seal output now includes `seal_boundary_review` for all39
construction instances and selected critical reads. Every actual identity and
seal-readiness field stays unverified; complete offline inputs do not authorize
sealing. In particular, verify pre-seal SeaDrop and LP-converter bindings, the
fixed native venue graph, correct home chain, initial VRF and still-future sale
end. A previously configured mint end can expire during bootstrap and become
unextendable even with zero NFTs. Generic `Access.seal` is not a full release
validator and does not automatically reject every such omitted integration.

'''
    assert marker in text;text=text.replace(marker,addition+marker,1)
    marker='## Custody and LP migration'
    addition='''### Reserve a correct bucket without moving LP

1. Finish the complete module and Migration/validator bindings; read the current
   `Vault.canonicalModule()` and `Migration.validation()` addresses.
2. For a new bucket, read `VaultCanonical.bucketIdentity(poolId)` with the exact
   admitted pool ID. Use its uint256 result unchanged. It preserves canonical
   origin through replacements; do not hash the current Vault address manually.
3. Inspect `Vault.bucketCount()`, `bucketAt(index)` and `poolBucket(poolId)`.
   Governance calls `Vault.reservePool(poolId,bucketId)` with zero ETH. New-ID
   typos reject before capacity/alias writes. Repeating the same mapping is
   idempotent; reassignment remains forbidden. Valid reservations are permanent.
4. For a pool move, preserve the existing registered bucket. An alias consumes
   no new bucket slot. The read-only
   `CustodyValidation.validReservationIdentity(poolId,bucketId)` checks identity
   only; it neither grants authority nor validates pool admission/capacity.
5. Verify `PoolReserved`, the mapping and count. Reservation does not move funds,
   enable deposits or create LP. Do not alias an empty other-pool reservation as
   a fresh activation destination: activation still needs its canonical domain.
   Use the separately reviewed move/resume procedure for actual existing LP.

External swaps do not change these IDs. A different deployment target/lifecycle
still needs refreshed review. No restart is required for the contract call;
matching new runtimes/services are adopted only through their separate procedure.

'''
    assert marker in text;text=text.replace(marker,addition+marker,1)
    return text


def deployment(text):
    text=text.replace('operator-seal-20261117','seal-boundaries-20261117')
    text=text.replace('normal compiler family with the AccessController nonempty-artwork-root seal check.',
                      'normal compiler family with chain/URI guards and the canonical reservation identity check. The previous controller artwork-root guard remains.')
    text=text.replace('The closed registry also retains **`metadata2-20261116`** and',
                      'The closed registry also retains **`operator-seal-20261117`**, **`metadata2-20261116`** and')
    text=text.replace('selecting either family','selecting an older family')
    text=text.replace('the original compiler settings; only AccessController source changed.',
                      'the original compiler settings; Vault, renderer, Budget and existing CustodyValidation source change. The sole Foundry configuration delta is a read permission for pinned public test fixtures.')
    text=text.replace('Its\r\ncreation code plus96argument bytes','AccessController\r\ncreation code plus96argument bytes').replace('Its\ncreation code plus96argument bytes','AccessController\ncreation code plus96argument bytes')
    text=text.replace('../reports/operator-behavior-followup-20261117/REVIEW.md','../reports/test-seal-deep-review-20261117/REVIEW.md')
    return text


def ledger(text):
    data=json.loads(text);data['reviewed']='2026-11-17'
    entries={
      'security-governance':'The [systematic irreversible review](reports/test-seal-deep-review-20261117/SEAL_REVIEW.md) covers all61sources and exact one-time/constructor/lifecycle boundaries. Source now rejects foreign home-chain identities and bare artwork schemes. All39 construction records and critical-read criteria are exposed as unverified before-seal review metadata. Missing SeaDrop/converter bindings, an expired bootstrap mint end, wrong immutable venue graph, bad content and unanswered VRF remain explicit readiness/recovery limits; generic seal is not production approval.',
      'operator-stop-controls':'The approved reservation restriction rejects a fresh pool bucket not equal to VaultCanonical.bucketIdentity(pool), while preserving existing registered aliases. A bounded read-only predicate lives in the existing CustodyValidation child; no new deployment/storage/custody authority. First reservation requires complete Migration/validator binding. Valid reservations still consume permanent bounded capacity; empty aliases are not new activation domains. [Procedure](docs/OPERATOR_MANUAL.md#reserve-a-correct-bucket-without-moving-lp).',
      'metadata-ops':'The [OpenSea artwork-path check](reports/test-seal-deep-review-20261117/OPENSEA_ARTWORK_EXECUTION.json) exercises the pinned SeaDrop runtime, actual NFT/Vault/renderer/lifecycle lens and controlled VRF: revealed metadata uses the collection root while minting stays Dormant. MockAccess and synthetic payment/provider settings do not qualify hosted OpenSea, actual content, target gas or refresh latency. The URI parser now rejects bare schemes; actual root/content/cold read cost still require qualification.',
      'audit-release':'The [focused-test review](reports/test-seal-deep-review-20261117/REVIEW.md) individually assesses both original lists (30 and29) with assertions/fixtures/limits, strengthens weak checks, corrects pinned-block mutation ordering and repairs missing execution interfaces. No blanket claim that every mock is current or all branches were executed. Final strict573=22 current+551 exact-source reuse, separate from test counts and independent approval; intermediate failures/source stages retained.',
      'deployment-initcode':'The fresh trusted build is seal-boundaries-20261117; prior operator-seal/metadata2/manual families remain exact historical pins. All48 normal gates pass without compiler/size/default relaxation. Budget69/Vault32/Oracle3 runtime bytes remain. New identity predicate is one additive read on an existing helper; no new contract. Failed oversize attempts stay explicit; no full new constructor/gas/fee/operating rehearsal is claimed.',
    }
    found=set()
    for area in data['areas']:
        for task in area['tasks']:
            if task['id'] in entries:
                task.setdefault('acceptance',[]).append(entries[task['id']]);found.add(task['id'])
    assert found==set(entries)
    newline='\r\n' if '\r\n' in text else '\n'
    return (json.dumps(data,ensure_ascii=False,indent=2)+'\n').replace('\n',newline)


def main():
    for p in ('README.md','AGENTS.md','PROJECT_CONTEXT.md'):
        edit(p,lambda s:current_intro(s,''))
    for p in ('docs/WORK_HANDOFF.md','docs/IMPLEMENTATION_STATUS.md'):
        edit(p,lambda s:current_intro(s,'../'))
    edit('docs/OPERATOR_MANUAL.md',manual)
    edit('docs/DEPLOYMENT_PREPARATION.md',deployment)
    edit('docs/project-todo.json',ledger)
    for p in ('docs/DEPLOYMENT_SEQUENCE.md','docs/PRESEAL_CONFIGURATION.md'):
        edit(p,lambda s:s.replace('operator-seal-20261117','seal-boundaries-20261117'))
    edit('docs/PRESEAL_CONFIGURATION.md',lambda s:s+'\nThe `seal_boundary_review` appendix covers all39 constructor instances and critical\nchain/metadata/OpenSea/converter/venue/VRF/role/end/reservation reads. It remains\nblocked pending actual observation and content review, even with complete offline\nsettings. Inert bytecode uses length/hash commitments, not duplicated full payloads.\nSee [irreversible setup](SEAL_READINESS.md); no seal calldata is generated.\n')
    for p in ('docs/ROADMAP.md','docs/RELEASE_CHECKLIST.md','reports/README.md'):
        relative='' if p.startswith('reports/') else '../reports/'
        target=relative+'test-seal-deep-review-20261117/REVIEW.md'
        edit(p,lambda s:s[:s.index('\n')+1]+'\nThe [test and irreversible-setup review]('+target+') fixes chain/URI/reservation defects and strengthens specific test oracles. Current build is seal-boundaries-20261117; no release sign-off, deployment, service or website adoption is implied. Real dependencies, complete fees/gas, operations and independent review remain open.\n'+s[s.index('\n')+1:])
    edit('docs/RELEASE_CHECKLIST.md',lambda s:s.replace('The [current controller fix]','The [earlier controller fix]').replace('requires the fresh source-bound `operator-seal-20261117` build.','used the then-current source-bound `operator-seal-20261117` build; that evidence remains historical.'))
    def instructions(text):
        start=text.index('- CI/check-slither-review selects');end=text.index(' The earlier gas-feasibility567',start)
        return text[:start]+'- CI/check-slither-review selects [the final strict review](reports/test-seal-deep-review-20261117/static-final-review.json):573records,\n 22individually current contexts/551unique exact referenced-source reuse. Earlier\n stage2(571) and controller(570) records retain their exact source scopes.\n'+text[end:]
    edit('AGENTS.md',instructions)
    manifest={p.relative_to(ARCHIVE).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()for p in ARCHIVE.rglob('*')if p.is_file()}
    (ARCHIVE/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print('Current guides, task acceptance and repository context updated; original drafts archived.')


if __name__=='__main__':main()
