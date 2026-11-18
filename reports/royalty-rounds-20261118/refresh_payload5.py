"""Bind NEW payload5 to the accepted actual current build; never a candidate.

No compilation, RPC, signing, deployment, old payload edit or release approval.
"""
from pathlib import Path
import hashlib,json,re,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from zzz_ops import deployment_plan as D,royalty_read_policy as READ
sha=lambda b:hashlib.sha256(b).hexdigest()
hashcode=lambda b:'0x'+D.keccak256(b).hex()
PROFILE='royalty-rounds-20261118'
HISTORICAL=('zzz_ops/factory_code_v3.py','config/factory-code-storage-v3.json',
    'zzz_ops/factory_code_v4.py','config/factory-code-storage-v4.json',
    'config/production.schema17.payload3.example.json','config/production.schema17.payload4.example.json')


def main():
    if D.DEFAULT_BUILD_PROFILE!=PROFILE:raise ValueError('Final rounds normal build not adopted; no pins emitted')
    historical={p:sha((ROOT/p).read_bytes()) for p in HISTORICAL}
    assert historical[HISTORICAL[-1]]=='cc1061255416857aab34b6ccfe4c44b0281f6745fc142cda2440ea08a011692b'
    accepted=D.Artifacts();accepted.check_sources()
    assert accepted.profile==PROFILE and len(accepted.input['sources'])==100
    assert accepted.directory.resolve()==(ROOT/'reports/royalty-rounds-20261118/build/final').resolve()
    assert sha(accepted.input['sources']['src/ZZZRoyaltyRewards.sol']['content'].encode())=='35f712bd0b95abdd63a9e696e6e85e63453f2d8e5ec57c089c595e6bfd5f5bbd'
    code=bytes.fromhex(accepted.output['contracts']['src/ZZZRoyaltyRewards.sol']['ZZZRoyaltyRewards']['evm']['bytecode']['object'])
    assert len(code)<=2*24573
    artifact=json.loads((ROOT/'config/factory-code-storage-v4.json').read_bytes())
    artifact.update(profile='royalty_factory_code_storage_payload_v5',
        source_sha256={p:sha(v['content'].encode()) for p,v in accepted.input['sources'].items()},
        creation_code_length=len(code),creation_code_hash=hashcode(code),parts=[])
    for index,data in enumerate((code[:24573],code[24573:])):
        runtime=bytes.fromhex('5f5ffd')+data;assert len(runtime)<=24576
        artifact['parts'].append(dict(index=index,data_length=len(data),runtime_length=len(runtime),runtime_hash=hashcode(runtime)))
    canonical=sha(json.dumps(artifact,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())
    helper=(ROOT/'zzz_ops/factory_code_v4.py').read_text(encoding='utf-8')
    helper=helper.replace('payload4','payload5').replace('payload_v4','payload_v5').replace('storage-v4.json','storage-v5.json')
    helper,count=re.subn(r"ARTIFACT_CANONICAL_SHA256='[0-9a-f]{64}'","ARTIFACT_CANONICAL_SHA256='"+canonical+"'",helper)
    assert count==1
    (ROOT/'config/factory-code-storage-v5.json').write_text(json.dumps(artifact,indent=2)+'\n',encoding='utf-8')
    (ROOT/'zzz_ops/factory_code_v5.py').write_text(helper,encoding='utf-8')
    prior=(ROOT/'config/production.schema17.payload4.example.json').read_bytes();current=json.loads(prior)
    chain=current['chains'][0];assert chain['factory_payload_version']==4
    chain['factory_payload_version']=5
    section=chain['factory_code'];section.update(creation_code_length=len(code),creation_code_hash=hashcode(code))
    for row,wanted in zip(section['parts'],artifact['parts']):row.update(wanted)
    chain['helpers']['royalty_factory']['bindings'].update(royaltyCodeHash=hashcode(code),creationCodeLength=len(code),
        part0CodeHash=artifact['parts'][0]['runtime_hash'],part1CodeHash=artifact['parts'][1]['runtime_hash'])
    chain['helpers']['protocol_policy']['bindings']['royaltyBalanceGas']=None
    chain['helpers']['royalty_rewards']['bindings']['ROYALTY_ALLOCATION_VERSION']=2
    chain['royalty_read_policy']=dict(version=1,policy=None,balance_gas=None,gas_revision=None,
        fingerprint=None,fingerprint_scope=READ.SCOPE,observed=None,review_evidence=None)
    current['_notes']=[text.replace('factory_payload_version4','factory_payload_version5').replace('royalty payload4','royalty payload5')
        for text in current['_notes']]
    current['_notes'].append('Payload5 uses constant-cost exact royalty rounds and a separate reviewed ERC20 balance-call cap. '
        'Omission/3 and explicit4 retain historical bytes; production.schema17.payload4.example.json is byte-identical to the prior fresh template. '
        'royalty_read_policy fingerprint is computed offline from actual policy/cap/gas revision, not a new on-chain getter. '
        'Null cap/observations remain unverified; no gas policy, address, selected currency, service or release is approved.')
    rendered=(json.dumps(current,indent=2)+'\n').encode()
    if b'\r\n' in prior:rendered=rendered.replace(b'\n',b'\r\n')
    (ROOT/'config/production.example.json').write_bytes(rendered)
    accepted.check_sources()
    assert historical=={p:sha((ROOT/p).read_bytes()) for p in HISTORICAL}
    report=dict(schema=1,kind='Actual trusted current source-owned payload5; not release approval',
        producer_sha256=sha(Path(__file__).read_bytes()),build_profile=PROFILE,build_files_sha256=accepted.file_pins,
        build_directory=accepted.directory.relative_to(ROOT).as_posix(),
        royalty_source_sha256=sha(accepted.input['sources']['src/ZZZRoyaltyRewards.sol']['content'].encode()),
        source_count=100,all100_current_source_bytes_match=True,normal_size_gates=48,normal_size_gates_pass=True,
        creation_length=len(code),creation_hash=hashcode(code),canonical_manifest_sha256=canonical,
        parts=artifact['parts'],historical_files_sha256=historical,production_approved=False,
        signing_performed=False,public_deployment_or_operating_adoption=False)
    (ROOT/'reports/royalty-rounds-20261118/FINAL_PAYLOAD5.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('build_profile','creation_length','creation_hash','canonical_manifest_sha256','production_approved')}))


if __name__=='__main__':main()
