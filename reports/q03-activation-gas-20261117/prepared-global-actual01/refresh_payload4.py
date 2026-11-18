"""Bind only the final owned actual normal compilation to NEW payload4.

No RPC, signing, deployment, source port, old payload edit or approval path.
"""
from pathlib import Path
import hashlib,json,re,sys

R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R))
from zzz_ops.abi import keccak256
E=Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/q03-activation-gas-20261117/global-only-build/actual01')
sha=lambda raw:hashlib.sha256(raw).hexdigest()
codehash=lambda raw:'0x'+keccak256(raw).hex()


def main():
    before={p:sha((R/p).read_bytes()) for p in ('zzz_ops/factory_code_v3.py','config/factory-code-storage-v3.json',
        'config/production.schema17.payload3.example.json')}
    input_raw=(E/'compiler-input.json').read_bytes();output_raw=(E/'compiler-output.json').read_bytes()
    source=json.loads(input_raw);output=json.loads(output_raw);gate=json.loads((E/'normal-size-evidence.json').read_bytes())
    assert gate['exit_code']==0 and not gate['errors'] and len(gate['gates'])==48
    assert all(row['runtime_ok'] and row['creation_ok'] for row in gate['gates'])
    assert len(source['sources'])==100
    for name,row in source['sources'].items():
        target=(R/name).resolve();assert target.is_relative_to(R)
        assert target.read_bytes()==row['content'].encode('utf-8'),name
    code=bytes.fromhex(output['contracts']['src/ZZZRoyaltyRewards.sol']['ZZZRoyaltyRewards']['evm']['bytecode']['object'])
    artifact=json.loads((R/'config/factory-code-storage-v3.json').read_bytes())
    artifact.update(profile='royalty_factory_code_storage_payload_v4',
        source_sha256={p:sha(v['content'].encode('utf-8')) for p,v in source['sources'].items()},
        creation_code_length=len(code),creation_code_hash=codehash(code),parts=[])
    for index,data in enumerate((code[:24573],code[24573:])):
        runtime=bytes.fromhex('5f5ffd')+data
        assert len(runtime)<=24576
        artifact['parts'].append(dict(index=index,data_length=len(data),runtime_length=len(runtime),runtime_hash=codehash(runtime)))
    canonical=sha(json.dumps(artifact,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())
    (R/'config/factory-code-storage-v4.json').write_text(json.dumps(artifact,indent=2)+'\n',encoding='utf-8')
    helper=R/'zzz_ops/factory_code_v4.py';text=helper.read_text(encoding='utf-8')
    text,count=re.subn(r"ARTIFACT_CANONICAL_SHA256='[0-9a-f]{64}'","ARTIFACT_CANONICAL_SHA256='"+canonical+"'",text)
    assert count==1;helper.write_text(text,encoding='utf-8')
    path=R/'config/production.example.json';old=path.read_bytes();current=json.loads(old);chain=current['chains'][0]
    assert chain['factory_payload_version']==4
    section=chain['factory_code'];section.update(creation_code_length=len(code),creation_code_hash=codehash(code))
    for row,wanted in zip(section['parts'],artifact['parts']):row.update(wanted)
    factory=chain['helpers']['royalty_factory']['bindings']
    factory.update(royaltyCodeHash=codehash(code),creationCodeLength=len(code),
        part0CodeHash=artifact['parts'][0]['runtime_hash'],part1CodeHash=artifact['parts'][1]['runtime_hash'])
    rendered=json.dumps(current,indent=2)+'\n'
    path.write_bytes(rendered.replace('\n','\r\n').encode() if b'\r\n' in old else rendered.encode())
    assert all(sha((R/p).read_bytes())==h for p,h in before.items())
    report=dict(schema=1,kind='final source-owned payload4 from actual full normal output; not release approval',
        producer_sha256=sha(Path(__file__).read_bytes()),input_sha256=sha(input_raw),output_sha256=sha(output_raw),
        normal_size_evidence_sha256=sha((E/'normal-size-evidence.json').read_bytes()),
        canonical_manifest_sha256=canonical,creation_length=len(code),creation_hash=codehash(code),
        parts=artifact['parts'],all100_current_source_bytes_match_compiler_input=True,all48_size_gates_pass=True,
        actual_filesystem_source_adopted=True,trusted_default_adopted=False,public_deployment_or_adoption=False,
        production_approved=False,adoption_scope='Current source and compiled payload only; default admission and release approval are not established by this producer.',
        historical_files_sha256=before,
        prepared_counter_candidate='prepared-counter-payload4/MANIFEST.json retains the earlier unadopted identity.')
    (R/'reports/q03-activation-gas-20261117/FINAL_PAYLOAD4.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('creation_length','creation_hash','canonical_manifest_sha256',
        'all100_current_source_bytes_match_compiler_input','actual_filesystem_source_adopted','production_approved')},indent=2))


if __name__=='__main__':main()
