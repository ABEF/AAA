"""Admit the new source-bound selected records; no EVM/network execution."""
from pathlib import Path
import gzip,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2];OWN=Path(__file__).resolve().parent
V=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/launch-workload-20261117')
sys.path.insert(0,str(ROOT))
from zzz_ops.abi import keccak256
def sha(raw):return hashlib.sha256(raw).hexdigest()
def main():
    out=OWN/'contributions';out.mkdir(exist_ok=True)
    stage=V/'completed-rpc';raw=(stage/'raw.json').read_bytes();parsed=json.loads(raw)
    result=json.loads((stage/'EXECUTION.json').read_bytes())
    assert result['exit_code']==0 and result['production_unchanged']
    expected={
      'testLaunch16AllBurningFaultsDoNotAffectGrowth()', 'testLaunch16AllBurningFaultsETHActivation()',
      'testLaunch16ColdEmptyETHActivation()', 'testLaunch16ColdHealthyETHActivationAndGrowth()',
      'testLaunch16ColdHealthyZZZActivationAndGrowth()', 'testLaunch16FirstOpeningAllocationETHActivation()',
      'testLaunch16OneBurningFaultETHActivation()', 'testLaunch16RPCStateHealthyPendingAndGrowth()'}
    host='test/LaunchContributionCapacity20261117.t.sol:LaunchContributionCapacity20261117Test'
    assert set(parsed)=={host};tests=parsed[host]['test_results'];assert set(tests)==expected
    rows=[]
    for name,t in tests.items():
        assert t['status']=='Success'
        rows.append({'id':host+'.'+name,'status':t['status'],'reason':t['reason'],
                     'decoded_logs':t['decoded_logs'],'test_kind':t['kind']})
    artifact_path=V/'out/LaunchContributionCapacity20261117.t.sol/LaunchContributionCapacity20261117Test.json'
    artifact_raw=artifact_path.read_bytes();artifact=json.loads(artifact_raw);metadata=artifact['metadata']
    if isinstance(metadata,str):metadata=json.loads(metadata)
    dependencies={}
    for name,pin in metadata['sources'].items():
        body=(ROOT/name).read_bytes();raw_hash='0x'+keccak256(body).hex();lf_hash='0x'+keccak256(body.replace(b'\r\n',b'\n')).hex()
        assert pin['keccak256']in(raw_hash,lf_hash),name
        bracketed=name in result['source_before']
        if bracketed:assert result['source_before'][name]==result['source_after'][name]==sha(body),name
        dependencies[name]={'raw_sha256':sha(body),'compiler_keccak256':pin['keccak256'],
            'lf_normalization_required':pin['keccak256']!=raw_hash,'raw_before_after_bracketed':bracketed}
    identifiers=artifact['methodIdentifiers']
    for name in expected:assert name in identifiers
    source=(ROOT/'test/LaunchContributionCapacity20261117.t.sol').read_bytes()
    (out/'SOURCE_TEST.sol.txt').write_bytes(source)
    (out/'ARTIFACT.json.gz').write_bytes(gzip.compress(artifact_raw,mtime=0))
    (out/'METHODS.json').write_text(json.dumps({'lossy_method_summary':True,'full_raw_external':str(stage/'raw.json'),
       'raw_sha256':sha(raw),'methods':rows},indent=2)+'\n')
    (out/'EXECUTION.json').write_bytes((stage/'EXECUTION.json').read_bytes())
    stages=[]
    for folder in sorted(V.iterdir()):
        path=folder/'EXECUTION.json'
        if not path.is_file():continue
        record=json.loads(path.read_bytes())
        stages.append({'stage':folder.name,'exit_code':record['exit_code'],
           'methods':[{'id':x['id'],'status':x['status'],'reason':x['reason']}for x in record['methods']],
           'raw_sha256':sha((folder/'raw.json').read_bytes()),'raw_bytes':(folder/'raw.json').stat().st_size,
           'stderr_sha256':sha((folder/'stderr.log').read_bytes()),'original_evidence_preserved':True})
    verification={'schema':1,'distinct_current_new_methods':len(rows),'successes':len(rows),
       'raw_event_workflows_overlap_methods':True,'compiler':metadata['compiler'],'settings':metadata['settings'],
       'dependency_sources':dependencies,'method_selectors':{name:identifiers[name]for name in sorted(expected)},
       'artifact_sha256':sha(artifact_raw),'full_raw_sha256':sha(raw),'full_raw_bytes':len(raw),
       'raw_publication':'Lossy compact method/log summary; full verbose205MB raw retained outside Git with exact hash.',
       'stages':stages,'normal_contract_sources_unchanged':61,'old_suites_rerun':False,
       'scope':['Real v4 and full Entry/Vault/royalty4/LP1; synthetic authority/admission/Permit2/prices/VRF/depth',
                'Actual pinned SeaDrop fixture mints; no live OpenSea acceptance',
                '1 incumbent plus1 entrant; not full1000NFT/maximum-state whole-graph qualification',
                'Cold gasleft CALL measurements exclude intrinsic/refunds and have same-test original-value limits',
                'Read-only localRPC results separately settle naturally cold call/estimate/padding facts',
                'Only filesystem read/write permission temporarily added for owned exports; exact originalconfig restored',
                'Test harness code-size limit1M is not production limit adoption',
                'No production/default/financial limit or environment change;32M is diagnostic only']}
    (out/'VERIFICATION.json').write_text(json.dumps(verification,indent=2)+'\n')
    print(json.dumps({'distinct_successes':len(rows),'dependency_pins':len(dependencies),'retained_stages':len(stages)}))
if __name__=='__main__':main()
